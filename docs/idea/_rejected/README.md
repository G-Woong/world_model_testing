# docs/idea/_rejected/

This directory contains atomic idea units that failed C1..C10 checkpoint validation.

## Policy

A sub-claim is moved here when:
- ANY checkpoint returns FAIL (not just CONDITIONAL)
- The failure has no documented mitigation
- The user's requirement: "체크포인트를 원자 단위 분해마다 반드시 10개 이상씩 놓고 이를 전부 통과한 사항만을 docs/idea.md에 남겨라"

## Current Contents

(Empty — no FAILed sub-claims as of 2026-05-22 session)

## Format

Each rejected file should document:
- Unit ID (M-* or R-*)
- Which checkpoint failed
- Why no mitigation is possible
- Original content pointer
