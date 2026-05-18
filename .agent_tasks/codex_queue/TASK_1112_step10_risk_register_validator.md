TASK_NAME: TASK_1112_step10_risk_register_validator
SANDBOX_MODE: bypass
BACKGROUND:
STEP 10 STEP 1에서 01_global_risk_register.md (60개 risk, 20 카테고리)가 작성되었다.
이 register의 11-field schema를 자동으로 검증하는 validator script와 JSON 출력이 필요하다.

GOAL:
1. scripts/risk_hunt/validate_risk_register.py 작성 — markdown 파싱 후 11-field schema 검증
2. 출력: outputs/risk_hunt/audits/risk_register_<ts>.json
3. tests/test_step10_risk_register_schema.py 작성

FILES_ALLOWED:
scripts/risk_hunt/
outputs/risk_hunt/audits/
tests/test_step10_risk_register_schema.py

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
docs/orchestration/risk_hunt/01_global_risk_register.md

REQUIRED_IMPLEMENTATION:
1. scripts/risk_hunt/validate_risk_register.py:
   - 입력: docs/orchestration/risk_hunt/01_global_risk_register.md (읽기 전용)
   - 파싱: ### RH-<CAT>-<NN> 헤더로 각 risk 섹션 분리
   - 검증 항목 (11-field schema):
     1. Risk ID (RH-<CAT>-<NN> 형식)
     2. Risk statement (non-empty)
     3. Severity (CRITICAL/HIGH/MEDIUM/LOW 중 하나)
     4. Affected claim (non-empty)
     5. Current evidence (non-empty, 파일:라인 참조 포함 권장)
     6. Why this kills the paper (non-empty)
     7. Required test (non-empty)
     8. Candidate fix idea (non-empty)
     9. Codex implementation task (non-empty, N/A 허용)
     10. Stop condition (non-empty)
     11. Status (OPEN/TESTING/MITIGATED/REJECTED/BLOCKED_WITH_EVIDENCE/ACTIVE_CONSTRAINT 중 하나)
   - 카테고리별 집계:
     - CORE, THR, FORE, PCG, LAT, REG, DUP, ENV, OXE, CF, ARC, LOSS, LONG, EVAL, DTB, FAI, STAT, REV, NOV, LEAK
   - 출력 JSON:
     {
       "validation_timestamp": "<ISO timestamp>",
       "total_risks": int,
       "valid_risks": int,
       "invalid_risks": [...],
       "category_counts": {"CORE": n, ...},
       "severity_counts": {"CRITICAL": n, "HIGH": n, "MEDIUM": n, "LOW": n},
       "status_counts": {"OPEN": n, ...},
       "schema_valid": bool,
       "gate_o_risk_pass": bool  // total_risks >= 50 AND all 20 categories present
     }
   - 파일명: outputs/risk_hunt/audits/risk_register_{YYYYMMDD_HHMMSS}.json
   - --dry-run 옵션: JSON을 stdout에만 출력, 파일 저장 없음

2. tests/test_step10_risk_register_schema.py:
   ```python
   """Risk register schema validation test."""
   import json
   import subprocess
   import pathlib
   import pytest

   REPO_ROOT = pathlib.Path(__file__).parent.parent
   REGISTER_PATH = REPO_ROOT / "docs/orchestration/risk_hunt/01_global_risk_register.md"

   def test_register_file_exists():
       assert REGISTER_PATH.exists(), "01_global_risk_register.md not found"

   def test_validator_runs():
       result = subprocess.run(
           ["python", "scripts/risk_hunt/validate_risk_register.py", "--dry-run"],
           cwd=REPO_ROOT,
           capture_output=True,
           text=True,
           timeout=30,
       )
       assert result.returncode == 0, result.stderr
       data = json.loads(result.stdout)
       assert data["total_risks"] >= 50, f"Only {data['total_risks']} risks, need >= 50"
       assert data["schema_valid"], f"Schema invalid: {data.get('invalid_risks', [])}"

   def test_gate_o_risk_pass():
       result = subprocess.run(
           ["python", "scripts/risk_hunt/validate_risk_register.py", "--dry-run"],
           cwd=REPO_ROOT,
           capture_output=True,
           text=True,
           timeout=30,
       )
       assert result.returncode == 0
       data = json.loads(result.stdout)
       assert data["gate_o_risk_pass"], "Gate O-RISK not passed"

   def test_all_20_categories_present():
       result = subprocess.run(
           ["python", "scripts/risk_hunt/validate_risk_register.py", "--dry-run"],
           cwd=REPO_ROOT,
           capture_output=True,
           text=True,
           timeout=30,
       )
       assert result.returncode == 0
       data = json.loads(result.stdout)
       expected_cats = {"CORE","THR","FORE","PCG","LAT","REG","DUP","ENV","OXE","CF","ARC","LOSS","LONG","EVAL","DTB","FAI","STAT","REV","NOV","LEAK"}
       found_cats = set(data["category_counts"].keys())
       missing = expected_cats - found_cats
       assert not missing, f"Missing categories: {missing}"
   ```

REQUIRED_TESTS:
tests/test_step10_risk_register_schema.py → pytest -q → 4 passed

ACCEPTANCE_CRITERIA:
- scripts/risk_hunt/validate_risk_register.py 존재
- --dry-run 실행 시 valid JSON stdout 출력
- total_risks >= 50
- schema_valid = true
- gate_o_risk_pass = true
- 20 카테고리 모두 category_counts에 존재
- test_step10_risk_register_schema.py 4 passed

COMMIT_MESSAGE:
feat(step10): validate_risk_register.py + schema validation test

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
01_global_risk_register.md 수정 시 즉시 abort (읽기 전용).
