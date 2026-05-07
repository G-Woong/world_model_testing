"""Synthetic shape sanity check for ``falsifiable_regime_world_model.wm``.

본 스크립트는 dataset loader / training loop을 만들지 않고, ``WMConfig``를 yaml에서
로드한 뒤 합성(synthetic) tensor만으로 forward / heads / loss shape을 검증한다.

PART0 §3 정합성:
    - 학습 코드 없음.
    - dataset npz를 읽지 않음.
    - planner / evaluator 호출 없음.

사용 예
-------
    python scripts/check_wm_shapes.py --config configs/wm_debug.yaml
    python scripts/check_wm_shapes.py --config configs/wm_medium.yaml --batch 2 --time 8
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

import torch

# -----------------------------------------------------------------------------
# 본 스크립트가 falsifiable_regime_world_model 패키지를 import 할 수 있도록 root path를 추가.
# 절대 hard-coded path를 두지 않는다 — 스크립트가 위치한 폴더의 부모(=레포 루트)를 추가한다.
# -----------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.wm import (  # noqa: E402
    RSSMWorldModel,
    WMConfig,
    compute_total_loss,
)


def build_synthetic_batch(cfg: WMConfig, B: int, T: int, device: torch.device) -> Dict[str, torch.Tensor]:
    """synthetic batch와 supervised target을 모두 같은 dict에 만들어 반환한다.

    실제 dataset loader는 Session 8이 만든다. 본 함수는 *오직 shape 검증* 용 가짜 데이터.
    """
    obs = cfg.observation
    H = obs.local_grid_size
    W = obs.local_grid_size
    C = obs.local_grid_channels
    S = obs.scalar_dim

    batch = {
        # ---- 모델 입력 (forward에 들어감) ----
        "local_grid":  torch.randn(B, T, H, W, C, device=device),
        "scalar":      torch.randn(B, T, S, device=device),
        "event_token": torch.randint(0, obs.event_vocab, (B, T), device=device),
        "action_raw":  torch.randint(0, obs.action_vocab, (B, T), device=device),
        # ---- 학습 target (loss에 들어감) ----
        "obs_local_target":  torch.randn(B, T, H, W, C, device=device),
        "obs_scalar_target": torch.randn(B, T, S, device=device),
        "reward":            torch.randn(B, T, device=device),
        "done":              torch.randint(0, 2, (B, T), device=device).float(),
        "true_state":        torch.randn(B, T, 5, device=device).clamp(-1.0, 1.0),
        "true_regime_control_mode": torch.randint(0, cfg.regime.num_control_modes, (B, T), device=device),
        "change_point":      torch.randint(0, 2, (B, T), device=device).float(),
        "reveal_event":      torch.randint(0, 2, (B, T), device=device).float(),
        "shift_event":       torch.randint(0, 2, (B, T), device=device).float(),
        "raw_eff_mismatch":  torch.randint(0, 2, (B, T), device=device).float(),
    }
    return batch


def expected_forward_keys(cfg: WMConfig) -> Dict[str, str]:
    """ON 상태 head별 예상 output key + 예상 shape의 string 표현."""
    h = cfg.heads
    obs = cfg.observation
    deter = cfg.rssm.deter_dim
    stoch = cfg.rssm.stoch_dim
    expect: Dict[str, str] = {
        "h":          f"(B, T, {deter})",
        "z":          f"(B, T, {stoch})",
        "prior_mean": f"(B, T, {stoch})",
        "prior_std":  f"(B, T, {stoch})",
        "post_mean":  f"(B, T, {stoch})",
        "post_std":   f"(B, T, {stoch})",
    }
    if h.obs_recon_local:
        expect["obs_local_pred"] = f"(B, T, {obs.local_grid_size}, {obs.local_grid_size}, {obs.local_grid_channels})"
    if h.obs_recon_scalar:
        expect["obs_scalar_pred"] = f"(B, T, {obs.scalar_dim})"
    if h.reward:
        expect["reward_pred"] = "(B, T)"
    if h.done:
        expect["done_logit"] = "(B, T)"
    if h.state:
        expect["state_pred"] = "(B, T, 5)"
    if h.regime:
        expect["regime_logits"] = f"(B, T, {cfg.regime.num_control_modes})"
    if h.change_point:
        expect["change_point_logit"] = "(B, T)"
    if h.reveal:
        expect["reveal_logit"] = "(B, T)"
    if h.shift:
        expect["shift_logit"] = "(B, T)"
    if h.raw_eff_mismatch:
        expect["raw_eff_mismatch_logit"] = "(B, T)"
    return expect


def main() -> int:
    parser = argparse.ArgumentParser(description="WM synthetic shape sanity check (no dataset / no training).")
    parser.add_argument("--config", type=str, required=True, help="path to configs/wm_*.yaml")
    parser.add_argument("--batch", type=int, default=2, help="batch size for synthetic tensor")
    parser.add_argument("--time", type=int, default=8, help="chunk_len for synthetic tensor")
    parser.add_argument("--device", type=str, default="cpu", help="cpu | cuda")
    parser.add_argument("--variant", type=str, default=None, help="optional variant name (e.g. no_regime)")
    args = parser.parse_args()

    cfg = WMConfig.from_yaml(args.config)
    if args.variant is not None:
        cfg = cfg.apply_variant(args.variant)
    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")

    print(f"[wm] config={args.config}  variant={args.variant}  device={device}")
    print(f"[wm] meta.scale={cfg.meta.scale}  paper_main={cfg.meta.paper_main}")
    print(f"[wm] feature_dim(h+z) = {cfg.feature_dim}")

    model = RSSMWorldModel(cfg).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[wm] total trainable params: {n_params:,} ({n_params/1e6:.2f}M)")

    batch = build_synthetic_batch(cfg, B=args.batch, T=args.time, device=device)
    out = model(batch)

    # ---- forward output shape 검증 ----
    expect = expected_forward_keys(cfg)
    print("[wm] forward output keys:")
    bad = []
    for key, expected in expect.items():
        if key not in out:
            bad.append(f"  MISSING key: {key} (expected {expected})")
            continue
        shape = tuple(out[key].shape)
        # B, T 위치를 그대로 둔 채 shape 일치 확인
        shape_str = "(" + ", ".join(["B" if i == 0 else "T" if i == 1 else str(s)
                                      for i, s in enumerate(shape)]) + ")"
        ok = shape_str == expected
        flag = "OK " if ok else "BAD"
        print(f"  [{flag}] {key:<28s} shape={shape_str:<32s} expected={expected}")
        if not ok:
            bad.append(f"  shape mismatch: {key}: got {shape_str}, expected {expected}")

    # ---- loss shape 검증 ----
    loss_out = compute_total_loss(out, batch, cfg.loss)
    print(f"[wm] loss.total            = {loss_out.total.item():.4f}  device={loss_out.total.device}")
    for k, v in loss_out.components.items():
        print(f"[wm] loss.components[{k}] = {v.item():.4f}")
    for k, v in loss_out.diagnostics.items():
        print(f"[wm] loss.diagnostics[{k}] = {v.item():.4f}")

    # ---- backward sanity (gradient finite) ----
    loss_out.total.backward()
    n_grads = 0
    grad_finite = True
    for p in model.parameters():
        if p.grad is not None:
            n_grads += 1
            if not torch.isfinite(p.grad).all():
                grad_finite = False
    print(f"[wm] backward: params_with_grad={n_grads}  grad_all_finite={grad_finite}")

    # ---- imagine API stub sanity ----
    init_state = model.initial_state(args.batch, device=device)
    horizon = max(2, args.time // 2)
    action_seq = torch.randint(0, cfg.observation.action_vocab, (args.batch, horizon), device=device)
    img = model.imagine(action_seq, init_state)
    print(f"[wm] imagine (H={horizon}): h={tuple(img['h'].shape)}  z={tuple(img['z'].shape)}")

    if bad:
        print("[wm] FAIL: shape mismatches:")
        for line in bad:
            print(line)
        return 1

    print("[wm] PASS: synthetic shape / loss / backward / imagine all consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
