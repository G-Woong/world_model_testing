TASK_NAME: C3_world_model_and_model

BACKGROUND:
P3 WorldModelHeads and TextFRCGModel.

From paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-018, MOD-07-021:

WorldModelHeads:
  - Input: concatenated [shared_h (B,128) || z_state (B,32) || action_emb (B,64)] = (B, 224)
  - Optional: hypothesis_emb (B,32) for hypothesis-conditioned prediction
  - effect_head: nn.Linear(224+32, n_effect_types=7) → effect_type_logits
  - progress_head: nn.Sequential(Linear(224+32, 64), ReLU, Linear(64,1)) → progress_delta (scalar)
  - failure_head: nn.Linear(224+32, 1) → sigmoid → failed_action_score
  - action_embedding: nn.Embedding(vocab_size=4096, embed_dim=64)  (action_type text hash)
  - hypothesis_embedding: nn.Embedding(n_hypotheses=64, embed_dim=32)
    n_hypotheses = n_regimes * n_grammars = 8*8 = 64 (Cartesian product)

rollout_step(h_t, z_state, action_type, hypothesis_id, H=1):
  - action_emb = action_embedding(hash(action_type))
  - hypothesis_emb = hypothesis_embedding(hypothesis_id)
  - input = cat([h_t, z_state, action_emb, hypothesis_emb])
  - return RolloutResult(effect_logits, progress_pred, failed_score)

TextFRCGModel:
  - Top-level wrapper integrating all P3 modules.
  - __init__(cfg: dict): reads vocab_size, embed_dim, d_model, nhead, num_layers,
    hidden_dim, z_state_dim, n_regimes, n_grammars, n_change_types, n_reveal_shift,
    n_effect_types from cfg dict (or uses defaults if not provided)
  - forward(public_input: PublicObservation | list[PublicObservation]) -> ModelOutput
  - Accepts both single PublicObservation and list[PublicObservation]
  - Internally calls TextStateEncoder, HistoryEncoder, LatentPosterior
  - Returns ModelOutput dataclass with all head outputs

ModelOutput dataclass:
  - z_state: Tensor (B, 32)
  - z_regime_logits: Tensor (B, 8)
  - z_grammar_logits: Tensor (B, 8)
  - z_change_logits: Tensor (B, 12)
  - z_reveal_shift_logits: Tensor (B, 3)
  - shared_h: Tensor (B, 128)
  - posterior_entropy: Tensor (B,)
  - aux_precondition: Tensor (B,)
  - aux_failure_risk: Tensor (B,)
  Note: effect_logits, progress_pred, failed_score are NOT in ModelOutput because they
  require a specific action and hypothesis — they come from WorldModelHeads.forward_given_action()
  which is called separately in the planning/loss computation phases.

WorldModelHeads design note:
  The model separates the "posterior" computation (TextFRCGModel.forward) from the
  "action-conditioned world model" (WorldModelHeads.forward_given_action). This is intentional:
  - Posterior: depends only on public_observation (encoded)
  - Effect prediction: depends on posterior + specific action + hypothesis

Additionally, TextFRCGModel should expose:
  - model.text_encoder: TextStateEncoder
  - model.history_encoder: HistoryEncoder
  - model.latent_posterior: LatentPosterior
  - model.world_model_heads: WorldModelHeads
  - model.action_embed(action_type: str) -> Tensor (B, 64): hash-based action embedding
  - model.grammar_embed(grammar_id: int) -> Tensor (B, 32): hypothesis embedding

Existing components (already implemented in C2):
  - src/frcgw/models/encoders.py: TextStateEncoder, HistoryEncoder
  - src/frcgw/models/latent_heads.py: LatentPosterior, AuxHeads, LatentSample

GOAL:
Implement src/frcgw/models/world_model_heads.py (WorldModelHeads, RolloutResult) and
src/frcgw/models/text_frcg_model.py (TextFRCGModel, ModelOutput).
Update tests/test_text_frcg_model.py with world model and forward tests.
Do NOT modify encoders.py or latent_heads.py.

FILES_ALLOWED:
  - src/frcgw/models/world_model_heads.py
  - src/frcgw/models/text_frcg_model.py
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
  - src/frcgw/models/encoders.py
  - src/frcgw/models/latent_heads.py

REQUIRED_IMPLEMENTATION:

src/frcgw/models/world_model_heads.py:
```python
"""frcgw.models.world_model_heads -- WorldModelHeads for P3 tiny FRCG text model.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-018, MOD-07-021
Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md §L-MAIN-001, L-MAIN-002
"""
```
Required:
- @dataclass class RolloutResult: effect_logits: Tensor, progress_pred: Tensor, failed_score: Tensor
- class WorldModelHeads(nn.Module):
  - __init__(self, d_model=128, z_state_dim=32, action_embed_dim=64, hypothesis_embed_dim=32,
             n_effect_types=7, n_hypotheses=64, vocab_size=4096)
  - action_embedding: nn.Embedding(vocab_size, action_embed_dim)
  - hypothesis_embedding: nn.Embedding(n_hypotheses, hypothesis_embed_dim)
  - input_dim = d_model + z_state_dim + action_embed_dim + hypothesis_embed_dim = 256
  - effect_head: nn.Linear(256, n_effect_types)
  - progress_head: nn.Sequential(Linear(256, 64), ReLU, Linear(64, 1))
  - failure_head: nn.Linear(256, 1)
  - def forward_given_action(self, shared_h: Tensor, z_state: Tensor, action_type: str | list[str],
                              hypothesis_id: int | list[int]) -> RolloutResult
    - action_emb = action_embedding(hash_tensor(action_type))  # use hashlib MD5 same as encoders
    - hypothesis_emb = hypothesis_embedding(hypothesis_id_tensor)
    - x = cat([shared_h, z_state, action_emb, hypothesis_emb], dim=-1)
    - effect_logits = effect_head(x)  # (B, n_effect_types)
    - progress_pred = progress_head(x).squeeze(-1)  # (B,)
    - failed_score = sigmoid(failure_head(x)).squeeze(-1)  # (B,)
    - return RolloutResult(effect_logits, progress_pred, failed_score)
  - def rollout_step(self, shared_h, z_state, action_type, hypothesis_id, H=1) -> RolloutResult:
    - For H=1 (default in P3): same as forward_given_action

