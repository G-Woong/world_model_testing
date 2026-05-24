TASK_NAME: TASK_2046_PUSHCUBE_COLLECTOR_PATCH

BACKGROUND:
FGLC Step 11-D7 (PickCube 450ep 수집) 완료 후, mass OOD axis 구제를 위해 PushCube-v1를 추가 task로 채택하였다 (synthesis RC1 Option 1: E.7+E.2+E.4). PushCube probe에서 gap=0.018, KS p=0.022 (PASS).

현재 collector/schema/script는 PickCube-v1에 hard-coded 되어 있어 PushCube-v1 수집이 불가능하다:
1. `src/fglc/data/collector.py::_apply_ood` Line 70: `inner.cube.set_mass()` hard-coded → PushCube에서 AttributeError 예상
2. `src/fglc/data/maniskill_schema.py::OOD_PARAMS` : PickCube 전용 dict, PushCube OOD params 없음
3. `scripts/fglc/collect_maniskill.py::SPLIT_DEFAULTS`: 모든 output path `data/fglc/PickCube-v1/raw/` hard-coded, --task PushCube-v1 + 경로 자동 라우팅 불가

probe 스크립트 (`_analysis_scratch/pushcube_mass_probe.py`)에서 PushCube inner 속성 탐지 체인이 검증됨:
  1. hasattr(inner, "obj") → inner.obj.set_mass()
  2. hasattr(inner, "cube") → inner.cube.set_mass()
  3. scene.get_all_actors() 이름 검색

D_x는 UNKNOWN (probe에서 obs_mode="state" 사용, 실제 state_dict 모드 D_x 확정 필요).
D_a=8 (Panda EEF, PickCube와 동일 추정).

참조: plans/fglc-step-vectorized-iverson.md §A.3 (코드 한계), §K.6 (TASK Q6 분해안),
      reports/pushcube_audit_R1.md §3 (코드 호환성 분석)

GOAL:
1. collector.py `_apply_ood`: task-aware 분기 추가 (PickCube: cube attr / PushCube: obj attr fallback chain)
2. maniskill_schema.py: task-aware OOD_PARAMS dispatcher (PickCube/PushCube 분리)
3. maniskill_schema.py: PushCube D_x/D_a를 1-episode probe로 자동 감지하는 유틸 함수 추가 (get_task_dims())
4. collect_maniskill.py: SPLIT_DEFAULTS를 task-aware path로 확장 (PickCube/PushCube 분리)
5. collect_maniskill.py: --task PushCube-v1 시 PushCube 경로/params 자동 라우팅
6. 신규 테스트 2개 작성 (PushCube 5ep probe + schema validation)
7. 기존 테스트 22개 green 유지

FILES_ALLOWED:
- src/fglc/data/collector.py
- src/fglc/data/maniskill_schema.py
- scripts/fglc/collect_maniskill.py
- tests/test_fglc_collector_pushcube.py   (신규 — 아직 없음)
- tests/test_fglc_maniskill_schema_pushcube.py  (신규 — 아직 없음)

FILES_FORBIDDEN:
- src/fglc/schemas/visibility.py            (forbidden field SSoT — 수정 불가)
- docs/idea/                                (SSoT 과학 계약 — 수정 불가)
- data/                                     (데이터 write 금지 — probe는 --no-save로)
- outputs/                                  (phase_gates 포함, write 금지)
- configs/                                  (smoke yaml은 별도 작업 Q3에서 완료됨)
- CLAUDE.md                                 (수정 불가)
- .claude/                                  (수정 불가)
- scripts/run_codex_task.ps1               (하네스 — 수정 불가)
- tests/test_fglc_maniskill_collector_probe.py  (기존 PickCube 테스트 — 수정 불가)

REQUIRED_IMPLEMENTATION:

[A] collector.py `_apply_ood` — task-aware 분기

```python
def _apply_ood(env, ood_params: dict[str, Any], task: str = "PickCube-v1") -> None:
    """Apply OOD physical parameters after env.reset()."""
    inner = env.unwrapped
    if "object_mass" in ood_params:
        mass_val = float(ood_params["object_mass"])
        # task-aware inner attribute lookup
        if hasattr(inner, "cube"):
            inner.cube.set_mass(mass_val)
        elif hasattr(inner, "obj"):
            inner.obj.set_mass(mass_val)
        else:
            # fallback: search scene actors by name
            for actor in inner.scene.get_all_actors():
                if any(kw in actor.name.lower() for kw in ("cube", "box", "obj")):
                    actor.set_mass(mass_val)
                    break
    if "joint_friction" in ood_params and ood_params["joint_friction"] > 0.0:
        robot = inner.agent.robot
        art = robot._objs[0]
        for j in art.joints:
            if hasattr(j, "set_friction"):
                j.set_friction(float(ood_params["joint_friction"]))
```

