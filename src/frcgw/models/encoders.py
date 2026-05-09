"""frcgw.models.encoders -- TextStateEncoder and HistoryEncoder for P3 tiny text model.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md MOD-07-003, MOD-07-007
"""
from __future__ import annotations

import hashlib

import torch
from torch import Tensor, nn

from frcgw.schemas.step_schema import PublicHistoryItem


def _hash_token(token: str, vocab_size: int) -> int:
    """Hash a token into the fixed vocabulary range using MD5."""
    return int(hashlib.md5(token.encode()).hexdigest(), 16) % vocab_size


def _tokenize_and_hash(text: str, vocab_size: int, max_len: int) -> list[int]:
    """Whitespace-tokenize text, prepend CLS id 0, and truncate."""
    token_ids = [0]
    token_ids.extend(_hash_token(token, vocab_size) for token in text.split())
    return token_ids[:max_len]


class TextStateEncoder(nn.Module):
    """Public instruction/DOM text encoder for P3 tiny FRCG models.

    Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
    """

    def __init__(
        self,
        vocab_size: int = 4096,
        embed_dim: int = 64,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 256,
        dropout: float = 0.1,
        max_seq_len: int = 128,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.input_projection = nn.Linear(embed_dim, d_model)
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

    def forward(self, instruction: str | list[str], dom_text: str | list[str] | None = None) -> Tensor:
        """Encode public instruction text plus optional public DOM text."""
        instructions = [instruction] if isinstance(instruction, str) else list(instruction)
        batch_size = len(instructions)
        if dom_text is None:
            dom_texts = [""] * batch_size
        elif isinstance(dom_text, str):
            dom_texts = [dom_text] * batch_size
        else:
            dom_texts = list(dom_text)

        if len(dom_texts) != batch_size:
            raise ValueError("dom_text batch length must match instruction batch length")

        sequences = [
            _tokenize_and_hash(f"{inst} {dom}".strip(), self.vocab_size, self.max_seq_len)
            for inst, dom in zip(instructions, dom_texts, strict=True)
        ]
        device = self.embedding.weight.device
        input_ids = torch.zeros((batch_size, self.max_seq_len), dtype=torch.long, device=device)
        padding_mask = torch.ones((batch_size, self.max_seq_len), dtype=torch.bool, device=device)
        for row, token_ids in enumerate(sequences):
            seq_len = len(token_ids)
            input_ids[row, :seq_len] = torch.tensor(token_ids, dtype=torch.long, device=device)
            padding_mask[row, :seq_len] = False

        positions = torch.arange(self.max_seq_len, device=device).unsqueeze(0).expand(batch_size, -1)
        x = self.input_projection(self.embedding(input_ids)) + self.position_embedding(positions)
        encoded = self.transformer(x, src_key_padding_mask=padding_mask)
        return encoded[:, 0, :]


class HistoryEncoder(nn.Module):
    """Public action/effect history encoder for P3 tiny FRCG models.

    Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
    """

    def __init__(self, vocab_size: int = 4096, embed_dim: int = 64, hidden_dim: int = 128) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        self.action_embedding = nn.Embedding(vocab_size, embed_dim)
        self.effect_embedding = nn.Embedding(vocab_size, embed_dim)
        self.step_mlp = nn.Sequential(
            nn.Linear(embed_dim + embed_dim + 1, 64),
            nn.ReLU(),
        )
        self.gru = nn.GRU(input_size=64, hidden_size=hidden_dim, num_layers=1, batch_first=True)

    def forward(self, history_list: list[list[PublicHistoryItem]]) -> Tensor:
        """Encode public per-step history summaries."""
        batch_size = len(history_list)
        device = self.action_embedding.weight.device
        out = torch.zeros((batch_size, self.hidden_dim), dtype=self.action_embedding.weight.dtype, device=device)
        lengths = [len(history) for history in history_list]
        max_len = max(lengths, default=0)
        if max_len == 0:
            return out

        action_ids = torch.zeros((batch_size, max_len), dtype=torch.long, device=device)
        effect_ids = torch.zeros((batch_size, max_len), dtype=torch.long, device=device)
        failed_flags = torch.zeros((batch_size, max_len, 1), dtype=out.dtype, device=device)

        for row, history in enumerate(history_list):
            for col, item in enumerate(history):
                action_token = item.action_summary.split()[0] if item.action_summary.split() else ""
                effect_text = item.effect_summary or "none"
                effect_token = effect_text.split()[0] if effect_text.split() else "none"
                action_ids[row, col] = _hash_token(action_token, self.vocab_size)
                effect_ids[row, col] = _hash_token(effect_token, self.vocab_size)
                failed_flags[row, col, 0] = 1.0 if effect_token == "failed" else 0.0

        step_features = self.step_mlp(
            torch.cat(
                [
                    self.action_embedding(action_ids),
                    self.effect_embedding(effect_ids),
                    failed_flags,
                ],
                dim=-1,
            )
        )
        gru_out, _ = self.gru(step_features)
        for row, length in enumerate(lengths):
            if length > 0:
                out[row] = gru_out[row, length - 1]
        return out
