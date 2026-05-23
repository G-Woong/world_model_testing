TASK_NAME: 11D7A_COLLECTOR_PATCH

BACKGROUND:
  Step 11-D7 실제 데이터 수집 전 선행 패치.
  현재 GAP 5건을 수정한다 — 수집 후 품질 게이트 4중(garbage/integrity/severity/novelty)을
  완전히 통과하기 위해 필요한 최소 변경이다.

  GAP 1: collect_maniskill.py에 --mode {probe,pilot,scaled} 플래그가 없다.
          기존 --no-save만 존재. (collect_maniskill.py:88)
  GAP 2: collector.py가 reject episode를 quarantine 경로에 저장하지 않는다.
          rejection_counts만 누적. (collector.py:188-196)
  GAP 3: validators.py에 EPISODE_DUPLICATE reason이 없다. 9개만 존재. (validators.py:20-29)
  GAP 4: build_split.py에 trajectory hash duplicate audit이 없다.
          quality_report.json에 hash 관련 필드 없음. (build_split.py:169-175)
  GAP 5: diagnose.py CANONICAL_METRIC_KEYS에 eval_ci95_over_effect_size 미포함.
          _fire_eval_noise_high(:117)가 해당 키를 읽으나 CANONICAL_METRIC_KEYS(:10-31)에 없어
          diagnose() 호출 시 발화 누락 위험. (diagnose.py:10-31 vs :117-123)

  기존 구현:
    - EpisodeRejectReason(str, Enum) 9종 — validators.py:20-29
    - CollectionStats.rejection_counts dict — collector.py:36-42
    - build_quality_report() — manifest.py:152-169
    - verify_split_integrity() — manifest.py:178-196
    - CANONICAL_METRIC_KEYS frozenset — diagnose.py:10-31
    - _fire_eval_noise_high() — diagnose.py:117-123

  참조: docs/STEP11_PLAN.md §M (Codex 패치 A)

GOAL:
  (1) collect_maniskill.py에 --mode {probe,pilot,scaled} 명시 플래그 추가.
      기존 --no-save 동작과 호환: --mode probe는 --no-save 와 동일 효과.
      --quarantine-dir 옵션 추가 (기본값 None; 미지정 시 quarantine 저장 비활성화).
      --mode pilot / scaled 는 저장 경로를 변경하지 않는다(기존 output 경로 유지).
      help 텍스트에 각 mode 설명 포함.

  (2) collector.py의 collect_episodes()에 quarantine_dir: str | None = None 파라미터 추가.
      quarantine_dir이 지정된 경우, reject episode의 states/actions/rewards/dones를
      <quarantine_dir>/<split>/<seed>_<reason>.h5 로 gzip4 압축 HDF5로 저장.
      저장 실패(I/O 에러)는 무시하고 WARNING만 출력 (수집 중단 금지).
      기존 rejection_counts dict 누적은 유지.

  (3) validators.py에 EPISODE_DUPLICATE = "episode_duplicate" reason 추가.
      validate_episode() 함수 시그니처에 seen_state_hashes: set[str] | None = None 추가.
      seen_state_hashes가 None이 아닐 때: hashlib.sha1(states.tobytes()).hexdigest()를 계산하고,
      해당 해시가 set에 있으면 EPISODE_DUPLICATE 반환. 없으면 set에 추가 후 계속.
      기존 9개 reason 순서와 우선순위 불변: EPISODE_TOO_SHORT -> EPISODE_SHORT ->
      NUMERICAL_INVALID -> ALL_STATE_STATIC -> ALL_ACTION_ZERO -> NO_TRANSITION ->
      REWARD_FLAT -> NO_DONE_SIGNAL -> DONE_FLOOD -> (마지막에) EPISODE_DUPLICATE.

  (4) build_split.py에 split-내 + split-간 trajectory hash duplicate audit 추가.
      각 split의 episode state array에 대해 hashlib.sha1(ep["state"].tobytes()).hexdigest() 계산.
      split-내 중복: 동일 split 내 hash 충돌 (hash_intra_duplicate_count 집계).
      split-간 중복: 다른 split 간 hash 충돌 (hash_inter_duplicate_count 집계).
      결과를 quality_report.json에 다음 필드로 기록:
        "hash_intra_duplicate_count": int,
        "hash_inter_duplicate_count": int,
        "hash_collision_pairs": list[str]  # ["split_a:ep_i vs split_b:ep_j", ...]
      충돌 pair 수가 100개 초과 시 리스트 대신 "TRUNCATED_AT_100" 문자열로 기록.
      [필수] hash audit 로직은 build_split.py 내 모듈 레벨 함수
      audit_trajectory_hashes(split_episodes: dict[str, list[dict]]) -> dict 로 반드시 분리한다.
      main() 내부 인라인 금지. test_fglc_split_integrity.py가 main() 호출 없이
      audit_trajectory_hashes를 직접 import해서 테스트해야 한다.

  (5) build_split.py의 quality_report 생성 시 다음 4 필드를 항상 포함:
        "friction_api": "joint_dry_friction",
        "friction_ssot_unit": "mu_kinetic",
        "friction_ssot_value_used": 5.0,
        "friction_mapping": "DEFERRED — see docs/idea/18_DATA_BENCHMARKS.md:44"

  (6) diagnose.py CANONICAL_METRIC_KEYS frozenset에 "eval_ci95_over_effect_size" 추가.
      기존 19개 키는 그대로 유지. 순서 무관 (frozenset).

