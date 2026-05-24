TASK_NAME: TASK_2050_ACTION_GAIN_IMPL

BACKGROUND:
FGLC Stage 1: action_gain OOD 파라미터 추가. random policy가 sampling한 action에
gain 곱셈 + clip + float32 cast를 적용하여 control axis OOD를 만든다.
true_action_gain은 이미 forbidden field에 등록되어 있고 eval_metas slot 존재
(collector.py L191, maniskill_schema.py EvalOnlyTransition.__slots__).
np는 collector.py L19에 이미 import되어 있다.
collect_maniskill.py가 yaml이 아닌 self-contained TASK_SPLIT_DEFAULTS dict +
CLI args를 사용한다는 점에 유의.
PickCube 현재 seeds: 42-650 (max=649). PushCube: 1042-1999.
신규 ood_gain_low seeds: PickCube 700-1199, PushCube 2000-2499 (disjoint 확인).
maniskill_schema.py REGIME_ID에 ood_latency=30 이미 존재.

GOAL:
~150 LOC 안에서 다음을 동시 구현한다:
1. collector.py L148-149 사이 action_gain 분기 (3 LOC + np 사용)
2. maniskill_schema.py REGIME_ID에 ood_gain_low:40 + TASK_OOD_PARAMS에
   PickCube/PushCube ood_gain_low:{"action_gain":0.7} (10 LOC)
3. collect_maniskill.py TASK_SPLIT_DEFAULTS에 ood_gain_low entry (PickCube
   seeds 700-1199, PushCube seeds 2000-2499) + CLI --ood-gain arg (40 LOC)
4. build_split.py SPLIT_DEFAULTS에 ood_gain_low entry (10 LOC)
5. configs/fglc/smoke_maniskill_pickcube.yaml에 seed_pool block 보강
   (U-N1 D-8) + ood_gain_value=0.7 + ood_gain_h5 추가 (10 LOC)
6. configs/fglc/smoke_maniskill_pushcube.yaml에 ood_gain_value=0.7 +
   ood_gain_h5 추가 (5 LOC)
7. tests/test_fglc_action_gain_collector.py 신규 (~70 LOC):
   - 3ep collect로 action_gain=0.7 적용 확인
   - eval_metas["true_action_gain"] == 0.7
   - forbidden field 0건
   - action dtype float32 + clip range 유지 (unit test, no ManiSkill required)
   - reproducibility: 같은 seed → 같은 action sequence

FILES_ALLOWED:
- src/fglc/data/collector.py
- src/fglc/data/maniskill_schema.py
- scripts/fglc/collect_maniskill.py
- scripts/fglc/build_split.py
- configs/fglc/smoke_maniskill_pickcube.yaml
- configs/fglc/smoke_maniskill_pushcube.yaml
- tests/test_fglc_action_gain_collector.py (신규)

FILES_FORBIDDEN:
- src/fglc/schemas/visibility.py (mirror 변경 금지)
- docs/idea/ (BACKBONE SSoT)
- .claude/
- src/fglc/repair/
- outputs/phase_gates/
- data/

REQUIRED_IMPLEMENTATION:
- collector.py L148-149 사이 정확 코드:
    a = env.action_space.sample()
    gain = float(config.ood_params.get("action_gain", 1.0))
    if gain != 1.0:
        a = np.clip(a * gain,
                    env.action_space.low,
                    env.action_space.high).astype(np.float32)
    obs_next, r, term, trunc, info = env.step(a)
  np import 존재 확인(L19에 이미 존재), dtype float32 강제
- maniskill_schema.py REGIME_ID 끝에 "ood_gain_low": 40 한 줄 추가
  (현재: "ood_latency": 30 이 마지막 항목)
- maniskill_schema.py TASK_OOD_PARAMS의 PickCube-v1 / PushCube-v1 두 task
  엔트리에 각각 "ood_gain_low": {"action_gain": 0.7} 추가
