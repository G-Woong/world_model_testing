# P0_REPO_SCAFFOLD_PLAN.md

---

## 0. Context

이 변경의 동기는 다음 두 가지다.

1. 직전 commit `2d20edd archive first failed experiment baseline`에서 기존 실험 트리(`falsifiable_regime_world_model/`, `configs/wm_*`, `docs/SESSION*` 등 111개 파일)가 "실패한 첫 baseline"으로 명시 archive 되었다. 현재 working tree는 그 코드를 모두 비운 상태이며, `paper_context_ref/`(설계 계약), `CLAUDE.md`, `.claude/` hooks, `.mcp.json`, 변경된 `.gitignore`, 기존 `requirements.txt`만 존재한다.
2. `paper_context_ref/13_..._ROADMAP_v1.md` §6 (CC-P0)는 "모델 로직 없이 repo scaffold + placeholder + docstring contract + 최소 pytest 실행"까지를 P0의 단일 목표로 못 박는다. P0는 mechanism 구현, 데이터 생성, 학습이 일절 들어가지 않는 phase다.

목표 결과(요약):
- `frcgw/` 패키지 skeleton과 11개 sub-package placeholder, 7개 config skeleton, scripts/ 10개 placeholder, tests/ 최소 4개 placeholder, README.md, pyproject.toml, data/ outputs/ README가 working tree에 존재한다.
- `paper_context_ref/` 원본은 절대 수정되지 않는다.
- `pytest`가 placeholder 테스트로 통과한다.
- 이전 archive(2d20edd)는 backup tag로 박제되어 잃지 않는다.
- P0 외 어떤 mechanism/data/model/loss/planner/eval 코드도 작성되지 않는다.

---

## 1. Read Context

### 1.1 Read in this plan turn
- `CLAUDE.md` — first rule, scientific/data 절대 규칙, baselines/ablations must-not-disappear, response policy.
- `.claude/rules/research_context_rules.md` — terms must-preserve, stop conditions, response format.
- `paper_context_ref/00_CONTEXT_INDEX.md` — context router, must-preserve terms, must-not-disappear baselines/ablations, P0~P8 phase router (§5).
- `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` — §3 read policy, §4 required repo layout, §6 CC-P0 명세, §15.1 scaffold prompt template, §16 quality gates, §20 docstring pattern, §21 config principles.
- `paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md` — §3 scope, §6.1 doc requirements, §10.1 P0 acceptance, §11 prohibited shortcuts.
- `paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md` — §3 target arch, §4 package map, §5 core data types (forward-reference only).

### 1.2 Distilled rules that bind P0
- (CLAUDE.md First Rule) 모든 작업 시작 전 `paper_context_ref/00_CONTEXT_INDEX.md`를 먼저 읽어야 한다.
- (CLAUDE.md Required Execution Order) `1. docs/scaffold` → `2. schema/visibility tests` 순서. P0는 1번에만 머무른다.
- (00_CONTEXT_INDEX.md §5, P0) Required gate = "repo scaffold and docs present".
- (13 §6.2) P0 산출물: `README.md`, `pyproject.toml`, schema-valid `configs/*.yaml`, `src/frcgw/__init__.py`, `tests/` placeholder.
- (13 §6.3) P0 gate: 디렉터리 존재 / docs router / README의 forbidden assumption / pytest 통과.
- (13 §20) 모든 major module docstring은 source-doc contract를 포함해야 하고, 그 경로는 `paper_context_ref/...`로 참조한다(원본 보존 정책).
- (13 §21) explicit paths/seed/split/visibility/compute_budget/ablation/version/forbidden_fields 8가지 config 원칙. P0는 "key 자리만" 비워둔다(값은 P1 이후에 채움).
- (14 §10.1) P0 acceptance: docs 00~14 present, repo scaffold created, README의 forbidden assumption, pytest runs, no model logic required.
- (14 §11) prohibited shortcuts — P0에서 모델/데이터/baseline 어떤 것도 미리 만들지 않는다.
- (15 §3) repo arch는 `frcgw/` 루트 아래 `src/frcgw/{schemas,text_env,gui_env,logging,data,models,objectives,planning,training,evaluation,reporting,utils}` 11 sub-package + `scripts/` + `tests/` + `data/` + `outputs/` + `configs/` + `docs/` + `paper_context_ref/`.
- (15 §4) `schemas`는 utils 외 의존 금지, `models`는 schemas의 field name 외 의존 금지, `evaluation`은 training-only label을 input으로 받지 않음 — package layering 규칙은 P0 placeholder docstring에 미리 명시한다.

---

## 2. Current Repository Inspection

### 2.1 Present at project root
- `.git/`, `.gitignore`(M), `.venv/`, `.claude/` (rules, commands, hooks, settings), `.mcp.json`, `CLAUDE.md`, `paper_context_ref/`(18 design MDs), `requirements.txt`.

### 2.2 Absent (not in working tree, not tracked)
- `README.md`, `pyproject.toml`
- `configs/`, `docs/`, `scripts/`, `tests/`, `data/`, `outputs/`, `plans/`
- `src/`, `src/frcgw/`, 12 sub-packages (11 + reporting)

### 2.3 Git status summary
- HEAD commit: `2d20edd archive first failed experiment baseline` (111 tracked files: failed first baseline).
- Working tree에서 그 111개 파일은 모두 deleted(unstaged) 로 표시 — 정상. archive 의도와 일치한다.
- `.gitignore`: M (secrets/`.token`/`.secret`/`.mcp.secrets.json`/`secrets/`/`.claude/.session_*.lock` 추가 — 적절).
- Branch: `main` (only branch).
- Archive tag `archive/first-failed-baseline-pre-frcgw` → `2d20edd` 생성 완료.

