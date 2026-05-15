# Codex Report Template

근거: `docs/orchestration/04_CODEX_FEEDBACK_LOOP_PROTOCOL.md §7`

Codex task 완료 후 Main Claude가 review 결과를 기록하는 공식 report.
`.agent_tasks/codex_done/TASK_<N>_<NAME>_RESULT.md`와 병존하나, Phase 3 이후 신규 task는 이 파일이 공식 기록.

---

```yaml
task_id: TASK_XXXX
branch: codex/TASK_XXXX_<short> | codex-work
commit_hash: <SHA>
files_changed:
  - <파일 경로 1>
  - <파일 경로 2>
allowed_files_compliance: PASS | FAIL
tests_run:
  - tests/test_<module>.py
test_results: PASS | FAIL
rejection_id_handled:
  - REJ_TASK_XXXX_NNN | none
rejection_response_table: |
  | rejection_id | blocking_reason | fix_applied | verification |
  |---|---|---|---|
diff_summary: >
  <3~5줄 요약>
risk_notes: <위험/불확실성>
ready_for_claude_review: YES | NO
```

---

## Gatekeeper 5조건 체크리스트

- [ ] verify mode 종료 코드 0
- [ ] `git diff --cached` 수동 review — 의도치 않은 변경 없음
- [ ] 금지 경로 미수정
- [ ] RESULT.md 존재 확인
- [ ] REQUIRED_TESTS 통과 재확인
