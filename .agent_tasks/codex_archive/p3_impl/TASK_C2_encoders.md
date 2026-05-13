TASK_NAME: C2_encoders

BACKGROUND:
P3 tiny FRCG text model encoders and latent posterior heads.

Model architecture from paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md:

TextStateEncoder (MOD-07-003):
  - Hash-based vocabulary: vocab_size=4096, embed_dim=64
  - Input: instruction string + optional dom_snapshot_public text (concatenated)
  - Architecture: nn.Embedding(4096, 64) -> 2-layer Transformer Encoder (d_model=128, nhead=4,
    dim_feedforward=256, dropout=0.1) -> CLS pooling -> output shape (B, 128)
  - Hash tokens: tokenize by whitespace, hash each token to [0, vocab_size-1] with:
    hash_id = int(hashlib.md5(token.encode()).hexdigest(), 16) % vocab_size
  - Prepend a CLS token (id=0), truncate to max_seq_len=128

HistoryEncoder (MOD-07-007):
  - Input: list of PublicHistoryItem (action_summary str, effect_summary str) per step
  - Per-step feature: embed action_type hash + effect_type hash + scalar flags (failed_flag=0/1)
    → simple MLP(input_dim=64+64+1, hidden=64) → step_feature (B, T, 64)
  - Architecture: GRU(input_size=64, hidden_size=128, num_layers=1, batch_first=True)
  - Output: last hidden state of GRU, shape (B, 128)
  - Empty history → return zeros (B, 128)

LatentPosterior (MOD-07-010 to MOD-07-014):
  - Input: combined representation h = TextStateEncoder_out + HistoryEncoder_out → MLP(256, 128) → shared_h (B, 128)
  - 4 separate linear head outputs:
    * z_state_logits: nn.Linear(128, z_state_dim=32) [used as mean of posterior approximation]
    * z_regime_logits: nn.Linear(128, n_regimes=8) [categorical logits]
    * z_grammar_logits: nn.Linear(128, n_grammars=8) [categorical logits]
    * z_change_logits: nn.Linear(128, n_change_types=12) [categorical logits; step index 0-11]
    * z_reveal_shift_logits: nn.Linear(128, n_reveal_shift=3) [logits for none/reveal/shift]
  - Returns LatentSample dataclass

AuxHeads (MOD-07-015 to MOD-07-017):
  - Input: shared_h (B, 128)
  - precondition_head: nn.Linear(128, 1) → sigmoid → precondition score
  - failure_risk_head: nn.Linear(128, 1) → sigmoid → failure risk score

LatentSample (return dataclass):
  - z_state: Tensor (B, 32)
  - z_regime_logits: Tensor (B, 8)
  - z_grammar_logits: Tensor (B, 8)
  - z_change_logits: Tensor (B, 12)
  - z_reveal_shift_logits: Tensor (B, 3)
  - shared_h: Tensor (B, 128)  [used by WorldModelHeads and RewriteHead]
  - posterior_entropy: Tensor (B,)  [sum of categorical entropies for regime+grammar]
  - aux_precondition: Tensor (B,)
  - aux_failure_risk: Tensor (B,)

Actual label vocabulary (confirmed from P2 dataset):
  - Regimes: search_form, required_dropdown, modal_blocker, nested_scroll, permission_gate,
             filter_accordion, pagination_vs_infinite, loading_delayed  (n=8)
  - Grammars: direct_search, required_dropdown_then_search, modal_confirm_then_action,
              container_scroll_then_select, wait_until_enabled_then_click,
              permission_accept_then_action, filter_open_then_select,
              pagination_or_infinite_scroll  (n=8)
  - Change points: integer step index 0-11  (n=12 classes)
  - Reveal/shift: none, reveal, shift  (n=3)
  - Effect types: no_change/none, reveal, shift, failed, delayed, noisy, no_op_valid  (n=7,
                  forward-compatible taxonomy; current P2 data has 4 subset: none/delayed/reveal/shift)

GOAL:
Implement src/frcgw/models/encoders.py (TextStateEncoder, HistoryEncoder) and
src/frcgw/models/latent_heads.py (LatentPosterior, AuxHeads, LatentSample).
Update tests/test_text_frcg_model.py with encoder/latent head unit tests.
All classes must have "Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md" in docstring.
No hidden fields as input to any module.

FILES_ALLOWED:
  - src/frcgw/models/encoders.py
  - src/frcgw/models/latent_heads.py
  - src/frcgw/models/__init__.py
  - tests/test_text_frcg_model.py

FILES_FORBIDDEN:
  - .claude/
  - CLAUDE.md
  - .mcp.json
  - .venv/
  - data/
  - outputs/
  - secrets/
  - scripts/run_codex_task.ps1
  - paper_context_ref/
  - src/frcgw/schemas/
  - src/frcgw/text_env/
  - src/frcgw/data/

REQUIRED_IMPLEMENTATION:

src/frcgw/models/encoders.py:
```python
"""frcgw.models.encoders — TextStateEncoder and HistoryEncoder for P3 tiny text model.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-003, MOD-07-007
"""
```
Required:
- def _hash_token(token: str, vocab_size: int) -> int  (MD5 hash approach)
- def _tokenize_and_hash(text: str, vocab_size: int, max_len: int) -> list[int]  (whitespace split, truncate)
- class TextStateEncoder(nn.Module):
  - __init__(self, vocab_size=4096, embed_dim=64, d_model=128, nhead=4, num_layers=2,
             dim_feedforward=256, dropout=0.1, max_seq_len=128)
  - forward(self, instruction: str | list[str], dom_text: str | list[str] | None = None) -> Tensor (B, d_model)
  - Handles both single string and list[str] batch inputs
