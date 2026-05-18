TASK_NAME: step6_lr_reconciliation_script

BACKGROUND:
STEP 5 produced an LR reconciliation audit at outputs/audits/step5_lr_reconciliation.json.
STEP 6 needs a new audit that compares TWO checkpoints:
- ABL-016 control: outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt (STEP 5, l_falsification=0.0)
- Experimental: outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt (STEP 6, l_falsification=1.0)

The audit compares 4 conditions:
  {ABL-016, FALSIFICATION_ENABLED} × {planner F_t, lr_scorer F_t}

GOAL:
Create scripts/audit_step6_lr_reconciliation.py that extends the STEP 5 script structure to
support dual-checkpoint 4-way comparison. Do NOT modify the STEP 5 audit script.

FILES_ALLOWED:
- scripts/audit_step6_lr_reconciliation.py (new file)
- tests/test_step6_lr_reconciliation.py (new file)

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/visibility.py
- .claude/**
- scripts/run_codex_task.ps1
- scripts/audit_step5_lr_reconciliation.py (read-only reference only)
- scripts/audit_step4_lr_comparison.py (read-only reference only)
- src/frcgw/evaluation/frcg_agent.py (read-only)
- src/frcgw/falsification/lr_scorer.py (read-only)
- outputs/audits/step4_*.json (IMMUTABLE)
- outputs/audits/step5_lr_reconciliation.json (IMMUTABLE)

REQUIRED_IMPLEMENTATION:

### scripts/audit_step6_lr_reconciliation.py

Command-line interface:
```
python scripts/audit_step6_lr_reconciliation.py \
  --abl016-checkpoint outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt \
  --falsification-checkpoint outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt \
  --dataset data/frcgw_text/v0_3/test_id.jsonl \
  --out outputs/audits/step6_lr_reconciliation.json \
  [--max-episodes 10]
```

Output JSON schema (outputs/audits/step6_lr_reconciliation.json):
```json
{
  "timestamp": "<ISO-8601>",
  "abl016_checkpoint": "<path>",
  "falsification_checkpoint": "<path>",
  "dataset": "<path>",
  "n_episodes_evaluated": <int>,
  "n_steps_evaluated": <int>,
  "abl016_planner": {
    "mean_f_t": <float|null>,
    "variance": <float|null>,
    "degenerate_rate": <float|null>
  },
  "abl016_lr_scorer": {
    "mean_f_t": <float|null>,
    "variance": <float|null>,
    "degenerate_rate": <float|null>
  },
  "falsification_planner": {
    "mean_f_t": <float|null>,
    "variance": <float|null>,
    "degenerate_rate": <float|null>
  },
  "falsification_lr_scorer": {
    "mean_f_t": <float|null>,
    "variance": <float|null>,
    "degenerate_rate": <float|null>
  },
  "mean_abs_diff_planner_vs_lr_abl016": <float|null>,
  "mean_abs_diff_planner_vs_lr_falsification": <float|null>,
  "delta_falsification_vs_abl016": {
    "planner": <float|null>,
    "lr_scorer": <float|null>
  },
  "active_path_swap_decision": "PERSIST_DUAL_TRACE" | "READY_FOR_SWAP" | "INCONCLUSIVE",
  "c3_claim_readiness": "PRELIMINARY" | "READY_FOR_REPORT" | "BLOCKED",
  "blocked_reasons": [<str>],
  "step4_audit_path": "outputs/audits/step4_lr_comparison.json",
  "step5_audit_path": "outputs/audits/step5_lr_reconciliation.json"
}
```

Degenerate detection: F_t value is degenerate if abs(f_t) < 1e-6.
degenerate_rate = count(|f_t| < 1e-6) / total_steps.

Swap decision rule:
- READY_FOR_SWAP: mean_abs_diff_planner_vs_lr_falsification < 0.1 AND falsification_planner.degenerate_rate < 0.1 AND falsification_lr_scorer.degenerate_rate < 0.1
- PERSIST_DUAL_TRACE: otherwise (does not mean failure — STEP 6 always reports PERSIST_DUAL_TRACE; swap deferred to STEP 7)
- INCONCLUSIVE: when one or both checkpoints are missing

C3 claim readiness rule:
- BLOCKED: either checkpoint missing, or dataset missing, or lr_scorer import failed, or both planner degenerate_rates == 1.0
- PRELIMINARY: falsification_planner.mean_f_t > 0 on at least some steps (even if noisy)
- READY_FOR_REPORT: NOT reachable in STEP 6 (reserved for STEP 7 with long-horizon training)

CRITICAL safety rules:
- Output path MUST be outputs/audits/step6_lr_reconciliation.json
- If --out does not contain "step6", raise ValueError immediately
- Never overwrite step4_*.json or step5_lr_reconciliation.json
- The script must check that --out != step4_audit_path and --out != step5_audit_path

Leakage prevention:
- The script may load JSONL episodes (public observation only)
- Must NOT read true_regime, true_control_grammar, true_wrong_hypothesis, or any FORBIDDEN_AGENT_FIELDS from the JSONL for the planner F_t computation
- LR scorer F_t computation uses the same step4_audit style (from scripts/audit_step4_lr_comparison.py)

Error handling:
- Missing abl016 checkpoint: write report with status "CKPT_ABL016_NOT_FOUND", c3_claim_readiness="BLOCKED"
- Missing falsification checkpoint: write report with status "CKPT_FALSIFICATION_NOT_FOUND", c3_claim_readiness="BLOCKED"
- Missing dataset: write report with status "DATASET_NOT_FOUND", c3_claim_readiness="BLOCKED"
- No silent fallbacks: if a checkpoint is missing, report it explicitly, do not substitute with random init

REQUIRED_TESTS:

### tests/test_step6_lr_reconciliation.py

1. test_output_schema_keys(): run reconciliation script with both checkpoints missing (mocked), verify output JSON has all required top-level keys from the schema above.
2. test_no_step4_step5_overwrite(): verify the script raises ValueError or explicitly refuses if --out path matches step4 or step5 audit paths.
3. test_dual_checkpoint_both_missing_gives_blocked(): when both checkpoints don't exist, output has c3_claim_readiness="BLOCKED" and blocked_reasons non-empty.
4. test_hidden_label_not_in_planner_input(): verify no FORBIDDEN_AGENT_FIELDS (true_regime, true_control_grammar, etc.) are accessed during planner F_t computation (use mock JSONL episode without those fields, verify no KeyError / AttributeError).
5. test_dual_trace_fields_present(): output contains all four condition keys: abl016_planner, abl016_lr_scorer, falsification_planner, falsification_lr_scorer.
6. test_claim_readiness_assignment(): when planner mean_f_t > 0, c3_claim_readiness is "PRELIMINARY" (not "READY_FOR_REPORT"); when both degenerate_rates == 1.0, c3_claim_readiness is "BLOCKED".

ACCEPTANCE_CRITERIA:
- 6 tests PASS
- Script is runnable: python scripts/audit_step6_lr_reconciliation.py --help exits 0
- Script with missing checkpoints writes BLOCKED report (does not crash)
- Script never writes to outputs/audits/step4_*.json or outputs/audits/step5_lr_reconciliation.json
- No imports or reads from FORBIDDEN paths

COMMIT_MESSAGE:
feat(step6/task3): LR reconciliation audit script for ABL-016 vs falsification-enabled 4-way comparison

STOP_CONDITION:
Stop if: (1) any FORBIDDEN file is modified; (2) script writes to step4/step5 audit paths; (3) planner F_t computation reads FORBIDDEN_AGENT_FIELDS; (4) c3_claim_readiness can reach "READY_FOR_REPORT" for any STEP 6 scenario (reserved for STEP 7).