### 2.4 Risk from deleted files
- 111개 deleted 파일은 "실패한 baseline 잔재"로 의도된 archive 결과다. 자동 복원 금지.
- archive 자체는 history(2d20edd) + backup tag에 안전히 보존.
- P0 scaffold의 신규 경로와 deleted 파일 경로는 file 단위에서 disjoint.

---

## 3. P0 Scope

### 3.1 In scope (this P0)
1. 신규 디렉터리 생성: `configs/`, `docs/`, `scripts/`, `src/`, `src/frcgw/` 및 12 sub-packages (11 + reporting), `tests/`, `data/`, `outputs/`, `plans/`.
2. `README.md`, `pyproject.toml` 작성(P0 minimal).
3. `configs/` 7개 yaml skeleton — 키만 자리, 값은 `null`.
4. `src/frcgw/__init__.py` + 12 sub-package `__init__.py` (source-doc contract docstring, 코드 로직 없음).
5. `scripts/` 10개 placeholder `.py` (stdlib only, `raise NotImplementedError`).
6. `tests/` 4개 placeholder 테스트.
7. `docs/README.md` — router.
8. `data/README.md`, `outputs/README.md`.
9. `plans/P0_REPO_SCAFFOLD_PLAN.md` — 본 계획서.
10. `.gitignore` patch: `!data/README.md`, `!outputs/README.md`.

### 3.2 Out of scope (절대 P0에서 하지 않는다)
- schema/visibility/validator 구현(P1).
- text/GUI environment, generator, collector, replay (P2/P4).
- model/encoder/head/loss/reward 구현 (P3/P5).
- planner, falsification, alternative proposer, decision gate, rewrite (P3+).
- evaluation, baselines, ablations, metrics, reports (P6/P8).
- VLM adapter / 7B 학습 / data download (P5/P7).
- hidden-label/leakage auditor 실코드(P1).
- 기존 deleted 파일 복원, archive 커밋 rebase, commit/push 실행.
- `paper_context_ref/*.md` 어떤 파일도 수정.

---

## 4. Target Directory Structure

```text
NeurIPS2026/
├── .claude/                             # 기존, 유지
├── .git/                                # 기존, 유지
├── .gitignore                           # 변경(§5.10)
├── .mcp.json                            # 기존, 유지
├── .venv/                               # 기존, 무시
├── CLAUDE.md                            # 기존, 유지
├── README.md                            # P0 신규
├── pyproject.toml                       # P0 신규
├── requirements.txt                     # 기존, 유지
├── configs/
│   ├── text_smoke.yaml
│   ├── data_collection_text.yaml
│   ├── data_collection_gui_mve.yaml
│   ├── model_text.yaml
│   ├── train_text.yaml
│   ├── eval_text.yaml
│   └── ablation_core.yaml
├── docs/
│   └── README.md
├── paper_context_ref/                   # READ-ONLY (18 MDs)
├── src/
│   └── frcgw/
│       ├── __init__.py
│       ├── schemas/__init__.py
│       ├── text_env/__init__.py
│       ├── gui_env/__init__.py
│       ├── logging/__init__.py
│       ├── data/__init__.py
│       ├── models/__init__.py
│       ├── objectives/__init__.py
│       ├── planning/__init__.py
│       ├── training/__init__.py
│       ├── evaluation/__init__.py
│       ├── reporting/__init__.py
│       └── utils/__init__.py
├── scripts/
│   ├── 00_validate_docs.py ... 09_generate_reports.py
├── tests/
│   ├── __init__.py
│   ├── test_p0_scaffold.py
│   ├── test_p0_paper_context_ref_present.py
│   ├── test_p0_readme_contract.py
│   └── test_p0_no_fake_result_marker.py
├── data/
│   └── README.md
├── outputs/
│   └── README.md
└── plans/
    └── P0_REPO_SCAFFOLD_PLAN.md
```

---

## 5. Gate Criteria (P0 PASS 조건)

1. directory skeleton exists.
2. `README.md` exists + §5.1 키워드 모두 포함.
3. `pyproject.toml` exists + `pip install -e ".[dev]"` 성공.
4. `configs/` 7개 yaml schema-valid + `phase`, `source_docs`, `forbidden_fields` 키 존재.
5. `src/frcgw/` import-able, 12 sub-packages 모두 import-able.
6. `scripts/` 10개 syntactically valid.
7. `pytest -q` 0 exit code.
8. `git diff paper_context_ref` 비어 있음.
9. 변경 파일 전부 P0 범위 내.
10. backup tag `archive/first-failed-baseline-pre-frcgw` → `2d20edd` 존재.
11. 14 §10.1 P0 acceptance 5개 항목 만족.

---

## 6. Commit Policy

commit을 P0의 일부로 강제하지 않는다(사용자 명시 승인 필요).

권장 commit 분리:
1. `chore(p0): scaffold frcgw repo per paper_context_ref/13`
2. `docs(p0): add docs/README router and data/outputs placeholders`

`git push`, `git rebase`, `git reset --hard`, `--no-verify` 금지.

---

## 7. Risks and Blockers

| Risk | Mitigation |
|---|---|
| deleted 파일 자동 복원 | git restore/checkout 류 명령 사용 안 함 |
| paper_context_ref/ 수정 | git diff paper_context_ref 검사 |
| pyproject 의존성 과다화 | pytest 1개만, torch/transformers 금지 |
| .gitignore data/outputs 무차별 ignore | !data/README.md, !outputs/README.md 단일 파일 negation만 |
| placeholder fake-result 토큰 | test_p0_no_fake_result_marker.py 자동 차단 |
| scripts에서 외부 라이브러리 import | stdlib만 사용(argparse, __future__) |