`collect_episodes` 호출 시 `_apply_ood(env, config.ood_params, task=config.task)` 로 task 전달.

[B] maniskill_schema.py — task-aware OOD_PARAMS + get_task_dims()

```python
# task별 OOD_PARAMS (PickCube: 기존 유지, PushCube: 신규)
TASK_OOD_PARAMS: dict[str, dict[str, dict]] = {
    "PickCube-v1": {
        "train_id": {"object_mass": 0.064, "joint_friction": 0.0},
        "val_id": {"object_mass": 0.064, "joint_friction": 0.0},
        "test_id": {"object_mass": 0.064, "joint_friction": 0.0},
        "ood_mass_low": {"object_mass": 1.5, "joint_friction": 0.0},
        "ood_friction_low": {"object_mass": 0.064, "joint_friction": 5.0},
    },
    "PushCube-v1": {
        "train_id": {"object_mass": 0.064, "joint_friction": 0.0},  # mass 확인 필요
        "val_id": {"object_mass": 0.064, "joint_friction": 0.0},
        "test_id": {"object_mass": 0.064, "joint_friction": 0.0},
        "ood_mass_low": {"object_mass": 1.5, "joint_friction": 0.0},   # probe 확인값
        "ood_friction_low": {"object_mass": 0.064, "joint_friction": 5.0},
    },
}

# 하위 호환: 기존 OOD_PARAMS는 PickCube alias로 유지
OOD_PARAMS = TASK_OOD_PARAMS["PickCube-v1"]


def get_task_dims(task: str, n_probe: int = 1) -> tuple[int, int]:
    """1-episode probe로 D_x, D_a 자동 감지. No-save.
    
    Returns: (D_x, D_a)
    """
    import warnings
    warnings.filterwarnings("ignore")
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401
    import numpy as np

    env = gym.make(task, obs_mode="state_dict")
    obs, _ = env.reset(seed=42)
    a = env.action_space.sample()
    
    # flatten obs dict (same logic as collector._flat_obs)
    def _flat(o):
        parts = []
        for k in sorted(o.keys()):
            v = o[k]
            if isinstance(v, dict):
                parts.append(_flat(v))
            else:
                if hasattr(v, "cpu"):
                    v = v.cpu().numpy()
                parts.append(np.array(v, dtype=np.float32).flatten())
        return np.concatenate(parts)
    
    D_x = len(_flat(obs))
    D_a = len(np.array(a, dtype=np.float32).flatten())
    env.close()
    return D_x, D_a
```

[C] collect_maniskill.py — task-aware SPLIT_DEFAULTS

```python
# SPLIT_DEFAULTS를 task-keyed dict로 확장
TASK_SPLIT_DEFAULTS: dict[str, dict] = {
    "PickCube-v1": {
        "train_id": {
            "n_episodes": 250,
            "seed_pool": list(range(42, 292)),
            "regime_id": 0,
            "ood_type": "id",
            "ood_params": {},
            "output": "data/fglc/PickCube-v1/raw/train_id.h5",
        },
        # ... (기존 SPLIT_DEFAULTS 그대로)
    },
    "PushCube-v1": {
        "train_id": {
            "n_episodes": 500,
            "seed_pool": list(range(1042, 1542)),
            "regime_id": 0,
            "ood_type": "id",
            "ood_params": {},
            "output": "data/fglc/PushCube-v1/raw/train_id.h5",
        },
        "val_id": {
            "n_episodes": 100,
            "seed_pool": list(range(1600, 1700)),
            "regime_id": 1,
            "ood_type": "id",
            "ood_params": {},
            "output": "data/fglc/PushCube-v1/raw/val_id.h5",
        },
        "test_id": {
            "n_episodes": 100,
            "seed_pool": list(range(1700, 1800)),
            "regime_id": 2,
            "ood_type": "id",
            "ood_params": {},
            "output": "data/fglc/PushCube-v1/raw/test_id.h5",
        },
        "ood_mass_low": {
            "n_episodes": 100,
            "seed_pool": list(range(1800, 1900)),
            "regime_id": 10,
            "ood_type": "ood_mass",
            "ood_params": {"object_mass": 1.5},
            "output": "data/fglc/PushCube-v1/raw/ood_mass_low.h5",
        },
        "ood_friction_low": {
            "n_episodes": 100,
            "seed_pool": list(range(1900, 2000)),
            "regime_id": 20,
            "ood_type": "ood_friction",
            "ood_params": {"joint_friction": 5.0},
            "output": "data/fglc/PushCube-v1/raw/ood_friction_low.h5",
        },
    },
}

# 하위 호환: 기존 SPLIT_DEFAULTS는 PickCube alias로 유지
SPLIT_DEFAULTS = TASK_SPLIT_DEFAULTS["PickCube-v1"]
```