src/frcgw/models/text_frcg_model.py:
```python
"""frcgw.models.text_frcg_model -- TextFRCGModel top-level wrapper for P3.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-003, MOD-07-007, MOD-07-010-021
"""
```
Required:
- @dataclass class ModelOutput:
  - z_state: Tensor
  - z_regime_logits: Tensor
  - z_grammar_logits: Tensor
  - z_change_logits: Tensor
  - z_reveal_shift_logits: Tensor
  - shared_h: Tensor
  - posterior_entropy: Tensor
  - aux_precondition: Tensor
  - aux_failure_risk: Tensor
- class TextFRCGModel(nn.Module):
  - __init__(self, cfg: dict | None = None)
    - If cfg is None, use all defaults
    - Instantiates: text_encoder (TextStateEncoder), history_encoder (HistoryEncoder),
      latent_posterior (LatentPosterior), world_model_heads (WorldModelHeads)
  - def forward(self, public_input: PublicObservation | list[PublicObservation]) -> ModelOutput
    - Handles both single item and batch list
    - Extracts instruction text from public_input.instruction
    - Extracts history_public from public_input.history_public (list[PublicHistoryItem])
    - Does NOT use any hidden/forbidden fields
    - Calls text_encoder(instructions, dom_texts) → text_h
    - Calls history_encoder(histories) → hist_h
    - Calls latent_posterior(text_h, hist_h) → LatentSample
    - Returns ModelOutput from LatentSample fields
  - def action_embed(self, action_type: str) -> Tensor
    - Hash-based embedding from world_model_heads.action_embedding
  - def grammar_embed(self, grammar_id: int) -> Tensor
    - From world_model_heads.hypothesis_embedding
  - def get_default_cfg() -> dict:
    - Returns dict with all defaults (vocab_size=4096, embed_dim=64, d_model=128, etc.)

REQUIRED_TESTS:
Add to tests/test_text_frcg_model.py (do NOT delete existing C2 tests):

Tests use synthetic inputs (no data/ dependency).

10. test_model_output_keys:
    - model = TextFRCGModel()
    - from frcgw.schemas.step_schema import PublicObservation
    - pub = PublicObservation(instruction="click button", history_public=[])
    - out = model(pub)
    - assert isinstance(out, ModelOutput)
    - assert out.z_state.shape[1] == 32
    - assert out.z_regime_logits.shape[1] == 8
    - assert out.z_grammar_logits.shape[1] == 8
    - assert out.z_change_logits.shape[1] == 12
    - assert out.z_reveal_shift_logits.shape[1] == 3
    - assert out.shared_h.shape[1] == 128
    - assert out.posterior_entropy.shape[0] == 1

11. test_world_model_heads_shape:
    - model = TextFRCGModel()
    - pub = PublicObservation(instruction="test", history_public=[])
    - out = model(pub)
    - result = model.world_model_heads.forward_given_action(
          out.shared_h, out.z_state, "click", 0
      )
    - assert result.effect_logits.shape == (1, 7)
    - assert result.progress_pred.shape == (1,)
    - assert result.failed_score.shape == (1,)

12. test_forward_batch:
    - pubs = [PublicObservation(instruction=f"action {i}", history_public=[]) for i in range(4)]
    - out = model(pubs)
    - assert out.z_state.shape == (4, 32)
    - assert out.posterior_entropy.shape == (4,)

13. test_forward_no_hidden_fields:
    - from frcgw.schemas.step_schema import PublicObservation
    - Verify forward() signature does not have true_regime, true_control_grammar etc.
    - import inspect; sig = inspect.signature(TextFRCGModel.forward)
    - assert "true_regime" not in sig.parameters
    - assert "true_control_grammar" not in sig.parameters

14. test_deterministic_model_seed:
    - torch.manual_seed(42)
    - out1 = model(pub)
    - model.eval()
    - with torch.no_grad(): out2 = model(pub)
    - assert torch.allclose(out1.z_state.detach(), out2.z_state.detach())

15. test_action_embed_shape:
    - emb = model.action_embed("click")
    - assert emb.shape[-1] == 64  # action_embed_dim

16. test_grammar_embed_shape:
    - emb = model.grammar_embed(0)
    - assert emb.shape[-1] == 32  # hypothesis_embed_dim

ACCEPTANCE_CRITERIA:
  - pytest tests/test_text_frcg_model.py -q: ALL PASS (9 from C2 + 7 new = 16 total)
  - pytest tests/ -q: ALL PASS (119 existing + 7 new = 126 total, 0 regression)
  - Source MD docstring present in both new files
  - ModelOutput has all 9 required fields
  - forward() does NOT use hidden fields
  - RESULT.md written to .agent_tasks/codex_done/TASK_C3_world_model_and_model_RESULT.md

COMMIT_MESSAGE: feat(p3-c3): WorldModelHeads + TextFRCGModel forward

STOP_CONDITION:
  - STOP if any hidden/forbidden field (true_regime, true_control_grammar, oracle_*, etc.)
    appears in forward() input parameters
  - STOP if ModelOutput is missing required fields
  - STOP if test_model_output_keys fails with shape mismatch
  - STOP if modifying encoders.py or latent_heads.py
