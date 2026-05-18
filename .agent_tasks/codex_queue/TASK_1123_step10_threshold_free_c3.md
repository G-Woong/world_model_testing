TASK_NAME: TASK_1123_step10_threshold_free_c3
SANDBOX_MODE: bypass
BACKGROUND:
현재 C3 falsification metric은 threshold-based F1 (wrong_prob > 0.5)이다.
STEP 10 plan은 threshold-free AUROC/AUPRC와 sliding window evidence accumulation quality를 추가하도록 요구한다.
이는 threshold selection artifact를 방지하고 Claim-A (evidence-integrating falsification) 검증에 필수적이다.

GOAL:
1. src/frcgw/evaluation/metrics.py에 threshold_free_c3_auroc() 함수 추가
2. src/frcgw/evaluation/metrics.py에 evidence_accumulation_quality() 함수 추가
3. eval_runner.py의 METRIC_FUNCTIONS에 두 함수 등록
4. tests/test_step10_threshold_free.py 작성 (단위 테스트)

FILES_ALLOWED:
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/eval_runner.py
tests/test_step10_threshold_free.py

FILES_FORBIDDEN:
.claude/
CLAUDE.md
.mcp.json
.venv/
data/
outputs/
secrets/
.env
scripts/run_codex_task.ps1
paper_context_ref/
src/frcgw/schemas/visibility.py
src/frcgw/schemas/step_schema.py
src/frcgw/planning/
src/frcgw/falsification/
src/frcgw/evaluation/frcg_agent.py
src/frcgw/evaluation/ablations.py

REQUIRED_IMPLEMENTATION:
1. metrics.py에 다음 두 함수 추가:

```python
def threshold_free_c3_auroc(episodes: list[dict]) -> dict[str, float]:
    """Threshold-free AUROC/AUPRC for C3 falsification detection.
    
    Uses wrong_prob (continuous) vs true_wrong_hypothesis (binary label).
    Returns {"auroc": float, "auprc": float, "n_positive": int, "n_total": int}.
    
    Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-FALS-003 (threshold-free)
    """
    from sklearn.metrics import roc_auc_score, average_precision_score
    y_true, y_score = [], []
    for ep in episodes:
        for step in ep.get("step_results", []):
            label_dict = step.get("eval_labels", {}) or {}
            twh = label_dict.get("true_wrong_hypothesis")
            wp = step.get("wrong_prob")
            if twh is not None and wp is not None:
                y_true.append(int(bool(twh)))
                y_score.append(float(wp))
    if len(y_true) < 2 or sum(y_true) == 0 or sum(y_true) == len(y_true):
        return {"auroc": 0.0, "auprc": 0.0, "n_positive": sum(y_true) if y_true else 0, "n_total": len(y_true)}
    auroc = float(roc_auc_score(y_true, y_score))
    auprc = float(average_precision_score(y_true, y_score))
    return {"auroc": auroc, "auprc": auprc, "n_positive": int(sum(y_true)), "n_total": len(y_true)}


def evidence_accumulation_quality(episodes: list[dict], window: int = 10) -> dict[str, float]:
    """Sliding window AUROC for evidence accumulation quality.
    
    Computes window-averaged wrong_prob (EWMA) vs per-step prediction.
    Measures whether accumulated evidence is better than instantaneous.
    
    Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-FALS-004 (accumulation)
    """
    from sklearn.metrics import roc_auc_score
    y_true_inst, y_score_inst = [], []
    y_true_accum, y_score_accum = [], []
    for ep in episodes:
        steps = ep.get("step_results", [])
        wp_history = []
        for step in steps:
            label_dict = step.get("eval_labels", {}) or {}
            twh = label_dict.get("true_wrong_hypothesis")
            wp = step.get("wrong_prob")
            if twh is None or wp is None:
                continue
            wp_history.append(float(wp))
            accum_wp = sum(wp_history[-window:]) / len(wp_history[-window:])
            y_true_inst.append(int(bool(twh)))
            y_score_inst.append(float(wp))
            y_true_accum.append(int(bool(twh)))
            y_score_accum.append(accum_wp)
    
    def _safe_auc(yt, ys):
        if len(yt) < 2 or sum(yt) == 0 or sum(yt) == len(yt):
            return 0.0
        return float(roc_auc_score(yt, ys))
    
    return {
        "instantaneous_auroc": _safe_auc(y_true_inst, y_score_inst),
        "window_auroc": _safe_auc(y_true_accum, y_score_accum),
        "window_size": window,
        "n_steps": len(y_true_inst),
    }
```

2. eval_runner.py의 METRIC_FUNCTIONS dict에 두 함수 추가:
   "threshold_free_c3_auroc": threshold_free_c3_auroc,
   "evidence_accumulation_quality": evidence_accumulation_quality,

3. tests/test_step10_threshold_free.py:
   - test_threshold_free_c3_auroc_random(): random wrong_prob → AUROC ≈ 0.5 ± 0.1
   - test_threshold_free_c3_auroc_perfect(): perfect predictor → AUROC = 1.0
   - test_threshold_free_c3_auroc_no_positives(): no positive labels → auroc=0.0, n_positive=0
   - test_evidence_accumulation_quality_returns_schema(): schema check (keys present)
   - test_evidence_accumulation_quality_window(): window=5 vs window=1 (instantaneous)

REQUIRED_TESTS:
tests/test_step10_threshold_free.py → pytest -q → 5 passed
tests/test_step9_regime_shift_f1.py → still GREEN (regression)
tests/test_forbidden_field_mirror_sync.py → GREEN

ACCEPTANCE_CRITERIA:
- threshold_free_c3_auroc() defined in metrics.py
- evidence_accumulation_quality() defined in metrics.py
- Both registered in METRIC_FUNCTIONS
- sklearn.metrics imported correctly
- 5 new tests pass
- no regression in existing tests

COMMIT_MESSAGE:
feat(step10): threshold_free_c3_auroc + evidence_accumulation_quality metrics (Gate O-EVAL)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
visibility.py 수정 시 즉시 abort.
Codex must not modify claim wording, metric definition, baseline list, or ablation list.
Codex must not edit docs/orchestration/lr_alignment/*.md or paper_context_ref/*.md.
If task ambiguity arises, emit BLOCKED status in RESULT.md, do not guess.