main()에서 `--task` args 기반으로 TASK_SPLIT_DEFAULTS[args.task] 사용.
--task PushCube-v1 시 자동으로 PushCube 경로/seeds/ood_params 사용.

REQUIRED_TESTS:

[T1] tests/test_fglc_collector_pushcube.py (신규, mani-skill 있을 때만 실행):

```python
@skip_no_maniskill
def test_pushcube_collect_5ep_probe():
    """PushCube-v1 5ep probe (no-save): AttributeError 없음, D_x 유효."""
    from fglc.data.collector import CollectionConfig, collect_episodes
    config = CollectionConfig(
        task="PushCube-v1",
        split="train_id",
        n_episodes=5,
        seed_pool=list(range(1042, 1050)),
        regime_id=0,
        ood_type="id",
        ood_params={},
        max_episode_steps=50,
    )
    episodes, eval_metas, stats = collect_episodes(config, verbose=False)
    assert stats.n_accepted >= 5
    D_x = episodes[0]["state"].shape[1]
    assert D_x > 0, "D_x must be positive"
    assert episodes[0]["action"].shape[1] == 8, "D_a must be 8"

@skip_no_maniskill
def test_pushcube_ood_mass_collect_3ep():
    """PushCube-v1 ood_mass_low 3ep probe: no AttributeError."""
    from fglc.data.collector import CollectionConfig, collect_episodes
    config = CollectionConfig(
        task="PushCube-v1",
        split="ood_mass_low",
        n_episodes=3,
        seed_pool=list(range(1800, 1810)),
        regime_id=10,
        ood_type="ood_mass",
        ood_params={"object_mass": 1.5},
        max_episode_steps=50,
    )
    episodes, _, stats = collect_episodes(config, verbose=False)
    assert stats.n_accepted >= 3
```

[T2] tests/test_fglc_maniskill_schema_pushcube.py (신규, mani-skill 독립):

```python
def test_task_ood_params_has_pushcube():
    from fglc.data.maniskill_schema import TASK_OOD_PARAMS
    assert "PushCube-v1" in TASK_OOD_PARAMS
    assert "ood_mass_low" in TASK_OOD_PARAMS["PushCube-v1"]
    assert TASK_OOD_PARAMS["PushCube-v1"]["ood_mass_low"]["object_mass"] == 1.5

def test_pickcube_ood_params_backward_compat():
    from fglc.data.maniskill_schema import OOD_PARAMS, TASK_OOD_PARAMS
    assert OOD_PARAMS == TASK_OOD_PARAMS["PickCube-v1"]

def test_task_split_defaults_pushcube():
    from scripts.fglc.collect_maniskill import TASK_SPLIT_DEFAULTS, SPLIT_DEFAULTS
    assert "PushCube-v1" in TASK_SPLIT_DEFAULTS
    pc = TASK_SPLIT_DEFAULTS["PushCube-v1"]
    for split in ("train_id", "val_id", "test_id", "ood_mass_low", "ood_friction_low"):
        assert split in pc
        assert "PushCube-v1" in pc[split]["output"]
    # PickCube backward compat
    assert SPLIT_DEFAULTS == TASK_SPLIT_DEFAULTS["PickCube-v1"]

def test_pushcube_pickcube_seed_disjoint():
    from scripts.fglc.collect_maniskill import TASK_SPLIT_DEFAULTS
    pc_seeds = set()
    for v in TASK_SPLIT_DEFAULTS["PickCube-v1"].values():
        pc_seeds.update(v["seed_pool"])
    push_seeds = set()
    for v in TASK_SPLIT_DEFAULTS["PushCube-v1"].values():
        push_seeds.update(v["seed_pool"])
    assert pc_seeds.isdisjoint(push_seeds), "PickCube and PushCube seed pools overlap!"
```

