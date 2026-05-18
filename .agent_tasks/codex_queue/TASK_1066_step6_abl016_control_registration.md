TASK_NAME: step6_abl016_control_registration

BACKGROUND:
STEP 5 checkpoint (outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt) was trained with
l_falsification=0.0. This is the deliberate training-time no-falsification ablation.

Per SSoT paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8, this corresponds to
ABL-016 (tdd_ref="ABL-016", id="no_falsification"). The plan name "ABL-010" used in some
session documents is a naming error — ABL-016 is the correct SSoT identifier.

STEP 6 goal: register the STEP 5 checkpoint as ABL-016 control evidence in the codebase,
so the experimental comparison (ABL-016 vs falsification-enabled) is formally tracked.

GOAL:
1. Add control_evidence_ref optional field to AblationConfig dataclass.
2. Update the "no_falsification" entry in ABLATION_REGISTRY to include control_evidence_ref and training context metadata.
3. Update ablation_core.yaml ABL-016 entry with control_checkpoint_ref, training_l_falsification, and step references.
4. Create step6 ABL-016 control registration document.
5. Write tests verifying registration integrity.

FILES_ALLOWED:
- src/frcgw/evaluation/ablations.py (AblationConfig dataclass + no_falsification registry entry only)
- configs/ablation_core.yaml (ABL-016 entry metadata only)
- docs/orchestration/lr_alignment/29_step6_abl016_control_registration.md (new file)
- tests/test_step6_abl016_control_registration.py (new file)

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/visibility.py
- .claude/**
- scripts/run_codex_task.ps1
- outputs/checkpoints/pretrain_v0_3/** (IMMUTABLE — never modify, never delete)
- outputs/runs/p3_lr_real_eval_step5_* (IMMUTABLE)

REQUIRED_IMPLEMENTATION:

## 1. src/frcgw/evaluation/ablations.py — AblationConfig dataclass

Add optional field to AblationConfig:
```python
@dataclass
class AblationConfig:
    ablation_id: str
    tdd_ref: str
    severity: str
    description: str
    expected_collapse: dict[str, str]
    masking: dict[str, Any]
    control_evidence_ref: str | None = None  # path to checkpoint used as control evidence
```

Do NOT change any other AblationConfig fields or any ablation wrapper class behavior.

## 2. src/frcgw/evaluation/ablations.py — ABLATION_REGISTRY no_falsification entry

Update the "no_falsification" entry to include control_evidence_ref:
```python
"no_falsification": AblationConfig(
    ablation_id="no_falsification",
    tdd_ref="ABL-016",
    severity="CRITICAL",
    description="Remove falsification scoring; agent never detects wrong hypothesis",
    expected_collapse={
        "falsification_precision_recall_f1": "decrease",
        "false_planning_call_rate": "increase",
    },
    masking={"disable_falsification": True},
    control_evidence_ref="outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt",
),
```

## 3. configs/ablation_core.yaml — ABL-016 entry

In the no_falsification entry, add metadata fields after the existing fields:
```yaml
  - id: no_falsification
    tdd_ref: ABL-016
    severity: CRITICAL
    description: "Remove falsification scoring; agent never detects wrong hypothesis"
    expected_collapse:
      falsification_precision_recall_f1: decrease
      false_planning_call_rate: increase
    # STEP 6 ABL-016 control evidence
    paper_ssot_id: ABL-016
    control_checkpoint_ref: "outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt"
    training_l_falsification: 0.0
    control_eval_run_ref: "outputs/runs/p3_lr_real_eval_step5_trained_smoke"
    step6_experimental_group_ckpt: "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt"
    note: "STEP 5 checkpoint is training-time ABL-016 control (l_falsification=0.0). STEP 6 experimental group uses l_falsification=1.0."
```

## 4. docs/orchestration/lr_alignment/29_step6_abl016_control_registration.md

Create this document with the following sections:
- Title: STEP 6 ABL-016 Control Registration
- Date: 2026-05-18
- Status: REGISTERED
- Section 1: What ABL-016 Is
  - STEP 5 checkpoint = training-time L_falsification removed (weight=0.0)
  - This is the deliberate no-falsification control condition per paper §8
  - control_checkpoint: outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt
  - control_eval_run: outputs/runs/p3_lr_real_eval_step5_trained_smoke/ (preserved)
  - This is NOT a failure of FRCG-LR; it is the deliberate control condition
- Section 2: Naming Correction
  - Prior session documents used "ABL-010" — this is an error
  - SSoT paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8 + ablations.py define ABL-016 (no_falsification)
  - ABL-010 does not exist in the SSoT registry
- Section 3: Experimental Comparison
  - Control (ABL-016): STEP 5 checkpoint, l_falsification=0.0
  - Experimental: STEP 6 checkpoint (pretrain_v0_3_falsification), l_falsification=1.0
  - Comparison metrics: C3 (falsification F1), C4 (rollout fidelity), C1 (persistence)
- Section 4: Immutability Guarantee
  - outputs/checkpoints/pretrain_v0_3/** must never be modified or deleted
  - outputs/runs/p3_lr_real_eval_step5_* must never be overwritten
  - Claim wording maximum: PRELIMINARY (not resolved/proven/outperforms)

REQUIRED_TESTS:

### tests/test_step6_abl016_control_registration.py

1. test_abl016_control_evidence_ref_registered(): import ABLATION_REGISTRY, assert ABLATION_REGISTRY["no_falsification"].control_evidence_ref == "outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt"
2. test_abl016_tdd_ref_is_ABL016(): assert ABLATION_REGISTRY["no_falsification"].tdd_ref == "ABL-016"
3. test_abl016_dispatch_behavior_unchanged(): instantiate NoFalsificationAblation (via get_ablation_agent("no_falsification", base_agent)), verify act() still returns (action, ComputeBudgetLog) with planning_calls=0 (behavior unaffected by metadata addition)
4. test_ablation_config_control_evidence_ref_optional(): create AblationConfig(ablation_id="test", tdd_ref="T", severity="s", description="d", expected_collapse={}, masking={}) — omitting control_evidence_ref — verify it succeeds (field is optional)

ACCEPTANCE_CRITERIA:
- 4 tests PASS
- git diff --stat outputs/ = empty (Codex must not write to outputs/)
- STEP 5 checkpoint file exists and is unchanged (test reads only its path, does not modify)
- NoFalsificationAblation wrapper behavior unchanged
- ablation_core.yaml only has metadata additions to ABL-016 entry (no other entry changed)

COMMIT_MESSAGE:
feat(step6/task2): register STEP5 ckpt as ABL-016 control + add control_evidence_ref metadata

STOP_CONDITION:
Stop if: (1) any FORBIDDEN file is modified; (2) outputs/checkpoints/pretrain_v0_3/** is accessed for write; (3) NoFalsificationAblation.act() behavior is changed (only metadata/docstring changes allowed); (4) AblationConfig existing fields are renamed or removed.
