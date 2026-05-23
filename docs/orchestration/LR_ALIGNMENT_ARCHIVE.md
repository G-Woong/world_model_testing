---
file_id: LR-ALIGNMENT-ARCHIVE
title: LR Alignment Phase — Compressed Archive (2026-05)
status: ARCHIVED_SUMMARY
replaces: docs/orchestration/lr_alignment/ (55 files, 514KB)
date_archived: 2026-05-22
---

# LR Alignment Phase Archive

이 파일은 `docs/orchestration/lr_alignment/` (STEP 0–48, 55 파일, 514KB)의 핵심을 1장으로 압축한 아카이브다.
원본 파일들은 2026-05-22 정리 시 삭제됨. 재현이 필요하면 git history 참조.

---

## 1. 핵심 결정 (DEC-OPTION-B)

**결정**: Option B 채택 — 구현을 이론에 맞춘다.

| 항목 | 내용 |
|---|---|
| Main path | `LikelihoodRatioFalsificationScorer` |
| Ablation path | `BCEBinaryFalsificationScorer` → ABL-022/023 |
| 이론 F_t | `max_{h_alt} [ell_t(h_alt) − ell_t(h_exec)]` (09_PLANNING §172) |
| 이론-구현 gap | BCE로는 LR approximation만 가능 → LR을 main으로 올림 |

근거: War Room R1 (verdict C, AT_RISK) + math_critic RISK_HIGH (C3) + 4개 FATAL_FLAW.

---

## 2. STEP 1–9 실행 결과 (P3 완료 기준)

| STEP | 목적 | 최종 결과 |
|---|---|---|
| 1–4 | real eval runner 구현, dataset backfill | v0_4 5000 ep, leakage=0 |
| 5 | LR score 배선, namespace alignment | lr_scorer.py 완성 |
| 6 | falsification eval gate | PlannerState 동결 문제 발견 |
| 7 | C4 expanded validation | C4 moderate, C6 14.9× (STEP 9 기준) |
| 8 | full test eval, direct threat baseline | ABL-040 positive control 확인 |
| 9 | C3 root cause fix (tau_f 과보수, eval asymmetry) | C3 f1=0.539/0.587 (BREAKTHROUGH) |

---

## 3. Evidence Card 요약 (STEP 9 기준)

| Claim | Metric | STEP 9 Status | Note |
|---|---|---|---|
| C1 wrong-grammar persistence | wgp_f1 | ALIVE (moderate) | 회귀 없음 |
| C2 regime separability | regime_shift_f1=0.0 | AT_RISK | v0_4 단일 regime 한계 |
| C3 falsification LR score | f1=0.539/0.587 | PRELIMINARY_PLUS | STEP 10에서 DEAD 판명 |
| C4 alt-hypothesis WM | moderate effect | CONDITIONAL | n=5 필요 |
| C5 action-interface rewrite | rewrite accuracy | ALIVE (moderate) | |
| C6 compute gate | ppc=14.9× | STRONG | STEP 10에서 2.0×으로 축소 |

> **STEP 10 후속**: C3/C6 모두 proxy artifact로 판명 → CLAIM_SHRINK_REQUIRED
> 상세: `docs/orchestration/RISK_HUNT_ARCHIVE.md`

---

## 4. Phase Gate 달성 순서

P3_EVAL → P3_LR_EVAL → P3_LR_REAL_EVAL → P3_STEP3..9 → P3_STEP9_C3_RECOVERY.passed

---

## 5. 주요 코드 위치

| 컴포넌트 | 파일 |
|---|---|
| LR scorer | `src/frcgw/falsification/lr_scorer.py` |
| Planner | `src/frcgw/planning/planner.py` |
| Eval runner | `src/frcgw/evaluation/eval_runner.py` |
| Step 9 configs | `configs/lr_eval_step9_c3_recovery.yaml` |