FILES_ALLOWED:
  - scripts/fglc/collect_maniskill.py
  - scripts/fglc/build_split.py
  - src/fglc/data/collector.py
  - src/fglc/data/validators.py
  - src/fglc/data/manifest.py
  - src/fglc/repair/diagnose.py
  - tests/test_fglc_no_garbage_data.py
  - tests/test_fglc_split_integrity.py

FILES_FORBIDDEN:
  - src/fglc/schemas/visibility.py
  - docs/idea/
  - docs/ROADMAP/
  - .claude/
  - CLAUDE.md
  - CLAUDE.local.md
  - .mcp.json
  - data/
  - outputs/
  - secrets/
  - scripts/run_codex_task.ps1
  - src/fglc/schemas/

REQUIRED_IMPLEMENTATION:
  위 GOAL (1)~(6) 전체. 각 항목의 세부 명세를 정확히 구현한다.
  기존 9 reject reason 열거 순서, CollectionStats 필드, build_quality_report() 시그니처,
  verify_split_integrity() 동작은 변경하지 않는다.

REQUIRED_TESTS:
  - tests/test_fglc_no_garbage_data.py에 EPISODE_DUPLICATE 케이스 추가:
      (a) test_episode_duplicate_detected(): seen_hashes set에 동일 state hash 존재 시
          validate_episode()가 EPISODE_DUPLICATE 반환하는지 확인.
      (b) test_episode_duplicate_different_episode_passes(): 다른 states는 PASS (None 반환).
      (c) test_all_ten_reject_reasons_in_enum(): enum이 10개 reason을 포함하는지 확인.
          기존 test_all_nine_reject_reasons_in_enum은 삭제하고 이 테스트로 교체.
  - tests/test_fglc_split_integrity.py에 trajectory hash duplicate 검사 케이스 추가:
      (a) test_no_hash_duplicate_in_clean_splits(): 서로 다른 episode는 중복 없음.
      (b) test_hash_duplicate_detected_intra(): 동일 state array를 같은 split에 중복 삽입 시
          hash_intra_duplicate_count > 0 반환 확인.
      (c) test_hash_duplicate_detected_inter(): 동일 state array가 다른 split에 있을 때
          hash_inter_duplicate_count > 0 반환 확인.
      위 테스트는 build_split.py의 hash audit 함수 또는 별도 helper 함수를 직접 호출한다.
      (build_split.py main()을 직접 호출하지 않아도 됨 — helper 분리 권장)
  - pytest -q tests/ 전체 green (279 기존 + 신규 ≥ 5 추가 = 284 이상 통과).

ACCEPTANCE_CRITERIA:
  - pytest -q tests/ 전체 PASS (기존 279 + 신규 ≥ 5 = ≥ 284 통과)
  - collect_maniskill.py --help 출력에 "--mode" 및 "--quarantine-dir" 등장
  - quality_report.json 스키마에 friction_api / friction_ssot_unit / friction_ssot_value_used /
    friction_mapping / hash_intra_duplicate_count / hash_inter_duplicate_count /
    hash_collision_pairs 등장 (build_quality_report 반환값에 포함 또는
    build_split.py main()이 quality_report에 추가)
  - diagnose.py CANONICAL_METRIC_KEYS에 "eval_ci95_over_effect_size" 포함

COMMIT_MESSAGE:
  feat(d7): collector quarantine + trajectory hash audit + friction unit annotation + eval metric key
            (Step 11-D7-A precursor: GAP 1-5 close)

STOP_CONDITION:
  허용된 FILES_ALLOWED 파일 외 어떤 파일도 수정 금지.
  특히 src/fglc/schemas/visibility.py, docs/ 하위 파일 절대 수정 금지.
  pytest -q tests/ 전체 green 미달성 시 abort하고 BLOCKED RESULT.md 작성.
  기존 test_all_nine_reject_reasons_in_enum이 enum 10개로 fail하면
  해당 테스트를 삭제하고 test_all_ten_reject_reasons_in_enum으로 교체하는 것이 허용됨.
  collect_maniskill.py append 모드(기존 HDF5에 episode 추가) 구현은 이 task 범위 외 — 구현 금지.

SANDBOX_MODE: bypass

RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/2026-05/impl_risk_11d7a_R0.md