- collect_maniskill.py TASK_SPLIT_DEFAULTS 두 task에 ood_gain_low split:
  PickCube: {"n_episodes": 500, "seed_pool": list(range(700,1200)),
             "regime_id": 40, "ood_type": "ood_gain",
             "ood_params": {"action_gain": 0.7},
             "output": "data/fglc/PickCube-v1/raw/ood_gain_low.h5"}
  PushCube: {"n_episodes": 500, "seed_pool": list(range(2000,2500)),
             "regime_id": 40, "ood_type": "ood_gain",
             "ood_params": {"action_gain": 0.7},
             "output": "data/fglc/PushCube-v1/raw/ood_gain_low.h5"}
- collect_maniskill.py --split choices 자동 확장 (이미 union 방식 사용)
- collect_maniskill.py CLI에 --ood-gain (type=float, default=None) 추가
  + 기존 ood_mass/ood_friction 분기 직후에:
    if args.ood_gain is not None:
        ood_params["action_gain"] = args.ood_gain
- build_split.py SPLIT_DEFAULTS dict에 ood_gain_low 항목 추가:
  "ood_gain_low": {"regime_id": 40, "ood_type": "ood_gain",
                   "ood_params": {"action_gain": 0.7},
                   "h5_name": "ood_gain_low.h5",
                   "seed_pool": list(range(700, 710))}
- configs/fglc/smoke_maniskill_pickcube.yaml:
  dataset 블록에 추가:
    ood_gain_h5: data/fglc/PickCube-v1/raw/ood_gain_low.h5
    n_episode_ood_gain: 10
    ood_gain_value: 0.7
  seed_pool 블록 추가 (PushCube yaml 참조):
    seed_pool:
      train_id: "42-291"
      val_id: "200-249"
      test_id: "300-349"
      ood_mass_low: "500-549"
      ood_friction_low: "600-649"
      ood_gain_low: "700-1199"
- configs/fglc/smoke_maniskill_pushcube.yaml:
  dataset 블록에 추가:
    ood_gain_h5: data/fglc/PushCube-v1/raw/ood_gain_low.h5
    n_episode_ood_gain: 20
    ood_gain_value: 0.7
  seed_pool.ood_gain_low 추가:
    ood_gain_low: "2000-2499"
- tests/test_fglc_action_gain_collector.py: 검증 5개:
  1. (unit, no mani-skill) np.clip 로직 직접 검증 - dtype float32, clip range
  2. (integration) 3ep collect, action_gain=0.7, eval_metas true_action_gain==0.7
  3. (integration) no forbidden fields in episode inference dicts
  4. (integration) action magnitude reduced vs ID (|a|_mean < ID × 0.85)
  5. (integration) reproducibility: seed=700 로 2회 수집, action sequence identical

REQUIRED_TESTS:
1. pytest -q tests/test_fglc_action_gain_collector.py
2. pytest -q tests/test_fglc_forbidden_field_sync.py
3. pytest -q tests/test_fglc_split_integrity.py
4. python -c "from fglc.data import collector, maniskill_schema; print('ok')"
5. python scripts/fglc/collect_maniskill.py --task PickCube-v1 --split ood_gain_low --ood-gain 0.7 --n-episodes 1 --no-save

ACCEPTANCE_CRITERIA:
- 위 5 테스트 모두 PASS (integration tests skip 허용 시 mani-skill 미설치)
- git diff --cached --stat에 7개 파일만 변경 (다른 파일 변경 0)
- src/fglc/schemas/visibility.py 미변경 확인
- docs/idea/ 미변경 확인
- .agent_tasks/codex_done/TASK_2050_ACTION_GAIN_IMPL_RESULT.md 작성

COMMIT_MESSAGE:
feat(collector): action_gain OOD parameter support + PickCube/PushCube ood_gain_low split

STOP_CONDITION:
- collector.py L148-149 사이 빈 라인 패턴 매치 실패 시 BLOCKED
- env.action_space.low/high shape mismatch detection 시 BLOCKED
- TASK_SPLIT_DEFAULTS dict 구조가 예상과 다르면 BLOCKED
- yaml 구조 오류로 build_split.py가 fail하면 BLOCKED
- 위 stop 발생 시 RESULT.md에 BLOCKED 기록 + Main Claude escalation

RELATED_AGENT_REPORT_IDS:
- impl_risk_TASK_2050_R1.md (T3 implementation-risk-critic, post-Codex)