[T3] 기존 22개 테스트 green 유지:
- tests/test_fglc_forbidden_field_sync.py
- tests/test_fglc_state_only_schema.py
- tests/test_fglc_maniskill_collector_probe.py (PickCube hard-coded D_x=42 포함)
- 나머지 19개

ACCEPTANCE_CRITERIA:
1. PushCube-v1 5ep probe (`collect_episodes` with task="PushCube-v1") 성공 — no AttributeError
2. test_fglc_collector_pushcube.py 2개 테스트 PASS (mani-skill 있을 때)
3. test_fglc_maniskill_schema_pushcube.py 4개 테스트 PASS (mani-skill 독립)
4. 기존 22개 test_fglc_*.py 모두 PASS (mani-skill 없는 환경에서도 green)
5. SPLIT_DEFAULTS backward compatibility 유지 (PickCube path 변경 없음)
6. OOD_PARAMS backward compatibility 유지
7. data/ 경로 write 없음 (probe는 --no-save)
8. src/fglc/schemas/visibility.py 미수정

COMMIT_MESSAGE:
feat(collector): task-aware PushCube-v1 support (TASK_2046)

Add PushCube-v1 collection support:
- collector._apply_ood: task-aware inner attr lookup (cube/obj/actor fallback)
- maniskill_schema: TASK_OOD_PARAMS dispatcher + get_task_dims() probe util
- collect_maniskill: TASK_SPLIT_DEFAULTS with PushCube seed/path (1042-1999)
- tests: 2 new files (collector_pushcube + schema_pushcube), 6 new tests
Backward compat: OOD_PARAMS and SPLIT_DEFAULTS aliases preserved.

STOP_CONDITION:
- src/fglc/schemas/visibility.py 수정 시 즉시 중단
- docs/idea/ 수정 시 즉시 중단
- data/ 에 HDF5 write 시 즉시 중단 (--no-save 이외 경로)
- PickCube 기존 테스트 (test_fglc_maniskill_collector_probe.py, D_x=42) 회귀 시 중단
- PushCube 5ep probe에서 AttributeError 해결 불가 시 (ManiSkill API 비표준) → manual_blocker → 사용자 escalation
- 기존 SPLIT_DEFAULTS["train_id"]["output"]에서 "PickCube" 문자열 제거 시 중단 (PickCube 경로 변경 금지)

RELATED_AGENT_REPORT_IDS:
- docs/orchestration/agent_reports/2026-05/impl_risk_Q6_R1.md  (T3 trigger — CONDITIONAL_PASS)
- reports/pushcube_audit_R1.md  (Q1+Q2 사전 감사)
- docs/orchestration/agent_reports/2026-05/mass_ood_root_cause_synthesis_RC1.md  (synthesis RC1)

# T3 GAP 보완 (impl_risk_Q6_R1.md GAP 1, GAP 2 반영)

## GAP 1 보완: --split choices 동적 처리

collect_maniskill.py main() 수정 시:
- `--split` argparse choices를 고정하지 말 것.
- 대신 다음 방식으로 동적 처리:
  Option A (권장): `--task`를 먼저 parse_known_args로 파싱 후 choices 동적 생성
  Option B (단순): choices를 양쪽 union으로 확장
    `choices=list(set(TASK_SPLIT_DEFAULTS["PickCube-v1"].keys()) | set(TASK_SPLIT_DEFAULTS["PushCube-v1"].keys()))`
  두 옵션 모두 허용. PickCube/PushCube 동일한 split 이름("train_id" 등)을 사용하므로 Option B가 단순하고 안전함.

## GAP 2 보완: _apply_ood 호출부 명시

collector.py 변경 시 반드시 다음 위치도 수정할 것:
- 파일: `src/fglc/data/collector.py`
- 현재 코드 (line 126): `_apply_ood(env, config.ood_params)`
- 수정 후: `_apply_ood(env, config.ood_params, task=config.task)`
- 이 변경을 누락하면 PushCube 환경에서 task="PickCube-v1" 기본값이 사용되어 OOD가 올바르게 적용되지 않음.
