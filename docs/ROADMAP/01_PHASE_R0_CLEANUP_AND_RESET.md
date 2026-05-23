# Phase R0 — 정리 및 계약 초기화

## 상태: 완료 (2026-05-22)

## 목표
FRCG-WM 아티팩트를 아카이빙하고 FGLC를 위한 연구 계약을 재작성합니다.

## 완료된 단계
1. A.1: src/frcgw/, paper_context_ref/, configs/, tests/, scripts/를 .lifecycle_trash/에 아카이빙
2. A.2: Phase gate sentinel P*.passed → R*.passed 규약으로 초기화
3. A.3: CLAUDE.md, research_context_rules.md, behavioral_coding_rules.md,
        codex_orchestration_rules.md, baseline_ablation_guard.ps1, phase_gate_guard.ps1 재작성
4. A.4: fglc-context-router.md, fglc-code-reviewer.md, fglc-related-work-scout.md 생성
5. A.5: pyproject.toml 업데이트 (frcgw → fglc), src/fglc/ 스텁 생성

## 생성된 산출물
- `CLAUDE.md` — FGLC 과학 계약
- `.claude/rules/research_context_rules.md` — FGLC 연구 규칙
- `src/fglc/__init__.py` + `py.typed` — 패키지 스텁
- `docs/idea/00_OVERVIEW.md` ~ `26_CROSSCHECK_SUMMARY.md` — 27개 아이디어 파일
- `docs/ROADMAP/` — 로드맵 파일 (이 세션)
- 에이전트 보고서: `docs/orchestration/agent_reports/synthesis/2026-05/`

## Gate 기준

R0.passed를 위해 모두 true여야 함:
- [x] CLAUDE.md에 FGLC 계약 포함 (FRCG-WM 용어 없음)
- [x] src/frcgw/가 src/에 없음 (아카이빙됨)
- [x] paper_context_ref/가 없음 (아카이빙됨)
- [x] outputs/phase_gates/*.passed 없음 (P*.passed 파일 없음)
- [x] src/fglc/__init__.py 임포트 가능
- [x] docs/idea/00_OVERVIEW.md 존재
- [x] pytest tests/test_lifecycle_*.py 통과 (이 세션 후 검증됨)

## 커밋 참조
- A.1+A.2: `cae2c8d`
- A.3+A.4+A.5: `73087a4`
- F+G (idea+roadmap): `8174ab1`
- R0.passed sentinel: `ca92ff4`

## 위험 등록부 참조
- R-19 (ROADMAP/19): 라이프사이클 hook이 세션 중간에 자동 커밋할 수 있음
