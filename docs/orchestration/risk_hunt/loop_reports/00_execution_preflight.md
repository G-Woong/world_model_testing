# Execution Preflight Report — STEP 10 Risk-Hunt Loop Run

작성일: 2026-05-19
담당: Main Claude (STEP 10 Phase 2 Loop Execution Orchestrator)
branch: `memory-redesign-2026-05-16` @ `bab31db`

---

## 0. 결론 요약

| Loop | 실행 가능 여부 | 차단 이유 / 수정 필요 |
|---|---|---|
| Loop-01 proxy_off_eval | **READY** | `pretrain_v0_4_long/checkpoint_best.pt` 존재 ✓ |
| Loop-06 fair_compute | **READY** | 동일 checkpoint 사용, RealNoGateAblation 등록됨 ✓ |
| Loop-03 ABL-001/003 retrain | **BLOCKED-LAUNCHER** | (1) launcher가 `--output-dir` 미지정 → 결과가 `outputs/runs/p3_smoke`에 덮어써짐. (2) train_text.py는 `checkpoint_best.pt`를 생성하지 않음 (`checkpoint_ep{N}.pt`만 저장) → eval config의 `outputs/checkpoints/abl001_no_regime/checkpoint_best.pt` 경로와 불일치. (3) `warm_start_checkpoint` 필드는 train_text.py에서 미사용 → cosmetic. |
| Loop-02 multiseed | **BLOCKED-LAUNCHER** | `02_train_text_smoke.py`는 `--seed` / `--checkpoint-dir` argument를 지원하지 않음 (`argparse` 미정의). `run_multiseed_training.py`가 이 argument를 넘기면 즉시 argparse error. |

---

## 1. Git / Branch 상태

```
branch: memory-redesign-2026-05-16
HEAD: bab31db feat(step10): Loop execution Phase 2 complete — loop reports + test fix
status: clean working tree on tracked files (untracked: 2026-05-19 session_report)
```

이전 STEP 10 scaffold commit 모두 반영됨.

---

## 2. 필수 자원 존재 검증

| 자원 | 경로 | 존재 |
|---|---|---|
| 메인 checkpoint | `outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt` | ✓ (18MB, 2026-05-18) |
| 데이터셋 train | `data/frcgw_text/v0_4/train.jsonl` | ✓ |
| 데이터셋 test_id | `data/frcgw_text/v0_4/test_id.jsonl` | ✓ |
| 데이터셋 test_ood | `data/frcgw_text/v0_4/test_ood.jsonl` | ✓ |
| 데이터셋 manifest | `data/frcgw_text/v0_4/manifest.json` | ✓ |
| ABL-001 ckpt | `outputs/checkpoints/abl001_no_regime/checkpoint_best.pt` | **✗ 없음** |
| ABL-003 ckpt | `outputs/checkpoints/abl003_merged_regime_grammar/checkpoint_best.pt` | **✗ 없음** |
| stageA ckpt | `outputs/checkpoints/pretrain_v0_4_long_stageA/checkpoint_best.pt` | **✗ 없음** (config가 가리키지만 코드에서 미사용) |
| Multiseed ckpts | `outputs/checkpoints/pretrain_v0_4_seed*/checkpoint_best.pt` | **✗ 없음** |

---

## 3. Loop별 사전 검증 상세

### Loop-01: `run_proxy_ablation_eval.py`

- config: `configs/lr_eval_step10_proxy_ablation.yaml` 존재 ✓
- 두 agent 모두 `pretrain_v0_4_long/checkpoint_best.pt` 사용
- proxy ON/OFF는 `GateConfig.use_no_state_change_proxy` 한 줄 차이
- **즉시 실행 가능**

### Loop-06: `lr_eval_step10_fair_compute.yaml`

- config 존재 ✓ (FRCG-LR + ABL-036b-real-no-gate + ABL-036-heuristic)
- 세 agent 모두 `pretrain_v0_4_long/checkpoint_best.pt` 사용
- `RealNoGateAblation` class는 `src/frcgw/evaluation/ablations.py`에 등록됨 ✓
- 호출: `python scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_fair_compute.yaml`
- **즉시 실행 가능**

