# STEP 9 Handoff Queue

date: 2026-05-18
source: STEP 8 final evidence card scaffold
status: QUEUE_TEMPLATE

## Training-time retrain queue

- ABL-001 (no_regime) faithful retrain -> CLAIM-EVAL-002 prerequisite
- ABL-003 (merged regime-control grammar) faithful retrain -> CLAIM-EVAL-002 prerequisite

## Faithful baseline queue

- BASE-028 (WebWorld) faithful upgrade -> simulator search complexity

## Visibility contract changes (R2 lock review required)

- Add true_regime to EvaluationLabels EVALUATION_ONLY bucket -> enables true regime_shift_f1
- schema_leakage_guard hook drift sync -> update .claude/hooks after visibility.py if changed

## Metric queue

- true regime_shift_f1 (MET-OOD-003 faithful) implementation
- compute-matched BASE-015 vs FRCG-LR comparison

## Architecture queue

- LR active path swap: frcg_agent.py integrate lr_scorer into planning loop (condition: C3 PRELIMINARY+)
- h_exec_id training emission policy decision (deterministic vs model argmax)

## Paper framing queue (STEP 9 novelty)

- Update 01_RELATED_WORK_THREAT_MAP.md: add StressWeb (CITE-019, HIGH), BacktrackAgent (CITE-020), WebUncertainty (CITE-021), gWorld (CITE-022), AgentProg (CITE-023)
- Upgrade PARTIALLY_CONFIRMED -> CONFIRMED_PRIMARY: ViMo, MobileDreamer, Code2World, AgentRx
- Cite StressWeb as primary motivation in 짠RWG-005 (Remap perturbation = 92 consecutive wrong actions)
- Add WebUncertainty as uncertainty-gate baseline competitor in STEP 10 evaluation plan
- Add ATK-NEW-001 through ATK-NEW-006 to reviewer attack ledger

## ICLR readiness gate conditions

- C3 READY_CANDIDATE (F_t variance > 0.01 confirmed on n=5 seeds)
- C4 READY_FOR_REPORT (0.824 level maintained or higher)
- ABL-003 faithful retrain PASS (CLAIM-EVAL-002)
- True regime_shift_f1 implemented (C2 not PROXY)
- Faithful direct-threat baselines: [FILL STEP 9 TARGET COUNT]
- n=5 seed full report with all C1-C5
