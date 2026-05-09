---
description: >
  FRCG-WM phase 시작/종료 시 강제 응답 형식(Read/Phase/Changed/Tests/Gates/Blockers)을 적용하고
  phase gate PASS sentinel을 검증한다. 사용자가 "P2 시작", "phase 끝났다",
  "다음 phase로 가자" 같은 발화를 하거나 /frcgw-phase-check 명령을 호출할 때 사용한다.
---

# frcgw-phase-gate

Source MDs: `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` §5, §16;
`paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md` §10;
`paper_context_ref/00_CONTEXT_INDEX.md` §5.

## Checklist (모든 항목 명시)

1. 어떤 MD를 읽었는가.
2. 현재 phase + 직전 gate status (PASS / PENDING / BLOCKED).
3. 변경 또는 생성한 파일 목록.
4. 실행한 pytest + 새로 추가한 testcase.
5. must-not-disappear baseline/ablation 위반 여부.
6. Blockers 또는 `none`.

## Output Format (이 형식 외 허용하지 않는다)

```
Read:
  - <MD files read this turn>

Phase:
  - <current phase> | gate status: <PASS / PENDING / BLOCKED>

Changed/Created:
  - <file list>

Tests/Gates:
  - <tests run + new tests>

Blockers:
  - <blockers or none>
```

## Forbidden Actions

- gate PASS sentinel(`outputs/phase_gates/<phase>.passed`) 없이 다음 phase main script 실행.
- phase artifact가 불완전한 상태에서 PASS 마크.
- baseline / ablation must-not-disappear 목록 항목 누락 확인 없이 eval 진행.

## Gate Sentinel Policy

- sentinel 위치: `outputs/phase_gates/P<N>.passed`
- sentinel 부재: Bash `python scripts/0<N>_*.py` 실행 → `phase_gate_guard.ps1` BLOCK.
- sentinel 생성: `/frcgw-phase-check` command 또는 사용자 명시 승인 후 main agent가 `touch`.
- override: `/frcgw-phase-check --override <reason>` → 사유 로그 + 임시 sentinel.

## Stop Condition

gate 통과 못 하면 응답 끝에 `BLOCKED: <reason>` 출력 후 구현 중단.
