# FRCG-WM

**FRCG-WM: falsification-guided control-grammar world model for Web/GUI agents (research scaffold P0).**

This is not a generic Web/GUI world model.
The target is falsification-guided planning:
action-effect evidence → current hypothesis falsification → alternative control-grammar hypothesis → short rollout → decision-relevant compute gate → action-interface rewrite.

---

## First Rule

> **Read `paper_context_ref/00_CONTEXT_INDEX.md` before any task.**

Then read only the specific MD files routed by that index.

---

## Required Execution Order

```
1. docs/scaffold
2. schema and visibility tests
3. text-only data
4. text-only model and ablations
5. synthetic GUI MVE data
6. frozen VLM MVE
7. compute-matched baselines and ablations
8. paper-main planning only after gates pass
```

Do not jump to the impressive part.

---

## Forbidden Assumptions

- **hidden label leakage**: `true_regime`, `true_control_grammar`, `true_change_point`, etc. are never inference inputs.
- **success-rate-only evaluation**: mechanism metrics (persistence, recovery delay, falsification PR) are required.
- **generic Web/GUI world model novelty**: this paper targets wrong-control-grammar persistence, not generic WM.
- **7B-first training**: text-only and MVE gates must pass before paper-main VLM training.
- **fake empirical results**: all reported numbers must come from real run artifacts.

---

## Install

```bash
pip install -e ".[dev]"
pytest -q
```

---

## Context Router

| File | Role |
|---|---|
| `paper_context_ref/00_CONTEXT_INDEX.md` | **Start here** — routes to correct docs |
| `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` | Phase order, gates, commands |
| `paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md` | MUST/SHOULD requirements |
| `paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md` | Module design and interfaces |
| `docs/README.md` | Operational docs router |

---

## License / Citation

TBD
