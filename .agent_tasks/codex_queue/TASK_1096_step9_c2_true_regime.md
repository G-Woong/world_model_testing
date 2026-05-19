TASK_NAME: TASK_1096_step9_c2_true_regime
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM P3 STEP 9 C2/C1 Label Contract Recovery.
C2 regime_shift_f1 is BLOCKED because EvaluationLabels does not have a true_regime field.
STEP 8 showed C2_regime_split: null (BLOCKED_regime_split_metric_not_implemented).
This task adds true_regime to EvaluationLabels, backfills v0_4 dataset, and implements regime_shift_f1.

Key confirmed facts (verified before delegating to Codex):
1. EvaluationLabels (step_schema.py:74-82) has no true_regime field
2. TrainingLabels (step_schema.py:59-70) already has true_regime: str
3. TextState._hidden_regime exists (state.py:39)
4. collector.py:_build_evaluation_labels (line 229-247) does not emit true_regime
5. validate_visibility_contract only checks step.public_observation — safe to add to EvaluationLabels
6. test_visibility_contract.py tests true_regime in PublicObservation dict raises — this is correct; EvaluationLabels is a separate container
7. FORBIDDEN_AGENT_FIELDS contains "true_regime" — this must NEVER flow into any inference input
8. The backfill can use training_labels.true_regime (already in v0_4 JSONL) as the source

R2 Lock check:
- visibility.py NOT modified — FORBIDDEN_AGENT_FIELDS stays unchanged
- hook tokens NOT changed
- paper_context_ref NOT modified
- tests/test_forbidden_field_mirror_sync.py must stay GREEN

GOAL:
1. Add true_regime: str | None = None to EvaluationLabels dataclass
2. Emit true_regime in collector._build_evaluation_labels()
3. Write backfill script that reads v0_4 JSONL and adds true_regime from training_labels to evaluation_labels
4. Add regime_shift_f1 function to metrics.py
5. Add regime_shift_f1 to METRIC_FUNCTIONS dict in eval_runner.py
6. Write test_step9_regime_shift_f1.py with unit tests

FILES_ALLOWED:
- src/frcgw/schemas/step_schema.py
- src/frcgw/text_env/collector.py
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/eval_runner.py
- tests/test_step9_regime_shift_f1.py
- scripts/backfill_v0_4_true_regime.py

FILES_FORBIDDEN:
- src/frcgw/schemas/visibility.py
- CLAUDE.md
- .claude/
- .mcp.json
- paper_context_ref/
- scripts/run_codex_task.ps1
- outputs/
- data/
- .venv/
- secrets/

REQUIRED_IMPLEMENTATION:

### 1. step_schema.py: Add true_regime to EvaluationLabels

EvaluationLabels dataclass에 다음 필드 추가:
```python
true_regime: str | None = None
```
위치: existing fields 뒤에 추가 (ood_type 뒤). Optional field이므로 default=None.

### 2. collector.py: Emit true_regime in _build_evaluation_labels

_build_evaluation_labels 함수 (line 229-247)에서:
```python
return EvaluationLabels(
    true_wrong_hypothesis=is_wrong,
    h_exec_id=None,
    correct_hypothesis_id=pre_state._hidden_control_grammar,
    evidence_timestamp=pre_state.step_index,
    hypothesis_update_timestamp=None,
    recovery_timestamp=None,
    ood_type=None,
    true_regime=pre_state._hidden_regime,  # ADD THIS LINE
)
```

### 3. scripts/backfill_v0_4_true_regime.py: Backfill script

```python
"""Backfill true_regime from training_labels into evaluation_labels for v0_4 dataset."""
import json
from pathlib import Path

def backfill(dataset_root: str) -> dict:
    root = Path(dataset_root)
    stats = {}
    for split_file in ["train.jsonl", "valid.jsonl", "test_id.jsonl", "test_ood.jsonl"]:
        path = root / split_file
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        updated = 0
        already_set = 0
        output_lines = []
        for line in lines:
            if not line.strip():
                continue
            episode = json.loads(line)
            for step in episode.get("steps", []):
                tr = step.get("training_labels", {}) or {}
                el = step.get("evaluation_labels") or {}
                if el.get("true_regime") is not None:
                    already_set += 1
                else:
                    true_regime = tr.get("true_regime")
                    if true_regime is not None:
                        if step.get("evaluation_labels") is None:
                            step["evaluation_labels"] = {}
                        step["evaluation_labels"]["true_regime"] = true_regime
                        updated += 1
            output_lines.append(json.dumps(episode, ensure_ascii=False))
        path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        stats[split_file] = {"updated": updated, "already_set": already_set}
    return stats

if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "data/frcgw_text/v0_4"
    stats = backfill(root)
    print(json.dumps(stats, indent=2))
```

