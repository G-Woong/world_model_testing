TASK_NAME: TASK_1021_A_gui_env_data_integrity_scaffold
BACKGROUND: |
  FRCG-WM P3/P3_EVAL gate PASS (text-only model). P4 GUI env 진입 전에
  데이터 무결성 게이트(schema / leakage audit / deterministic replay)를 먼저
  구축한다. GUI 화면 실제 생성은 이 task 범위 밖이다. 데이터 contract만 구축.

  기존 패턴 참고:
  - src/frcgw/text_env/replay.py       → gui_env/replay_validator.py 기반
  - src/frcgw/data/leakage_auditor.py  → gui_env/leakage_audit.py 기반
  - src/frcgw/schemas/visibility.py    → VisibilityBucket / FORBIDDEN_AGENT_FIELDS 재사용 (수정 금지)

GOAL: |
  1. src/frcgw/gui_env/ 하위 5개 파일 생성
     - __init__.py          : 패키지 init (모듈 공개 API만)
     - task_spec.py         : MVE task 10개 spec 데이터클래스 (dataclass, pydantic v2 불필요)
     - event_schema.py      : action/effect/observation 스키마 (VisibilityBucket 재사용)
     - replay_validator.py  : deterministic replay (seed + event trace → 동일 출력 보장)
     - leakage_audit.py     : GUI 특화 leakage audit (FORBIDDEN_AGENT_FIELDS 재사용,
                               추가 GUI 특화 필드 gold_element_id/oracle_target/true_label
                               등을 AGENT_OBSERVATION 밖으로 강제)
  2. tests/ 하위 3개 테스트 파일 생성
     - test_gui_env_schema.py           : task_spec + event_schema 단위 테스트
     - test_gui_env_leakage.py          : leakage_audit 단위 테스트
     - test_gui_env_replay_determinism.py: replay determinism 테스트

FILES_ALLOWED:
  - src/frcgw/gui_env/__init__.py
  - src/frcgw/gui_env/task_spec.py
  - src/frcgw/gui_env/event_schema.py
  - src/frcgw/gui_env/replay_validator.py
  - src/frcgw/gui_env/leakage_audit.py
  - tests/test_gui_env_schema.py
  - tests/test_gui_env_leakage.py
  - tests/test_gui_env_replay_determinism.py

FILES_FORBIDDEN:
  - .claude/
  - CLAUDE.md
  - .mcp.json
  - paper_context_ref/
  - docs/orchestration/
  - outputs/phase_gates/
  - data/
  - .env
  - .env.local
  - secrets/
  - scripts/run_codex_task.ps1
  - plans/PHASE_PROGRESS.md
  - src/frcgw/schemas/visibility.py
  - src/frcgw/schemas/step_schema.py
  - src/frcgw/schemas/validation.py
  - src/frcgw/schemas/episode_schema.py
  - src/frcgw/text_env/
  - src/frcgw/data/leakage_auditor.py

