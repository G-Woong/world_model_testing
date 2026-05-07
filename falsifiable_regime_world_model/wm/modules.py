"""WM 공통 building block 모듈 (encoder / decoder / MLP / sequence helpers).

본 모듈은 RSSM core(``rssm.py``)와 prediction head(``heads.py``)에서 공유되는
PyTorch ``nn.Module`` building block만 제공한다. training loop / dataset I/O는
정의하지 않는다.

설계 원칙:
- 모든 forward는 batch-first (B, T, ...) 또는 (B, ...) shape을 받는다.
- shape comment를 모든 forward 위에 명시한다.
- 어떤 모듈도 collector_metadata / privilege metadata를 input으로 받지 않는다.
- 어떤 모듈도 file I/O를 수행하지 않는다.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from .config import EncoderConfig, ObservationConfig


# =============================================================================
# 1. MLP / activation 유틸
# =============================================================================


def make_mlp(
    in_dim: int,
    hidden_dims: Sequence[int],
    out_dim: int,
    *,
    activation: str = "elu",
    output_activation: str = "none",
) -> nn.Sequential:
    """일반적인 fully-connected MLP. 마지막 layer는 보통 linear (output_activation="none").

    activation 선택지: ``relu`` | ``elu`` | ``gelu``. Dreamer-style은 elu 또는 silu가 흔함.
    """
    act = _activation_module(activation)
    layers: List[nn.Module] = []
    prev = in_dim
    for h in hidden_dims:
        layers.append(nn.Linear(prev, h))
        layers.append(act())
        prev = h
    layers.append(nn.Linear(prev, out_dim))
    if output_activation != "none":
        layers.append(_activation_module(output_activation)())
    return nn.Sequential(*layers)


def _activation_module(name: str) -> type:
    name = name.lower()
    if name == "relu":
        return nn.ReLU
    if name == "elu":
        return nn.ELU
    if name == "gelu":
        return nn.GELU
    if name == "silu":
        return nn.SiLU
    raise ValueError(f"unknown activation: {name}")


# =============================================================================
# 2. Observation encoder
# =============================================================================


class ObservationEncoder(nn.Module):
    """관측 (local_grid + scalar + event_token)을 single feature vector로 인코딩.

    입력
    ----
    local_grid : Tensor[B, T, H, W, C]   (float32)
    scalar     : Tensor[B, T, S]         (float32)
    event_token: Tensor[B, T]            (long, 0..event_vocab-1)

    출력
    ----
    features   : Tensor[B, T, feature_dim]

    설계 메모
    --------
    - local_grid는 small (5×5) 이므로 단순 2-layer Conv + flatten으로 충분.
    - scalar는 14-D (room_id one-hot 14는 아님; obs_scalar_dim=14)의 fully-connected.
    - event_token은 embedding lookup (vocab=13).
    - 이 모듈은 raw action을 받지 않는다 (RSSM 내부에서 별도 embedding).
    """

    def __init__(self, obs_cfg: ObservationConfig, enc_cfg: EncoderConfig) -> None:
        super().__init__()
        self.obs_cfg = obs_cfg
        self.enc_cfg = enc_cfg

        # CNN: input C=local_grid_channels, spatial H×W → flatten(channels[-1] * H * W).
        # padding=1로 spatial size 보존 (5x5 매우 작아 stride=1 충분).
        in_channels = obs_cfg.local_grid_channels
        cnn_layers: List[nn.Module] = []
        prev_c = in_channels
        for c in enc_cfg.cnn_channels:
            cnn_layers.append(
                nn.Conv2d(
                    prev_c, c,
                    kernel_size=enc_cfg.cnn_kernel,
                    padding=enc_cfg.cnn_padding,
                )
            )
            cnn_layers.append(nn.ELU())
            prev_c = c
        self.cnn = nn.Sequential(*cnn_layers)
        cnn_out_dim = (
            enc_cfg.cnn_channels[-1] * obs_cfg.local_grid_size * obs_cfg.local_grid_size
        )

        # scalar branch
        self.scalar_mlp = nn.Sequential(
            nn.Linear(obs_cfg.scalar_dim, enc_cfg.scalar_hidden),
            nn.ELU(),
            nn.Linear(enc_cfg.scalar_hidden, enc_cfg.scalar_hidden),
            nn.ELU(),
        )

        # event embedding
        self.event_embed = nn.Embedding(obs_cfg.event_vocab, enc_cfg.event_embed_dim)

        # fuse
        fused_in = cnn_out_dim + enc_cfg.scalar_hidden + enc_cfg.event_embed_dim
        self.fuse = nn.Sequential(
            nn.Linear(fused_in, enc_cfg.feature_dim),
            nn.ELU(),
            nn.Linear(enc_cfg.feature_dim, enc_cfg.feature_dim),
        )

    @property
    def feature_dim(self) -> int:
        return int(self.enc_cfg.feature_dim)

    def forward(
        self,
        local_grid: Tensor,
        scalar: Tensor,
        event_token: Tensor,
    ) -> Tensor:
        """encode observation sequence.

        Shapes
        ------
        local_grid : (B, T, H, W, C)  float32
        scalar     : (B, T, S)        float32
        event_token: (B, T)           long
        out        : (B, T, feature_dim) float32
        """
        B, T = local_grid.shape[:2]
        H, W, C = local_grid.shape[2], local_grid.shape[3], local_grid.shape[4]
        if C != self.obs_cfg.local_grid_channels:
            raise ValueError(
                f"local_grid C={C} != cfg.local_grid_channels={self.obs_cfg.local_grid_channels}"
            )

        # (B, T, H, W, C) → (B*T, C, H, W) for Conv2d
        x = local_grid.reshape(B * T, H, W, C).permute(0, 3, 1, 2).contiguous()
        x = self.cnn(x)                                  # (B*T, c[-1], H, W)
        x = x.reshape(B * T, -1)                          # (B*T, cnn_out_dim)

        s = scalar.reshape(B * T, scalar.shape[-1])      # (B*T, S)
        s = self.scalar_mlp(s)                            # (B*T, scalar_hidden)

        e = self.event_embed(event_token.reshape(B * T))  # (B*T, event_embed_dim)

        fused = torch.cat([x, s, e], dim=-1)             # (B*T, fused_in)
        out = self.fuse(fused)                            # (B*T, feature_dim)
        return out.reshape(B, T, self.enc_cfg.feature_dim)


# =============================================================================
# 3. Action embedding
# =============================================================================


class ActionEmbedding(nn.Module):
    """action (16종 enum)을 dense vector로 임베딩한다.

    Notes
    -----
    - action_raw / action_effective 둘 다 같은 embedding을 공유한다 (vocab=16).
    - RSSM의 GRU 입력은 ``action_raw``의 t-1 시점이다 (env step의 input).
    - action_effective는 학습 target 또는 auxiliary로만 쓴다 (control-drift mismatch).
    """

    def __init__(self, action_vocab: int, embed_dim: int) -> None:
        super().__init__()
        self.embed = nn.Embedding(action_vocab, embed_dim)
        self.embed_dim = int(embed_dim)

    def forward(self, action: Tensor) -> Tensor:
        """encode action.

        Shapes
        ------
        action : (B, T)     long
        out    : (B, T, E)  float32
        """
        return self.embed(action)


# =============================================================================
# 4. Observation decoder (small grid + scalar 재구성)
# =============================================================================


class ObservationDecoder(nn.Module):
    """RSSM features → observation 재구성. (Dreamer-style obs reconstruction loss용)

    main 환경의 local_grid가 5×5로 매우 작으므로 transposed-conv를 굳이 쓰지 않고,
    fully-connected로 직접 (H*W*C) 전체를 재구성한다.
    """

    def __init__(self, feature_dim: int, obs_cfg: ObservationConfig, hidden_dim: int) -> None:
        super().__init__()
        self.obs_cfg = obs_cfg
        self.local_size = obs_cfg.local_grid_size
        self.local_C = obs_cfg.local_grid_channels
        local_total = self.local_size * self.local_size * self.local_C
        self.local_decoder = make_mlp(
            in_dim=feature_dim,
            hidden_dims=(hidden_dim, hidden_dim),
            out_dim=local_total,
            activation="elu",
        )
        self.scalar_decoder = make_mlp(
            in_dim=feature_dim,
            hidden_dims=(hidden_dim,),
            out_dim=obs_cfg.scalar_dim,
            activation="elu",
        )

    def forward(self, features: Tensor) -> Tuple[Tensor, Tensor]:
        """decode.

        Shapes
        ------
        features      : (B, T, F)
        local_pred    : (B, T, H, W, C)
        scalar_pred   : (B, T, S)
        """
        B, T, F = features.shape
        local_flat = self.local_decoder(features.reshape(B * T, F))   # (B*T, H*W*C)
        local_pred = local_flat.reshape(B, T, self.local_size, self.local_size, self.local_C)
        scalar_pred = self.scalar_decoder(features.reshape(B * T, F)).reshape(B, T, -1)
        return local_pred, scalar_pred


# =============================================================================
# 5. small helper: chunk feature concat (h, z) → MLP head 공통 입력
# =============================================================================


def concat_features(h: Tensor, z: Tensor) -> Tensor:
    """(B, T, deter) + (B, T, stoch) → (B, T, deter+stoch)."""
    return torch.cat([h, z], dim=-1)


__all__ = [
    "make_mlp",
    "ObservationEncoder",
    "ActionEmbedding",
    "ObservationDecoder",
    "concat_features",
]