### 4. metrics.py: Add regime_shift_f1 function

regime_shift_f1 computes F1 for regime-shift detection using true_regime from evaluation_labels.
A "shift" is any episode where true_regime changes across steps.
Agent "detects" a shift if predicted_wrong=True occurs during a regime-shift episode.

```python
def regime_shift_f1(episodes: list[dict]) -> dict[str, float]:
    """Compute regime-shift detection F1 using true_regime from EvaluationLabels.

    Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-OOD-003 faithful
    true_regime is EVALUATION_ONLY — never inference input.
    """
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    skipped = 0

    for episode in episodes:
        steps = _field(episode, "steps", []) or []
        regimes = []
        detected = False
        has_regime_data = False
        for step in steps:
            labels = _field(step, "eval_labels", {}) or {}
            tr = _field(labels, "true_regime")
            if tr is not None:
                has_regime_data = True
                regimes.append(tr)
            if bool(_field(step, "predicted_wrong", False)):
                detected = True

        if not has_regime_data:
            skipped += 1
            continue

        # Regime shift: any change in true_regime across steps
        is_shift = len(set(regimes)) > 1

        if is_shift and detected:
            true_positives += 1
        elif not is_shift and detected:
            false_positives += 1
        elif is_shift and not detected:
            false_negatives += 1

    precision_denom = true_positives + false_positives
    recall_denom = true_positives + false_negatives
    precision = true_positives / precision_denom if precision_denom > 0 else 0.0
    recall = true_positives / recall_denom if recall_denom > 0 else 0.0
    f1_denom = precision + recall
    f1 = 2 * precision * recall / f1_denom if f1_denom > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": float(true_positives),
        "false_positives": float(false_positives),
        "false_negatives": float(false_negatives),
        "skipped_no_regime_data": float(skipped),
    }
```

### 5. eval_runner.py: Add regime_shift_f1 to METRIC_FUNCTIONS

In METRIC_FUNCTIONS dict, add:
```python
"regime_shift_f1": regime_shift_f1,
```
And import `regime_shift_f1` from metrics.

### 6. tests/test_step9_regime_shift_f1.py: New test file

Write tests:
- test_regime_shift_f1_empty_episodes: empty list → 0.0/0.0/0.0
- test_regime_shift_f1_no_true_regime: episodes without true_regime → all skipped
- test_regime_shift_f1_no_shift_no_detection: single regime, no predicted_wrong → fp=0, fn=0
- test_regime_shift_f1_shift_detected: true_regime changes, predicted_wrong=True → tp=1
- test_regime_shift_f1_shift_missed: true_regime changes, no predicted_wrong → fn=1
- test_regime_shift_f1_false_alarm: no shift but predicted_wrong=True → fp=1

REQUIRED_TESTS:
- tests/test_step9_regime_shift_f1.py: all 6 tests must pass
- tests/test_forbidden_field_mirror_sync.py: must remain GREEN (no change to visibility.py)
- tests/test_visibility_contract.py: must remain GREEN
- existing tests/test_eval_runner_timestamps.py: must remain GREEN

ACCEPTANCE_CRITERIA:
1. EvaluationLabels.true_regime field exists and is Optional[str]
2. collector._build_evaluation_labels emits true_regime from pre_state._hidden_regime
3. scripts/backfill_v0_4_true_regime.py runs without error on data/frcgw_text/v0_4/
4. regime_shift_f1 function returns dict with precision/recall/f1 keys
5. regime_shift_f1 is in METRIC_FUNCTIONS in eval_runner.py
6. All 6 test_step9_regime_shift_f1 tests pass
7. tests/test_forbidden_field_mirror_sync.py GREEN
8. tests/test_visibility_contract.py GREEN
9. No modification to visibility.py, paper_context_ref/, .claude/, scripts/run_codex_task.ps1

COMMIT_MESSAGE:
feat(c2): EvaluationLabels.true_regime + regime_shift_f1 metric + v0_4 backfill script (STEP 9 C2)

STOP_CONDITION:
Stop if any of the following:
- Attempting to modify visibility.py, paper_context_ref/, .claude/, scripts/run_codex_task.ps1, outputs/, data/
- Adding true_regime to public_observation or any inference input
- Adding true_regime to FORBIDDEN_AGENT_FIELDS (it's already there and must stay)
- tests/test_forbidden_field_mirror_sync.py fails
- tests/test_visibility_contract.py fails
