# P2 Gate Report (2026-05-08)

## Read
- plans/P2_TEXT_ONLY_DATA_PLAN.md
- paper_context_ref/00_CONTEXT_INDEX.md (via CLAUDE.md routing)
- paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md §3, §6, §11
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §5–§14, §19
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.3, §0.4, §4, §7, §14, §15
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §7, §8, §10, §13, §16
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §8 P2 spec
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §6, §10
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §5, §6
- src/frcgw/schemas/*.py (P1 schema files, read-only reference)
- src/frcgw/data/leakage_auditor.py (P1 leakage guard, read-only)
- configs/ablation_core.yaml (must-not-disappear baseline check)

## Phase
- P2 | gate status: PASS

## Changed/Created

### New source files
- src/frcgw/text_env/state.py         — TextState, TextEpisodeSpec, TextStepResult
- src/frcgw/text_env/grammar.py        — ControlGrammar (8 grammars), GrammarEngine
- src/frcgw/text_env/generator.py      — TaskFamily (8 families), TaskFamilyTemplate, EpisodeSpecGenerator, build_initial_state
- src/frcgw/text_env/policies.py       — Oracle/WrongGrammar/Retry/Recovery/RandomConstrained + PolicyMixtureRunner
- src/frcgw/text_env/collector.py      — collect_episode(), build_public_observation()
- src/frcgw/text_env/replay.py         — ReplayValidator
- src/frcgw/data/coverage_auditor.py   — CoverageAuditor, CoverageReport (CA-001~006)
- src/frcgw/data/shard_exporter.py     — ShardExporter (JSONL + manifest)

### New test files
- tests/test_text_env.py               — 18 tests (state transition, hidden field absence, 4-condition wrong_grammar rule)
- tests/test_text_public_leakage.py    — 8 tests (lexical scan + LeakageAuditor)
- tests/test_text_policy_mixture.py    — 8 tests (per-policy label distribution, oversampling)
- tests/test_text_data_collection.py   — 8 tests (schema validation, JSONL roundtrip, manifest)
- tests/test_text_replay.py            — 6 tests (deterministic replay, mismatch detection)

### New scripts/configs
- scripts/01_generate_text_data.py     — driver: collect → coverage audit → leakage audit → replay → manifest
- configs/data_collection_text.yaml    — P2 config (seed=73211, 200 episodes, 8 families, 5 policies)

### Updated files
- src/frcgw/text_env/__init__.py       — re-export public API
- src/frcgw/data/__init__.py           — export CoverageAuditor, ShardExporter
- plans/PHASE_PROGRESS.md             — P1.5 → PASS, P2 → PASS
- .gitignore                           — phase gate sentinel negation rules
- outputs/phase_gates/P1.passed        — sentinel created
- outputs/phase_gates/P1.5.passed      — sentinel created
- outputs/phase_gates/P2.passed        — sentinel created

### DO NOT MODIFY (unchanged, verified)
- paper_context_ref/** — 0 modifications
- src/frcgw/schemas/*.py — 0 modifications
- src/frcgw/data/leakage_auditor.py — 0 modifications
- .claude/{skills,agents,hooks,commands}/** — 0 modifications

## Tests/Gates

### pytest -q
- P0+P1 baseline: 53 passed (no regression)
- P2 신규: 48 passed
- **Total: 101 passed, 0 failed**

### Coverage report (data/frcgw_text/v0_1/audits/coverage_report.json)
| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| failed_action_ratio | ≥ 20% | **38.9%** | PASS |
| recovery_ratio | ≥ 8% | **23.9%** | PASS |
| repeated_wrong_mapping_ratio | ≥ 8% | **22.1%** | PASS |
| shift_ratio | ≥ 8% | **10.0%** | PASS |
| reveal_ratio | ≥ 5% | **6.4%** | PASS |
| delayed/noisy/no_op_valid_ratio | ≥ 3% | **10.1%** | PASS |

### Leakage report
- forbidden field hits in PublicObservation: **0**
- counterfactual hits in inference path: **0**
- LeakageAuditor.audit_batch PASS on all shards: **YES**

### Replay report
- episodes checked: 5 (sample)
- byte-identical on re-collection: **5/5 PASS**

## Subagent verdicts
- frcgw-data-leakage-auditor: **PASS** — all forbidden fields confined to label/audit buckets; double-layer enforcement (assert_agent_observation_safe + audit_agent_input in exporter)
- frcgw-test-runner: **PASS, Gate ready: YES** — 101 passed
- frcgw-code-reviewer: **ACCEPT** — no term drift, no baseline/ablation drift, no visibility flattening, all 9 modules have source MD docstring
- frcgw-experiment-design: **PASS** — CLAIM-EVAL-P2-01 claim-to-evidence table written; must-not-disappear 0 누락; ablation_core.yaml 12개 ablation 전부 보존

## P2 Gate Conditions (P2-G-01 ~ P2-G-17)
| ID | Condition | Status |
|----|-----------|--------|
| P2-G-01 | pytest -q ALL pass (≥70 expected) | PASS — 101 |
| P2-G-02 | P1 tests no regression | PASS — 53 baseline intact |
| P2-G-03 | P2 신규 test 5종 pass | PASS — 48 tests |
| P2-G-04 | dry-run 100~500 episodes | PASS — 200 episodes |
| P2-G-05 | hidden grammar/regime 0 leakage | PASS — 0 hits |
| P2-G-06 | LeakageAuditor.audit_batch PASS | PASS |
| P2-G-07 | failed_action_ratio ≥ 20% | PASS — 38.9% |
| P2-G-08 | recovery_ratio ≥ 8% | PASS — 23.9% |
| P2-G-09 | repeated_wrong_mapping_ratio ≥ 8% | PASS — 22.1% |
| P2-G-10 | shift_ratio ≥ 8% | PASS — 10.0% |
| P2-G-11 | delayed/no_op_valid count ≥ 1 per family | PASS — 10.1% across families |
| P2-G-12 | paper_context_ref/ 수정 없음 | PASS |
| P2-G-13 | P1 schema / P1.5 harness 수정 없음 | PASS — code reviewer ACCEPT |
| P2-G-14 | frcgw-data-leakage-auditor PASS | PASS |
| P2-G-15 | frcgw-test-runner PASS, Gate ready YES | PASS |
| P2-G-16 | frcgw-code-reviewer ACCEPT | ACCEPT |
| P2-G-17 | frcgw-experiment-design claim-to-evidence 표 | PASS |

## Blockers
- none

## Dry-run dataset location
- data/frcgw_text/v0_1/manifest.json
- data/frcgw_text/v0_1/{train,valid,test_id}.jsonl
- data/frcgw_text/v0_1/audits/coverage_report.json
- data/frcgw_text/v0_1/audits/leakage_report.json
- data/frcgw_text/v0_1/audits/replay_report.json

## Next phase
P3 — text-only model and ablations (requires explicit user approval)
