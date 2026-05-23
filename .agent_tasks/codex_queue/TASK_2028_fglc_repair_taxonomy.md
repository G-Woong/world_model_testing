TASK_NAME: fglc_repair_taxonomy

BACKGROUND: |
  docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.2 + docs/idea/FGLC_FAILURE_TAXONOMY.md는
  closed-loop repair harness가 사용할 20개 failure cause를 enum-id로 정형화했다.
  이 TASK는 그 명세를 Python 모듈로 구현한다. 다른 repair 모듈(diagnose.py,
  candidates.py, ranker.py 등)이 이 enum을 import해서 사용할 예정이다.

GOAL: |
  Create:
    src/fglc/repair/__init__.py  (package marker)
    src/fglc/repair/taxonomy.py  (FailureCauseId Enum + CAUSE_METADATA + DETECTION_THRESHOLDS + helpers)
    tests/test_fglc_repair_taxonomy.py  (unit tests, >=6 test groups)

  Touch nothing else. No other src/fglc/ files. No docs. No configs.
  No changes to src/fglc/schemas/ (forbidden).

FILES_ALLOWED:
  - src/fglc/repair/__init__.py
  - src/fglc/repair/taxonomy.py
  - tests/test_fglc_repair_taxonomy.py
  - .agent_tasks/codex_done/TASK_2026_05_23_FGLC_REPAIR_TAXONOMY_RESULT.md
  - .agent_tasks/codex_done/TASK_2028_fglc_repair_taxonomy_RESULT.md

FILES_FORBIDDEN:
  - "** (everything else)"
  - "특히: src/fglc/schemas/, .claude/, CLAUDE.md, docs/, scripts/, configs/, outputs/"

REQUIRED_IMPLEMENTATION: |
  1. Read docs/idea/FGLC_FAILURE_TAXONOMY.md (SSoT) — 20개 enum-id, detection threshold, source MD.
  2. Read docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.2 (요약 매핑).
  3. Implement src/fglc/repair/__init__.py:
     - module docstring with source MD ref ("Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §F.2")
     - re-export FailureCauseId, CAUSE_METADATA, DETECTION_THRESHOLDS, applicable_phases_for
  4. Implement src/fglc/repair/taxonomy.py:
     - module docstring citing docs/idea/FGLC_FAILURE_TAXONOMY.md as SSoT
     - class FailureCauseId(str, Enum) with EXACTLY these 20 members (SCREAMING_SNAKE_CASE):
       DATA_TOO_SMALL, DATA_BAD_SPLIT, OOD_TOO_HARD, OOD_TOO_EASY,
       MODEL_UNDERCAPACITY, MODEL_OVERCAPACITY,
       LATENT_GROUP_TOO_SMALL, LATENT_DIM_TOO_SMALL,
       HORIZON_TOO_SHORT, HORIZON_TOO_LONG, LOSS_IMBALANCE,
       SIGMA_CALIBRATION_FAILURE, BETA_GATE_COLLAPSE, ATTENTION_COLLAPSE,
       CORRECTION_TOO_WEAK, CORRECTION_TOO_LARGE,
       PLANNER_BUDGET_TOO_LOW, EVAL_NOISE_HIGH, BASELINE_MISMATCH,
       IMPLEMENTATION_BUG_SUSPECTED
     - @dataclass(frozen=True) class FailureCauseMeta with fields:
         cause_id: FailureCauseId
         meaning: str
         source_md_refs: tuple[str, ...]  (>=1 element each for all causes EXCEPT IMPLEMENTATION_BUG_SUSPECTED which uses empty tuple () per SSoT; all non-empty refs must point to existing path under docs/)
         applicable_phases: tuple[str, ...]  (subset of {"R2","R3","R4","R5","R6","R7","R9","R10"})
         detection_summary: str
     - CAUSE_METADATA: dict[FailureCauseId, FailureCauseMeta] with all 20 entries
       (use docs/idea/FGLC_FAILURE_TAXONOMY.md "Enum-ID 정의표" + "Cause -> Phase 적용 가능성" verbatim)
     - DETECTION_THRESHOLDS: dict[FailureCauseId, dict[str, float|None]]
       (e.g. DATA_TOO_SMALL -> {"nll_std_over_mean_max": 0.3})
       Only numeric values from docs/idea/FGLC_FAILURE_TAXONOMY.md. No callable. No expressions.
       IMPLEMENTATION_BUG_SUSPECTED -> {} (catch-all, no threshold).
     - def applicable_phases_for(phase: str) -> frozenset[FailureCauseId]:
         """Return set of cause-ids that are diagnostically active in the given phase."""
  5. Implement tests/test_fglc_repair_taxonomy.py with >=6 test groups:
     (1) Enum well-formedness: 20 members, all SCREAMING_SNAKE_CASE, all str subclass
     (2) CAUSE_METADATA completeness: every Enum member has metadata
     (3) source_md_refs nonempty + each path exists relative to repo root
         (exception: IMPLEMENTATION_BUG_SUSPECTED may have source_md_refs=() per SSoT)
     (4) applicable_phases subset of canonical phase set
     (5) DETECTION_THRESHOLDS values are int|float|None (no str, no callable)
     (6) applicable_phases_for() returns correct subset for R3, R4, R6 (sanity)

REQUIRED_TESTS: |
  .venv\Scripts\pytest.exe -q tests/test_fglc_repair_taxonomy.py

ACCEPTANCE_CRITERIA: |
  - Exactly 3 source files added (src/fglc/repair/__init__.py, taxonomy.py, tests/...).
  - RESULT.md added (4th file).
  - 0 files modified outside FILES_ALLOWED.
  - pytest -q tests/test_fglc_repair_taxonomy.py -> all green.
  - No import from src/fglc/schemas/ (taxonomy is independent of visibility contract).
  - No external deps beyond stdlib (no numpy, torch, pydantic).
  - Working tree clean after commit (git status --short returns empty).

COMMIT_MESSAGE: feat(repair): add failure cause taxonomy enum (20 cause-ids)

STOP_CONDITION: |
  Stop immediately after the single commit. Do not implement diagnose.py /
  candidates.py / compare.py -- those are separate Steps. Do not "clean up"
  unrelated files. Do not modify docs/idea/FGLC_FAILURE_TAXONOMY.md
  (read-only SSoT).

SANDBOX_MODE: bypass

RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_taxonomy_R1.md