### Loop-03: `run_abl001_retrain.py` / `run_abl003_retrain.py`

**문제 분석**:
1. `02_train_text_smoke.py`는 `--config`, `--model-config`, `--output-dir`만 받음. ABL launcher는 `--config`만 넘기므로 결과가 default `outputs/runs/p3_smoke`로 덮어씌워짐.
2. `train_text.py:save_checkpoint()`는 `checkpoint_ep{epoch}.pt`만 저장. `checkpoint_best.pt`는 별도 promote 단계 필요.
3. STEP 8 ABL-015 pattern을 따르려면: launcher에 `--output-dir outputs/runs/p3_train_v0_4_abl001` + 학습 종료 후 best checkpoint → `outputs/checkpoints/abl001_no_regime/checkpoint_best.pt` 복사 단계 필요.
4. eval config의 `ckpt_path: outputs/checkpoints/abl001_no_regime/checkpoint_best.pt`는 학습 완료 + 복사 후에만 유효.

**필요 최소 수정**:
- launcher script 수정: output_dir 명시 + best ckpt 복사 단계 추가
- 또는 `02_train_text_smoke.py`에 `--checkpoint-dir` 인자 추가 + train_text.py에 best-ckpt 로직 추가 (더 큰 변경)

**현 상황 권고**: STEP A에서는 BLOCKED로 기록. Loop-01/06 실행 후 결과에 따라 launcher patch 여부 결정.

### Loop-02: `run_multiseed_training.py`

**문제 분석**:
- launcher가 `--seed` 및 `--checkpoint-dir` 인자를 02_train_text_smoke.py에 넘김
- 02_train_text_smoke.py argparse는 이 두 인자 미정의 → `argparse error: unrecognized arguments` 즉시 실패
- 5번 학습 × 10분 = 50분 BLOCKER

**필요 최소 수정**:
- `02_train_text_smoke.py`에 `--seed`, `--checkpoint-dir` argument 추가
- `train_text.py`/`run_smoke_train`이 seed override 처리하도록 수정
- 또는 launcher가 환경변수 또는 임시 yaml 파일로 seed/checkpoint_dir 주입

**현 상황 권고**: Codex task로 위임 적합 (2개 이상 파일 수정 + 테스트 동반). Loop-01/06 결과 확인 후 실행 여부 결정.

---

## 4. 실행 우선순위

1. **Loop-01** (proxy_off_eval) — 즉시 실행, ~10-20분
2. **Loop-06** (fair_compute) — 즉시 실행, ~10-20분
3. **Loop-03/02** — launcher 수정 필요. Loop-01/06 결과가 PIVOT/SHRINK를 가리키면 retrain 우선순위 격하 가능.

---

## 5. 위험 / 부작용

- **Loop-03/02 BLOCKED**: 즉시 retrain 불가하므로 separability claim (Loop-03)과 statistical validity (Loop-02)에 대한 verdict가 **BLOCKED_WITH_EVIDENCE** 또는 deferred 처리됨.
- **데이터셋 미감사 확인 불필요**: 기존 `tests/test_forbidden_field_mirror_sync.py`가 GREEN 유지되는 한 leakage 안전.
- **eval 실행 시간 미지수**: 첫 Loop-01 실행에서 100-episode smoke가 얼마나 걸리는지 측정 후 Loop-06 계획.

---

## 6. 즉시 진행 계획

1. Loop-01 실행 → metrics.json 분석 → 09_loop_01_proxy_off_eval.md 업데이트
2. Loop-06 실행 → metrics.json 분석 → 09_loop_06_fair_compute_matching.md 업데이트
3. Loop-03/02 BLOCKED 사유와 launcher 패치 후보를 11_final_risk_hunt_execution_report.md에 기록

---

## 7. Blockers

- Loop-03/02 launcher 결함 (사실 확인, 수정 후보로 기록 — 즉시 코드 수정은 보류)

end.
