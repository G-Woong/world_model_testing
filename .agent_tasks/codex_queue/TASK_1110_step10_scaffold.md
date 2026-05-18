TASK_NAME: TASK_1110_step10_scaffold
BACKGROUND:
STEP 10 Risk-Hunt Recovery Loop를 위해 새 디렉터리 구조가 필요하다.
docs/orchestration/risk_hunt/ 와 outputs/risk_hunt/ 두 루트 아래 총 11개 서브디렉터리를 생성하고
각각 .gitkeep 파일을 추가해야 한다. .gitignore에 예외 규칙을 추가하고
디렉터리 존재를 검증하는 pytest 테스트 파일을 작성해야 한다.

GOAL:
1. docs/orchestration/risk_hunt/ 아래 9개 서브디렉터리 생성 (.gitkeep 포함)
2. outputs/risk_hunt/ 아래 3개 서브디렉터리 생성 (.gitkeep 포함)
3. .gitignore 에 outputs/risk_hunt/ 예외 추가 (outputs/ 는 이미 무시되지 않으나 명시)
4. tests/test_step10_scaffold.py 작성 — 모든 디렉터리 존재 assert

FILES_ALLOWED:
docs/orchestration/risk_hunt/
outputs/risk_hunt/
.gitignore
tests/test_step10_scaffold.py

FILES_FORBIDDEN:
.claude/
CLAUDE.md
.mcp.json
.venv/
data/
outputs/phase_gates/
outputs/checkpoints/
outputs/runs/
secrets/
.env
scripts/run_codex_task.ps1
paper_context_ref/
src/frcgw/schemas/visibility.py
src/frcgw/schemas/step_schema.py

REQUIRED_IMPLEMENTATION:
1. 아래 디렉터리 전부 생성 (없으면 생성):
   docs/orchestration/risk_hunt/
   docs/orchestration/risk_hunt/literature/
   docs/orchestration/risk_hunt/datasets/
   docs/orchestration/risk_hunt/architecture/
   docs/orchestration/risk_hunt/losses/
   docs/orchestration/risk_hunt/evaluation/
   docs/orchestration/risk_hunt/codex_tasks/
   docs/orchestration/risk_hunt/loop_reports/
   outputs/risk_hunt/
   outputs/risk_hunt/audits/
   outputs/risk_hunt/experiments/
   outputs/risk_hunt/dataset_feasibility/

2. 각 디렉터리에 .gitkeep 파일 생성 (내용 없음)

3. .gitignore 에 다음 섹션 추가 (이미 있으면 스킵):
   # risk_hunt outputs - keep gitkeep markers
   !outputs/risk_hunt/**/.gitkeep

4. tests/test_step10_scaffold.py 작성:
   ```python
   """STEP 10 scaffold directory existence test."""
   import pathlib
   import pytest

   REQUIRED_DIRS = [
       "docs/orchestration/risk_hunt",
       "docs/orchestration/risk_hunt/literature",
       "docs/orchestration/risk_hunt/datasets",
       "docs/orchestration/risk_hunt/architecture",
       "docs/orchestration/risk_hunt/losses",
       "docs/orchestration/risk_hunt/evaluation",
       "docs/orchestration/risk_hunt/codex_tasks",
       "docs/orchestration/risk_hunt/loop_reports",
       "outputs/risk_hunt",
       "outputs/risk_hunt/audits",
       "outputs/risk_hunt/experiments",
       "outputs/risk_hunt/dataset_feasibility",
   ]

   REPO_ROOT = pathlib.Path(__file__).parent.parent

   @pytest.mark.parametrize("rel_path", REQUIRED_DIRS)
   def test_risk_hunt_dir_exists(rel_path: str) -> None:
       assert (REPO_ROOT / rel_path).is_dir(), f"Missing: {rel_path}"
   ```

REQUIRED_TESTS:
tests/test_step10_scaffold.py — pytest -q tests/test_step10_scaffold.py → 12 passed

ACCEPTANCE_CRITERIA:
- 12개 디렉터리 모두 존재
- 각 디렉터리에 .gitkeep 파일 존재
- tests/test_step10_scaffold.py 12 assertions all PASS
- .gitignore에 risk_hunt 예외 라인 존재
- forbidden path 미수정

COMMIT_MESSAGE:
feat(step10): scaffold risk_hunt directory structure + scaffold test

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
test 12개 미만 PASS 시 abort.