REQUIRED_IMPLEMENTATION: |
  ### task_spec.py
  - GUITaskSpec dataclass: task_id, task_type (enum: CLICK/FILL/NAVIGATE/DRAG),
    description, target_url (str), expected_grammar (str — hidden from agent),
    difficulty (int 1-5), regime (str — hidden from agent)
  - MVE_TASK_SPECS: list[GUITaskSpec], 최소 10개 (다양한 task_type 커버)
  - IMPORTANT: expected_grammar, regime 필드는 AGENT_OBSERVATION 버킷 아님
    → event_schema.py에서 이 필드를 agent observation에 포함 금지

  ### event_schema.py
  - GUIEventType enum: CLICK, FILL, NAVIGATE, SCROLL, HOVER, DRAG
  - GUIObservation dataclass: observation_id, timestamp, url (str), 
    visible_text (str), clickable_elements (list[str]), 
    screenshot_hash (str — surrogate, not actual screenshot),
    action_taken (str), effect_description (str)
    IMPORTANT: 위 필드만 AGENT_OBSERVATION — hidden label 없음
  - GUIEpisodeRecord dataclass: episode_id, task_id, observations (list[GUIObservation]),
    true_grammar (str — AUDIT_ONLY), true_regime (str — AUDIT_ONLY),
    outcome (str), split_id (str — SPLIT_METADATA)
  - from_dict / to_dict 메서드 포함

  ### replay_validator.py
  - GUIReplayValidator class
  - validate(seed: int, event_trace: list[dict]) -> bool
    동일 seed + event_trace → 동일 outcome (deterministic)
  - 내부적으로 random.seed(seed) 사용
  - GUIReplayResult dataclass: is_valid, outcome_hash, mismatch_step (Optional[int])

  ### leakage_audit.py
  - FORBIDDEN_GUI_AGENT_FIELDS: frozenset = {
      "true_grammar", "true_regime", "gold_element_id", "oracle_target",
      "true_label", "counterfactual_action", "split_id", "template_id",
      "true_change_point", "audit_metadata"
    }
  - audit_gui_observation(obs: dict) -> GUILeakageAuditResult
    — obs 딕셔너리에 FORBIDDEN_GUI_AGENT_FIELDS 포함 여부 검사
    — 위반 시 raise GUILeakageError (caught in test)
  - GUILeakageAuditResult dataclass: passed (bool), violations (list[str])
  - GUILeakageError(Exception)
  - 반드시 src/frcgw/schemas/visibility.py의 FORBIDDEN_AGENT_FIELDS도 union으로 포함

  ### __init__.py
  - 공개 API: GUITaskSpec, MVE_TASK_SPECS, GUIObservation, GUIEpisodeRecord,
    GUIReplayValidator, audit_gui_observation, GUILeakageError

  ### tests/test_gui_env_schema.py
  - test_task_spec_fields_present: 10개 spec 모두 task_id 유일
  - test_hidden_fields_not_in_observation: GUIObservation에 true_grammar/true_regime 없음
  - test_episode_record_has_audit_only_fields: true_grammar/true_regime 존재
  - test_gui_event_types_cover_all: GUIEventType 4개 이상 값

  ### tests/test_gui_env_leakage.py
  - test_clean_observation_passes: FORBIDDEN 필드 없는 dict → audit pass
  - test_forbidden_field_raises: true_grammar 포함 dict → GUILeakageError
  - test_multiple_violations_reported: 2개 이상 forbidden field → violations 2개
  - test_visibility_forbidden_fields_covered: FORBIDDEN_AGENT_FIELDS (visibility.py)가
    FORBIDDEN_GUI_AGENT_FIELDS에 포함되어 있음

  ### tests/test_gui_env_replay_determinism.py
  - test_same_seed_same_result: seed=42, 동일 trace → validate() 결과 동일
  - test_different_seed_may_differ: seed=42 vs seed=99 (결과 다를 수 있음, 구조 검증)
  - test_empty_trace_valid: 빈 trace → is_valid=True (또는 정의된 결과)
  - test_replay_result_fields: GUIReplayResult에 is_valid, outcome_hash 있음

REQUIRED_TESTS: |
  tests/test_gui_env_schema.py
  tests/test_gui_env_leakage.py
  tests/test_gui_env_replay_determinism.py

ACCEPTANCE_CRITERIA: |
  1. pytest tests/test_gui_env_schema.py tests/test_gui_env_leakage.py \
       tests/test_gui_env_replay_determinism.py  → 모두 PASS
  2. GUIObservation에 true_grammar, true_regime, split_id 등 hidden 필드 없음
  3. audit_gui_observation({'true_grammar': 'x'}) → GUILeakageError 발생
  4. GUIReplayValidator().validate(42, trace) 두 번 호출 → 동일 결과
  5. 기존 pytest 전체 실행 시 추가 실패 없음 (기존 1개 FAIL은 pre-existing)

COMMIT_MESSAGE: |
  feat(gui_env): TASK_1021_A GUI env data integrity scaffold

  - task_spec.py: MVE 10 task specs
  - event_schema.py: observation schema (no hidden labels in agent input)
  - replay_validator.py: deterministic replay
  - leakage_audit.py: forbidden field audit (extends visibility.py contract)
  - tests: 3 new test files, all green

STOP_CONDITION: |
  3개 신규 테스트 파일 중 하나라도 pytest FAIL 시 중단.
  FILES_FORBIDDEN 경로 수정 시 즉시 중단.
  FORBIDDEN_GUI_AGENT_FIELDS에 AGENT_OBSERVATION 필드가 포함되면 중단.
  src/frcgw/schemas/visibility.py, step_schema.py, validation.py, episode_schema.py,
  src/frcgw/data/leakage_auditor.py 중 하나라도 수정하면 즉시 중단 (import만 허용).
  FORBIDDEN_AGENT_FIELDS를 새로 정의하거나 별도 frozenset으로 재선언하면 중단.
  PublicObservation을 새로 정의하면 중단 (step_schema.py의 기존 것을 import하여 재사용).
