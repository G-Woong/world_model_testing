---
file_id: RISK-HUNT-ARCHIVE
title: Risk Hunt Phase (STEP 10) — Compressed Archive (2026-05-19)
status: ARCHIVED_SUMMARY
replaces: docs/orchestration/risk_hunt/ (33 files, 326KB)
date_archived: 2026-05-22
---

# Risk Hunt Phase Archive

이 파일은 `docs/orchestration/risk_hunt/` (33 파일, 326KB)의 핵심을 1장으로 압축한 아카이브다.
원본 파일들은 2026-05-22 정리 시 삭제됨. 재현 필요 시 git history 참조.

---

## 1. 최종 Verdict

**`CLAIM_SHRINK_REQUIRED`** (2026-05-19 STEP 10 Phase 2 loop 실행 후)

---

## 2. Loop 결과 요약

| Loop | 테스트 | 결과 | Verdict |
|---|---|---|---|
| Loop-01 | proxy OFF eval (C3 학습 신호 검증) | F1: proxy-ON 0.581 → proxy-OFF **0.000** | **REJECT: 학습된 신호 없음** |
| Loop-02 | 5-seed stochastic eval | C3 F1 std=0.075 (range 0.42–0.58) | VALID (분산 해소) |
| Loop-03 | ABL-001/003 faithful retrain | reference도 C2=0 → contrast 불가 | **C2 DEAD** |
| Loop-06 | fair compute matching (ABL-036b) | C6 ratio = **2.00×** (14.9× artifact) | **C6 SHRUNK** |

---

## 3. Claim 재판정

| Claim | STEP 9 보고 | STEP 10 최종 | 원인 |
|---|---|---|---|
| C3 falsification LR | f1=0.539/0.587 | **DEAD** | proxy artifact (no_state_change 휴리스틱 의존) |
| C2 regime separability | f1=0.0 (데이터 한계) | **DEAD at current setup** | ABL collapse contrast 불가 |
| C6 compute gate | 14.9× PPC | **SHRUNK → 2.0×** | 분모가 heuristic-bypass ablation이었음 |
| C1 wrong-grammar persistence | ALIVE | 미재검증 (lower priority) | — |
| C5 action-interface rewrite | ALIVE (moderate) | 미재검증 | — |

---

## 4. 코드 변경 사항 (STEP 10 loop에서 적용)

모두 "path/checkpoint/argparse 누락 launcher 결함" 수정. 연구 알고리즘 변경 없음.

1. `scripts/10_run_lr_real_eval.py` — `RealNoGateAblation`, `NoComputeGateAblation` dispatch 등록
2. `scripts/risk_hunt/run_abl001_retrain.py`, `run_abl003_retrain.py` — `--output-dir` + promote 단계
3. `scripts/02_train_text_smoke.py` — `--seed`, `--checkpoint-dir` argparse 추가
4. `scripts/risk_hunt/run_multiseed_training.py` — promote 단계 추가

---

## 5. 주요 출력물 위치

| 아티팩트 | 경로 |
|---|---|
| Loop-01 proxy results | `outputs/risk_hunt/experiments/loop01_proxy_ablation/` |
| Loop-02 multiseed | `outputs/risk_hunt/experiments/loop02_multiseed/` |
| Loop-03 ABL retrain | `outputs/risk_hunt/experiments/loop03_abl001_retrain/`, `loop03_abl003_retrain/` |
| Loop-06 fair compute | `outputs/risk_hunt/experiments/loop06_fair_compute/` |
| ABL checkpoints | `outputs/checkpoints/abl001_no_regime/`, `abl003_merged_regime_grammar/`, `pretrain_v0_4_seed{42,123,456,789,999}/` |

---

## 6. 후속 과제 (미완)

- Loop-04 foresight causal: NOT RUN (Codex task 후보)
- C1/C5 재검증: 우선순위 낮음
- **차세대 환경 설계**: CLAIM_SHRINK 후 new WM 환경에서 C2/C3 재성립 필요

---

## 7. 핵심 교훈

> STEP 9의 C3 회복 (f1=0.539)과 C6 14.9× 모두 **학습된 model signal이 아닌 proxy/heuristic artifact**였다.
> 이는 paper main claim의 본질적 재구성을 요구한다.
> 새 WM 환경 없이는 C2/C3 empirical evidence 성립 불가.
