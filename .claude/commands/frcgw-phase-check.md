# frcgw-phase-check

## Purpose

현재 phase gate 상태를 점검하고, PASS sentinel을 관리한다.

FRCG-WM 구현 phase 경계(P0~P8)에서 반드시 실행한다.

---

## Usage

```text
/frcgw-phase-check
/frcgw-phase-check --phase P2
/frcgw-phase-check --pass P2
/frcgw-phase-check --override P3 "reasons for intentional override"
```

---

## Actions

### Default (`/frcgw-phase-check`)

1. `outputs/phase_gates/` 디렉토리에서 `*.passed` sentinel 목록을 확인한다.
2. `plans/PHASE_PROGRESS.md`를 읽어 마지막 recorded phase를 확인한다.
3. 기존 4개 hook + 7개 hook의 정상 동작 여부를 설명한다.
4. pytest 결과를 확인하라는 권고를 출력한다.
5. 응답 형식을 강제 출력:

```
Phase Status:
  P0: PASS (sentinel present)
  P1: PASS (sentinel present)
  P1.5: IN_PROGRESS (no sentinel — harness setup phase)
  P2: PENDING (no sentinel)
  ...

Next Action:
  ...

Blockers:
  none / <list>
```

---

### `--pass <phase>` (gate 통과 마크)

사용 조건:
- `pytest -q` 전부 통과.
- 해당 phase의 required gate(13§16, 14§10)가 전부 PASS.
- 사용자가 명시적으로 승인.

동작:
- `outputs/phase_gates/<phase>.passed` 파일 생성.
- `plans/PHASE_PROGRESS.md`에 타임스탬프 + PASS 기록.

---

### `--override <phase> "<reason>"` (강제 진행)

사용 조건:
- 사용자가 명시적으로 사유를 제공.

동작:
- `outputs/phase_gates/<phase>.passed` 임시 생성 + override 사유 기록.
- `plans/PHASE_PROGRESS.md`에 `OVERRIDE` 마크 + 사유 기록.
- 경고 출력: "Phase gate was OVERRIDDEN. Scientific contract may be at risk."

---

## Required Read Before Running

- `paper_context_ref/00_CONTEXT_INDEX.md` §5 phase router.
- `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` §5, §16.
- `paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md` §10.

---

## Stop Conditions

- 이전 phase gate sentinel 없이 `--pass <next_phase>` 불가.
- fake metric으로 PASS 마크 불가.
- 실패한 pytest 있는 상태에서 PASS 마크 불가.
