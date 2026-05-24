# T3 Implementation Risk Report — TASK_2046_PUSHCUBE_COLLECTOR_PATCH

**날짜**: 2026-05-24  
**TASK**: TASK_2046_PUSHCUBE_COLLECTOR_PATCH  
**검토자**: implementation-risk-critic (T3 agent)  
**종합 판정**: **CONDITIONAL_PASS**  

참조 파일:
- `.agent_tasks/codex_queue/TASK_2046_PUSHCUBE_COLLECTOR_PATCH.md`
- `src/fglc/data/collector.py`
- `src/fglc/data/maniskill_schema.py`
- `scripts/fglc/collect_maniskill.py`
- `tests/test_fglc_maniskill_collector_probe.py`
- `src/fglc/schemas/visibility.py`
- `reports/pushcube_audit_R1.md`
- `_analysis_scratch/pushcube_mass_probe.py`

---

## Gatekeeper 5조건 판정

| 조건 | 판정 | 근거 |
|---|---|---|
| 1. 금지 경로 미수정 | **PASS** | FILES_FORBIDDEN에 `src/fglc/schemas/visibility.py`, `docs/idea/`, `data/`, `outputs/`, `CLAUDE.md`, `.claude/`, `scripts/run_codex_task.ps1` 모두 명시. TASK 범위(data collection 분기 추가)에서 해당 경로를 건드릴 설계적 이유 없음. |
| 2. 테스트 커버리지 | **CONDITIONAL PASS** | 신규 6개 테스트(T1 2개 + T2 4개)가 핵심 경로 커버. GAP 1, GAP 2 존재 (아래 참조). |
| 3. scope creep | **PASS** | 변경 파일 5개 모두 collector/schema/script/테스트로 한정. visibility.py, docs/idea/, configs/ 미포함. |
| 4. backward compatibility | **PASS** | `OOD_PARAMS = TASK_OOD_PARAMS["PickCube-v1"]` alias와 `SPLIT_DEFAULTS = TASK_SPLIT_DEFAULTS["PickCube-v1"]` alias 명시. T2 테스트로 검증. |
| 5. STOP_CONDITION | **PASS** | 6개 STOP_CONDITION이 구체적 행동으로 서술됨. |

---

## 추가 RISK 항목

### GAP 1: `--split choices` 하드코딩 → PushCube 사용 시 argparse 오류 (RISK: MED)

현재 `collect_maniskill.py` line 82:
```python
parser.add_argument("--split", default="train_id", choices=list(SPLIT_DEFAULTS.keys()))
```
`choices`가 PickCube alias 기준이라 `--task PushCube-v1` 시 split 검증이 잘못 적용될 수 있음.

**권장**: `--split` choices를 `TASK_SPLIT_DEFAULTS[args.task].keys()`로 동적 결정하거나 양쪽 union으로 설정. TASK_V2에 반영됨.

### GAP 2: `_apply_ood` 호출부 누락 위험 (RISK: MED)

`collect_episodes` Line 126의 `_apply_ood(env, config.ood_params)` → `_apply_ood(env, config.ood_params, task=config.task)` 변경이 코드 블록 외부 1줄로만 명시됨. Codex가 놓칠 위험.

**권장**: REQUIRED_IMPLEMENTATION [A]에 "호출부: collector.py line 126" 명시. TASK_V2에 반영됨.

### GAP 3: `get_task_dims()` 테스트 미포함 (RISK: LOW)

`get_task_dims()` 직접 호출 테스트 없음. 단, inference path와 격리되어 있어 오염 위험 낮음.

### GAP 4: PickCube/PushCube seed pool disjoint 수치 검증 (RISK: LOW — 확인됨)

PickCube max seed = 649, PushCube min seed = 1042. 겹침 없음. `test_pushcube_pickcube_seed_disjoint` 테스트로 런타임 검증.

### GAP 5: ManiSkill 3.0.1 `scene.get_all_actors()` API (RISK: LOW)

`pushcube_mass_probe.py`에서 `hasattr(inner, "obj")` 체인 성공 확인됨. 3단계 fallback까지 내려갈 가능성 낮음. STOP_CONDITION에서 동적 처리.

---

## 시그니처/설계 검증 요약

| 항목 | 상태 |
|---|---|
| `_apply_ood` fallback chain — probe 검증 | CONFIRMED |
| `get_task_dims()` inference path 격리 | CONFIRMED |
| seed pool disjoint (PickCube ≤649, PushCube ≥1042) | CONFIRMED |
| backward compat aliases | CONFIRMED |
| visibility.py 미수정 | CONFIRMED |

---

## Codex 실행 전 수동 확인 체크리스트

Codex 실행 후 merge 전:
- [ ] `_apply_ood` 호출부(line 126)가 `task=config.task`로 변경되었는가
- [ ] `--split choices`가 PushCube 환경에서 정상 동작하는가
- [ ] `test_fglc_maniskill_collector_probe.py`의 PickCube D_x=42 테스트 PASS인가
- [ ] `SPLIT_DEFAULTS == TASK_SPLIT_DEFAULTS["PickCube-v1"]` alias 테스트 PASS인가

---

## 종합 판정

**CONDITIONAL_PASS** — GAP 1, GAP 2를 TASK 명세에 반영 후 Codex 실행 권장. Gatekeeper 6번째 조건 충족.