- class HistoryEncoder(nn.Module):
  - __init__(self, vocab_size=4096, embed_dim=64, hidden_dim=128)
  - forward(self, history_list: list[list[PublicHistoryItem]]) -> Tensor (B, hidden_dim)
  - Returns zeros tensor for empty history

src/frcgw/models/latent_heads.py:
```python
"""frcgw.models.latent_heads — LatentPosterior and AuxHeads for P3 tiny text model.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-010, MOD-07-011-014, MOD-07-015-017
"""
```
Required:
- @dataclass class LatentSample:
  - z_state: Tensor (B, z_state_dim)
  - z_regime_logits: Tensor (B, n_regimes)
  - z_grammar_logits: Tensor (B, n_grammars)
  - z_change_logits: Tensor (B, n_change_types)
  - z_reveal_shift_logits: Tensor (B, n_reveal_shift)
  - shared_h: Tensor (B, 128)
  - posterior_entropy: Tensor (B,)
  - aux_precondition: Tensor (B,)
  - aux_failure_risk: Tensor (B,)
- class LatentPosterior(nn.Module):
  - __init__(self, input_dim=256, hidden_dim=128, z_state_dim=32, n_regimes=8,
             n_grammars=8, n_change_types=12, n_reveal_shift=3)
  - forward(self, text_h: Tensor, hist_h: Tensor) -> LatentSample
  - Concatenates text_h + hist_h -> shared MLP -> 5 linear heads
  - posterior_entropy = entropy(z_regime softmax) + entropy(z_grammar softmax)
- class AuxHeads(nn.Module):
  - __init__(self, input_dim=128)
  - forward(self, shared_h: Tensor) -> tuple[Tensor, Tensor]  (precondition, failure_risk)

REQUIRED_TESTS:

tests/test_text_frcg_model.py:

Note: import torch and use pytest.importorskip("torch") at the top.
Create tests that work WITHOUT requiring data/frcgw_text/ (use synthetic inputs).

Required test cases:
1. test_text_state_encoder_shape:
   - encoder = TextStateEncoder()
   - out = encoder(["click the button", "search for products"])
   - assert out.shape == (2, 128)

2. test_text_state_encoder_single_string:
   - out = encoder("hello world")
   - assert out.shape == (1, 128) or out.shape == (128,) (handle both)

3. test_history_encoder_empty_history:
   - encoder = HistoryEncoder()
   - out = encoder([[]])  # 1 item, empty history
   - assert out.shape == (1, 128)
   - assert (out == 0).all()

4. test_history_encoder_nonempty:
   - from frcgw.schemas.step_schema import PublicHistoryItem
   - hist = [[PublicHistoryItem(0, "click submit", "no_change")]]
   - out = encoder(hist)
   - assert out.shape == (1, 128)

5. test_latent_posterior_output_keys:
   - lp = LatentPosterior()
   - text_h = torch.randn(2, 128)
   - hist_h = torch.randn(2, 128)
   - sample = lp(text_h, hist_h)
   - assert isinstance(sample, LatentSample)
   - assert sample.z_state.shape == (2, 32)
   - assert sample.z_regime_logits.shape == (2, 8)
   - assert sample.z_grammar_logits.shape == (2, 8)
   - assert sample.z_change_logits.shape == (2, 12)
   - assert sample.z_reveal_shift_logits.shape == (2, 3)
   - assert sample.shared_h.shape == (2, 128)
   - assert sample.posterior_entropy.shape == (2,)

6. test_latent_posterior_entropy_positive:
   - assert (sample.posterior_entropy >= 0).all()

7. test_aux_heads_shapes:
   - aux = AuxHeads()
   - shared_h = torch.randn(3, 128)
   - pre, fail = aux(shared_h)
   - assert pre.shape == (3,) or pre.shape == (3, 1)
   - assert fail.shape == (3,) or fail.shape == (3, 1)
   - assert (pre >= 0).all() and (pre <= 1).all()
   - assert (fail >= 0).all() and (fail <= 1).all()

8. test_deterministic_given_seed:
   - torch.manual_seed(42)
   - out1 = encoder(["test"])
   - torch.manual_seed(42)
   - out2 = encoder(["test"])
   - assert torch.allclose(out1, out2)

9. test_no_hidden_fields_required:
   - Verify encoder forward does NOT accept or require any of:
     true_regime, true_control_grammar, true_wrong_hypothesis, etc.
   - (Static inspection: just verify the forward signature has no such params)

ACCEPTANCE_CRITERIA:
  - pytest tests/test_text_frcg_model.py -q: ALL PASS (no skips for encoder tests since they use synthetic inputs)
  - pytest tests/ -q: ALL PASS (no regression in 110 existing tests)
  - Source MD docstring present in both files
  - LatentSample dataclass has all 9 required fields
  - TextStateEncoder and HistoryEncoder use NO hidden fields as input
  - RESULT.md written to .agent_tasks/codex_done/TASK_C2_encoders_RESULT.md

COMMIT_MESSAGE: feat(p3-c2): TextStateEncoder + HistoryEncoder + LatentPosterior + AuxHeads

STOP_CONDITION:
  - STOP if any hidden/forbidden field (true_regime, true_control_grammar, etc.) is required as input to any forward() method
  - STOP if LatentSample is missing any of the 9 required fields
  - STOP if test_latent_posterior_output_keys fails due to shape mismatch
