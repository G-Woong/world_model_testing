---
file_id: STEP-15
title: Technical Design Document for FRCG-WM
version: v1.0
status: technical_design_contract_not_final_code
language: ko
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
  - 11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
  - 12_DATA_COLLECTION_METHODOLOGY.md
  - 13_CLAUDE_CODE_EXECUTION_ROADMAP.md
  - 14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
  - FINAL_RESEARCH_BLUEPRINT.md
purpose:
  - TRD의 MUST/SHOULD/MUST NOT 요구사항을 실제 구현 가능한 기술 설계로 변환한다.
  - Claude Code가 repo scaffold, schema, generator, collector, model, loss, planner, evaluator, baseline, ablation, report를 구현할 때 따라야 할 module interface와 data flow를 정의한다.
  - class/function/config/test/run artifact 단위로 구현 계약을 고정한다.
  - hidden-label leakage, weak baseline, compute mismatch, fake result, premature scaling을 구조적으로 방지한다.
forbidden:
  - Do not write production code inside this document.
  - Do not weaken any MUST/MUST NOT requirement from 14_TRD.
  - Do not expose hidden labels or counterfactual labels to inference input.
  - Do not remove critical baselines or ablations.
  - Do not start implementation from paper-main 7B VLM.
  - Do not fabricate empirical results or example metrics.
  - Do not make API signatures depend on private/global state.
next_files:
  - 16_REPO_SCAFFOLD_AND_TEST_PLAN.md
  - 17_IMPLEMENTATION_TASK_BREAKDOWN.md
  - 18_CONFIG_SCHEMA_AND_RUNBOOK.md
---

# 15_TDD_TECHNICAL_DESIGN_DOCUMENT.md

## 1. File Purpose

이 문서는 FRCG-WM 연구 시스템의 **Technical Design Document(TDD)**다.  
`14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md`가 “무엇을 만족해야 하는가”를 정의했다면, 이 문서는 “그 요구사항을 어떤 모듈·클래스·함수·config·데이터 흐름·테스트로 구현할 것인가”를 정의한다.

이 문서는 실제 코드를 쓰는 파일이 아니다.  
하지만 Claude Code가 구현할 때 ambiguity 없이 따라갈 수 있도록 interface 수준까지 고정한다.

핵심 목표:

1. `schema → data generation → validation → text model → GUI MVE → frozen VLM MVE → baselines/ablations → reports`의 구현 흐름을 고정한다.
2. 각 module의 책임, input/output, forbidden input, side effect, test를 정의한다.
3. hidden labels와 counterfactual labels가 inference path에 들어가는 것을 구조적으로 차단한다.
4. baselines/ablations/evaluation을 나중에 “시간 없어서 생략”하지 못하도록 설계한다.
5. 모든 run이 config/manifest/hash/status로 재현 가능하게 만든다.

---

## 2. Design Principles

| Principle ID | Principle | Implementation Consequence |
|---|---|---|
| TDD-PRINCIPLE-001 | visibility separation by design | schema object에서 public/private/counterfactual/audit field를 분리한다. |
| TDD-PRINCIPLE-002 | MVE first | text-only와 GUI-MVE가 paper-main보다 먼저 구현된다. |
| TDD-PRINCIPLE-003 | test before scale | schema/leakage/replay/coverage tests 통과 전 학습 금지. |
| TDD-PRINCIPLE-004 | frozen backbone first | VLM full fine-tuning을 기본 경로로 두지 않는다. |
| TDD-PRINCIPLE-005 | claim-to-metric traceability | model/eval output은 claim ID와 metric ID를 연결한다. |
| TDD-PRINCIPLE-006 | baseline parity | proposed method와 baselines는 같은 split/base/compute budget을 공유한다. |
| TDD-PRINCIPLE-007 | no fake result | report generator는 run log와 metric artifact만 읽는다. |
| TDD-PRINCIPLE-008 | deterministic replay | synthetic env transition은 가능한 한 replay 가능해야 한다. |
| TDD-PRINCIPLE-009 | fail closed | validation이 불확실하면 pass가 아니라 fail/block 처리한다. |
| TDD-PRINCIPLE-010 | scientific definitions are config/doc controlled | regime/control grammar/falsification 정의는 코드에 숨기지 않는다. |

---

## 3. Target Repository Architecture

```text
frcgw/
  README.md
  pyproject.toml
  configs/
  docs/
  src/
    frcgw/
      schemas/
      text_env/
      gui_env/
      logging/
      data/
      models/
      objectives/
      planning/
      training/
      evaluation/
      reporting/
      utils/
  scripts/
  tests/
  data/
  outputs/
```

Implementation rule:

```text
Every executable script must call:
1. config loader,
2. seed setter,
3. manifest writer,
4. validation guard where applicable.
```

---

## 4. Package-Level Module Map

| Package | Responsibility | Depends On | Must Not Depend On |
|---|---|---|---|
| `schemas` | data objects, visibility, validation | none except utils | model/training/eval |
| `text_env` | symbolic environment and collector | schemas, data, logging | VLM/model training |
| `gui_env` | synthetic browser-like environment | schemas, logging, utils | model internals |
| `logging` | action-effect, counterfactual, replay, manifest | schemas, utils | training |
| `data` | split/export/load/audit/coverage | schemas, logging, utils | model-specific code except collator |
| `models` | encoders, latent heads, world model heads | schemas only for field names | evaluator reports |
| `objectives` | losses/rewards/weighting | models, schemas | data generation |
| `planning` | falsification, alternative, rollout, gate, rewrite | models/objectives outputs | hidden labels as inference input |
| `training` | train loops, checkpoints, monitoring | data, models, objectives, planning | report fabrication |
| `evaluation` | metrics, baselines, ablations, compute matching | data, models, planning | training-only labels as inputs |
| `reporting` | markdown/csv/figures from logs | evaluation outputs | raw fake numbers |
| `utils` | seed/hash/io/config | none | scientific logic |

---

## 5. Core Data Types

### 5.1 VisibilityBucket

```python
class VisibilityBucket(str, Enum):
    AGENT_OBSERVATION = "AGENT_OBSERVATION"
    TRAINING_SUPERVISION = "TRAINING_SUPERVISION"
    EVALUATION_ONLY = "EVALUATION_ONLY"
    COUNTERFACTUAL_ONLY = "COUNTERFACTUAL_ONLY"
    AUDIT_METADATA = "AUDIT_METADATA"
```

Design requirement:

- `AGENT_OBSERVATION`만 inference input으로 허용된다.
- 나머지 bucket은 target/eval/audit로만 사용된다.

### 5.2 EpisodeRecord

```python
@dataclass
class EpisodeRecord:
    episode_id: str
    dataset_version: str
    schema_version: str
    generator_version: str
    split_id: str
    task_family: str
    public_instruction: str
    steps: list[StepRecord]
    final_success: bool
    total_progress: float
    audit_metadata: AuditMetadata
```

Forbidden:

- `task_family`, `split_id`, `template_id`, `seed`는 model input으로 들어가면 안 된다.

### 5.3 StepRecord

```python
@dataclass
class StepRecord:
    step_id: str
    episode_id: str
    step_index: int
    public_observation: PublicObservation
    action: ActionRecord
    observed_effect_public: PublicEffect
    training_labels: TrainingLabels
    evaluation_labels: EvaluationLabels
    counterfactuals: list[CounterfactualRecord]
    audit_metadata: StepAuditMetadata
```

### 5.4 PublicObservation

```python
@dataclass
class PublicObservation:
    instruction: str
    dom_snapshot_public: dict | None
    accessibility_tree_public: dict | None
    screenshot_ref: str | None
    history_public: list[PublicHistoryItem]
    candidate_actions_public: list[CandidateAction]
```

Must not include:

```python
FORBIDDEN_AGENT_FIELDS = {
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_reveal_vs_shift",
    "true_wrong_hypothesis",
    "counterfactual_action_effects",
    "oracle_regime_action",
    "oracle_grammar_action",
    "split_id",
    "ood_type",
    "template_id",
    "seed",
    "policy_id",
}
```

### 5.5 TrainingLabels

```python
@dataclass
class TrainingLabels:
    true_regime: str
    true_control_grammar: str
    true_change_point: str
    true_reveal_vs_shift: str
    true_action_effect_type: str
    true_failed_action: bool
    failure_reason: str | None
    progress_delta: float
    recovery_action_id: str | None
    valid_hypothesis_switch: bool | None
```

### 5.6 EvaluationLabels

```python
@dataclass
class EvaluationLabels:
    true_wrong_hypothesis: bool | None
    h_exec_id: str | None
    correct_hypothesis_id: str | None
    evidence_timestamp: int | None
    hypothesis_update_timestamp: int | None
    recovery_timestamp: int | None
    ood_type: str | None
```

### 5.7 CounterfactualRecord

```python
@dataclass
class CounterfactualRecord:
    counterfactual_id: str
    source_step_id: str
    candidate_action: CandidateAction
    hypothesis_id: str
    counterfactual_effect_type: str
    counterfactual_progress_delta: float
    counterfactual_failure_risk: float
    is_oracle_best: bool
```

Hard rule:

```text
CounterfactualRecord is never returned by dataloader input collator.
```

---

## 6. Schema and Validation Design

### 6.1 `schemas/visibility.py`

Required API:

```python
def assert_agent_observation_safe(obj: Any) -> None:
    """Raise HiddenLabelLeakageError if forbidden fields are present."""

def strip_to_agent_observation(step: StepRecord) -> PublicObservation:
    """Return only AGENT_OBSERVATION bucket."""

def get_forbidden_agent_fields() -> set[str]:
    """Return forbidden field names."""
```

### 6.2 `schemas/validation.py`

Required API:

```python
def validate_step_schema(step: StepRecord) -> ValidationResult:
    ...

def validate_episode_schema(episode: EpisodeRecord) -> ValidationResult:
    ...

def validate_visibility_contract(episode: EpisodeRecord) -> ValidationResult:
    ...

def validate_counterfactual_exclusion(batch: dict) -> ValidationResult:
    ...
```

### 6.3 Error Types

```python
class HiddenLabelLeakageError(RuntimeError): ...
class CounterfactualLeakageError(RuntimeError): ...
class SchemaValidationError(RuntimeError): ...
class ReplayValidationError(RuntimeError): ...
class CoverageValidationError(RuntimeError): ...
class SplitIntegrityError(RuntimeError): ...
```

### 6.4 Required Tests

| Test File | Test Case |
|---|---|
| `test_visibility_contract.py` | injecting `true_control_grammar` into public observation raises |
| `test_counterfactual_exclusion.py` | dataloader input excludes counterfactuals |
| `test_episode_schema.py` | missing required labels fail validation |
| `test_schema_roundtrip.py` | JSONL serialize/deserialize preserves bucket separation |

---

## 7. Text-Only Environment Design

### 7.1 `text_env/state.py`

```python
@dataclass
class TextState:
    visible_text: str
    public_actions: list[str]
    hidden_regime: str
    hidden_control_grammar: str
    progress: float
    blocker_state: str | None
```

### 7.2 `text_env/grammar.py`

```python
class TextControlGrammar:
    grammar_id: str

    def precondition_satisfied(self, state: TextState, action: str) -> bool:
        ...

    def expected_effect(self, state: TextState, action: str) -> str:
        ...

    def apply(self, state: TextState, action: str) -> TextState:
        ...
```

### 7.3 `text_env/generator.py`

```python
class TextTaskGenerator:
    def generate_episode_spec(self, seed: int) -> TextEpisodeSpec:
        ...

    def generate_initial_state(self, spec: TextEpisodeSpec) -> TextState:
        ...
```

### 7.4 `text_env/policies.py`

Required policies:

```python
class OraclePolicy: ...
class WrongGrammarPolicy: ...
class RetryPolicy: ...
class RandomConstrainedPolicy: ...
class RecoveryPolicy: ...
class PolicyMixtureRunner: ...
```

### 7.5 `text_env/collector.py`

```python
class TextTrajectoryCollector:
    def collect_episode(self, spec: TextEpisodeSpec, policy: Policy) -> EpisodeRecord:
        ...

    def collect_dataset(self, n_episodes: int, output_path: Path) -> DatasetManifest:
        ...
```

### 7.6 Acceptance Tests

| Test | Required Result |
|---|---|
| deterministic transition | same seed produces same episode |
| wrong-grammar policy | produces repeated wrong mapping cases |
| recovery policy | produces valid recovery cases |
| lexical leakage audit | hidden grammar not in visible text |
| coverage | required ratios pass |

---

## 8. Synthetic Web/GUI Environment Design

### 8.1 `gui_env/task_spec.py`

```python
@dataclass
class TaskSpec:
    task_id: str
    task_family: str
    public_instruction: str
    subgoals: list[SubgoalSpec]
    allowed_regimes: list[str]
    allowed_grammars: list[str]
```

### 8.2 `gui_env/template_generator.py`

```python
class UITemplateGenerator:
    def sample_template(self, task_spec: TaskSpec, split_id: str, seed: int) -> UITemplate:
        ...

    def render(self, template: UITemplate, hidden_state: HiddenGUIState) -> RenderedUI:
        ...
```

RenderedUI must include:

- DOM tree,
- accessibility tree,
- screenshot reference,
- element map,
- public candidate action references.

### 8.3 `gui_env/regime_grammar_engine.py`

```python
class RegimeGrammarEngine:
    def assign_initial(self, task_spec: TaskSpec, seed: int) -> RegimeGrammarState:
        ...

    def get_preconditions(self, grammar_id: str, action: CandidateAction) -> list[str]:
        ...

    def expected_effect(self, state: HiddenGUIState, action: CandidateAction) -> ExpectedEffect:
        ...

    def apply_action(self, state: HiddenGUIState, action: CandidateAction) -> HiddenGUIState:
        ...
```

### 8.4 `gui_env/event_scheduler.py`

```python
class EventScheduler:
    def maybe_apply_event(self, state: HiddenGUIState, step_index: int) -> EventRecord:
        ...

    def label_event(self, before: HiddenGUIState, after: HiddenGUIState) -> str:
        ...
```

Event labels:

- none
- reveal
- shift
- delayed
- noisy
- stale
- failure

### 8.5 `gui_env/browser_executor.py`

```python
class BrowserExecutor:
    def snapshot(self) -> BrowserSnapshot:
        ...

    def execute(self, action: CandidateAction) -> ExecutionResult:
        ...

    def replay(self, episode: EpisodeRecord) -> ReplayResult:
        ...
```

This can be Playwright-backed or synthetic-renderer-backed. TDD does not mandate a specific implementation, but TRD requires deterministic replay.

### 8.6 `gui_env/action_space.py`

```python
class ActionSpaceBuilder:
    def build_public_actions(self, rendered_ui: RenderedUI) -> list[CandidateAction]:
        ...

    def validate_action(self, action: CandidateAction, rendered_ui: RenderedUI) -> bool:
        ...
```

### 8.7 Acceptance Tests

| Test | Required Result |
|---|---|
| render determinism | same seed/template/state gives same public obs |
| action precondition | unmet precondition causes labeled failure |
| reveal/shift event | event labels match hidden transition |
| public action space | no oracle-only action exposed |
| replay | replayed actual effects match stored effect |

---

## 9. Logging and Counterfactual Design

### 9.1 `logging/action_effect_logger.py`

```python
class ActionEffectLogger:
    def compute_effect(
        self,
        pre: BrowserSnapshot | TextState,
        post: BrowserSnapshot | TextState,
        action: CandidateAction,
    ) -> ActionEffectRecord:
        ...
```

Required output fields:

- effect_type,
- dom_diff_summary,
- a11y_diff_summary,
- screenshot_diff_ref,
- progress_delta,
- failed_action,
- failure_reason,
- delayed_effect_flag.

### 9.2 `logging/counterfactual_logger.py`

```python
class CounterfactualSimulator:
    def generate(
        self,
        env: Environment,
        pre_state: HiddenGUIState | TextState,
        candidate_actions: list[CandidateAction],
        hypotheses: list[str],
        top_k: int,
    ) -> list[CounterfactualRecord]:
        ...
```

### 9.3 `logging/replay_validator.py`

```python
class ReplayValidator:
    def validate_episode(self, episode: EpisodeRecord) -> ReplayResult:
        ...
```

### 9.4 `logging/manifest.py`

```python
class ManifestWriter:
    def write_dataset_manifest(self, manifest: DatasetManifest) -> None:
        ...

    def write_run_manifest(self, manifest: RunManifest) -> None:
        ...
```

### 9.5 Acceptance Tests

| Test | Required Result |
|---|---|
| effect diff | known transition yields known effect label |
| counterfactual exclusion | CF not passed to agent input |
| replay mismatch | invalid episode rejected |
| manifest hash | config/schema/dataset hash written |

---

## 10. Data Pipeline Design

### 10.1 `data/split_manager.py`

```python
class SplitManager:
    def assign(self, spec: TaskSpec | TextEpisodeSpec) -> str:
        ...

    def validate_split_integrity(self, manifest: DatasetManifest) -> SplitIntegrityReport:
        ...
```

### 10.2 `data/shard_exporter.py`

```python
class ShardExporter:
    def write_episode(self, split_id: str, episode: EpisodeRecord) -> None:
        ...

    def write_rejected(self, episode: EpisodeRecord, reason: str) -> None:
        ...

    def finalize(self) -> DatasetManifest:
        ...
```

### 10.3 `data/leakage_auditor.py`

```python
class LeakageAuditor:
    def audit_episode(self, episode: EpisodeRecord) -> LeakageReport:
        ...

    def audit_dataset(self, root: Path) -> LeakageReport:
        ...
```

### 10.4 `data/coverage_auditor.py`

```python
class CoverageAuditor:
    def audit_dataset(self, root: Path, targets: CoverageTargets) -> CoverageReport:
        ...
```

### 10.5 `data/dataset_loader.py`

```python
class FRCGDataset(Dataset):
    def __getitem__(self, idx: int) -> StepExample:
        ...

class FRCGCollator:
    def __call__(self, examples: list[StepExample]) -> dict[str, Tensor | list]:
        ...
```

Collator hard requirement:

```text
Input batch keys must be logged.
Forbidden fields must be absent.
Counterfactuals must be returned only if training config explicitly requests counterfactual targets, never as inference input.
```

---

## 11. Model Architecture Design

### 11.1 `models/encoders.py`

```python
class DOMEncoder(nn.Module):
    def forward(self, dom_features: DOMBatch) -> Tensor:
        ...

class AccessibilityEncoder(nn.Module):
    def forward(self, a11y_features: A11yBatch) -> Tensor:
        ...

class ScreenshotFeatureEncoder(nn.Module):
    def forward(self, screenshot_inputs: ScreenshotBatch) -> Tensor:
        ...

class ActionEffectEncoder(nn.Module):
    def forward(self, action_effect_features: ActionEffectBatch) -> Tensor:
        ...

class HistoryEncoder(nn.Module):
    def forward(self, sequence_embeddings: Tensor, mask: Tensor) -> Tensor:
        ...
```

### 11.2 `models/vlm_frcg_adapter.py`

```python
class FrozenVLMAdapter(nn.Module):
    def __init__(self, model_name: str, freeze: bool = True):
        ...

    def encode(self, images: Any, text: Any) -> Tensor:
        ...

    def assert_frozen(self) -> None:
        ...
```

Requirement:

- default `freeze=True`.
- full fine-tuning config must be blocked unless explicitly allowed and previous gates pass.

### 11.3 `models/latent_heads.py`

```python
class LatentPosteriorHead(nn.Module):
    def forward(self, h: Tensor) -> LatentPosterior:
        ...

@dataclass
class LatentPosterior:
    z_state: Tensor
    z_regime_logits: Tensor
    z_control_grammar_logits: Tensor
    z_change_point_logits: Tensor
    auxiliary: dict[str, Tensor]
```

### 11.4 `models/world_model_heads.py`

```python
class ActionEffectHead(nn.Module): ...
class ProgressHead(nn.Module): ...
class FalsificationHead(nn.Module): ...
class AlternativeScoringHead(nn.Module): ...
class ShortRolloutHead(nn.Module): ...
class RewriteHead(nn.Module): ...
```

### 11.5 `models/text_frcg_model.py`

```python
class TextFRCGModel(nn.Module):
    def forward(self, batch: dict) -> FRCGModelOutput:
        ...
```

### 11.6 `models/vlm_frcg_model.py`

```python
class VLMFRCGModel(nn.Module):
    def forward(self, batch: dict) -> FRCGModelOutput:
        ...
```

### 11.7 Output Contract

```python
@dataclass
class FRCGModelOutput:
    latent_posterior: LatentPosterior
    action_effect_logits: Tensor
    progress_pred: Tensor
    falsification_score: Tensor
    alternative_scores: Tensor | None
    rollout_pred: dict[str, Tensor] | None
    rewrite_logits: Tensor | None
    diagnostics: dict[str, Any]
```

---

## 12. Objective Design

### 12.1 `objectives/losses.py`

Required functions/classes:

```python
def loss_action_effect(pred: Tensor, target: Tensor, mask: Tensor | None = None) -> Tensor:
    ...

def loss_progress(pred: Tensor, target: Tensor) -> Tensor:
    ...

def loss_regime(logits: Tensor, target: Tensor) -> Tensor:
    ...

def loss_control_grammar(logits: Tensor, target: Tensor) -> Tensor:
    ...

def loss_change_point(logits: Tensor, target: Tensor) -> Tensor:
    ...

def loss_falsification(score: Tensor, target: Tensor, mode: str = "bce_or_pairwise") -> Tensor:
    ...

def loss_intent_action_mapping(logits: Tensor, target: Tensor) -> Tensor:
    ...

def loss_counterfactual_rollout(pred: Tensor, target: Tensor) -> Tensor:
    ...
```

### 12.2 `objectives/rewards.py`

```python
@dataclass
class RewardComponents:
    progress_reward: float
    failed_action_penalty: float
    repeated_failure_penalty: float
    recovery_reward: float
    valid_switch_reward: float
    invalid_switch_penalty: float
    compute_cost_penalty: float

def compute_valid_switch_reward(ctx: SwitchRewardContext) -> float:
    ...
```

Valid switch reward must check:

1. current hypothesis was wrong,
2. alternative explains evidence better,
3. selected action changed,
4. progress or reduced failure followed.

### 12.3 `objectives/weighting.py`

```python
class LossWeightScheduler:
    def weights_for_stage(self, stage_id: str, step: int) -> dict[str, float]:
        ...
```

---

## 13. Planning Design

### 13.1 `planning/falsification.py`

```python
class FalsificationScorer:
    def score(self, current_hypothesis: Hypothesis, evidence: Evidence, alternatives: list[Hypothesis]) -> FalsificationResult:
        ...
```

```python
@dataclass
class FalsificationResult:
    score: float
    current_likelihood: float
    best_alt_likelihood: float
    best_alt_id: str | None
    calibrated_confidence: float | None
```

### 13.2 `planning/alternative_proposer.py`

```python
class AlternativeHypothesisProposer:
    def propose(self, posterior: LatentPosterior, evidence: Evidence, k: int) -> list[Hypothesis]:
        ...
```

### 13.3 `planning/rollout.py`

```python
class ShortRolloutModel:
    def rollout(self, hypothesis: Hypothesis, candidate_actions: list[CandidateAction], horizon: int) -> list[RolloutPrediction]:
        ...
```

### 13.4 `planning/decision_gate.py`

```python
class DecisionRelevanceGate:
    def decide(self, falsification: FalsificationResult, rollout_set: list[RolloutPrediction], compute_cost: float) -> GateDecision:
        ...
```

Gate rule must support:

```text
F_t > tau_f AND ΔV_t > tau_v AND P(action_switch) > tau_a
```

### 13.5 `planning/rewrite.py`

```python
class ActionRewriteModule:
    def rewrite(self, intent: str, selected_hypothesis: Hypothesis, candidate_actions: list[CandidateAction]) -> RewriteResult:
        ...
```

### 13.6 `planning/planner.py`

```python
class FRCGPlanner:
    def plan(self, public_observation: PublicObservation, history: list[PublicHistoryItem]) -> PlanResult:
        ...
```

Planner must return diagnostics:

- falsification score,
- selected hypothesis,
- alternatives,
- rollout summary,
- gate decision,
- final action,
- whether rewrite used,
- compute budget.

---

## 14. Training Design

### 14.1 `training/train_text.py`

Required stages:

1. load text dataset,
2. validate visibility,
3. train text FRCG model,
4. run validation metrics,
5. save checkpoint,
6. write run manifest.

### 14.2 `training/train_vlm_mve.py`

Required stages:

1. load dataset manifest,
2. validate leakage report exists and passed,
3. initialize frozen VLM adapter,
4. assert frozen parameters,
5. train FRCG heads,
6. log batch input keys,
7. compute losses,
8. run validation,
9. save checkpoint,
10. write manifest.

### 14.3 `training/monitoring.py`

```python
class TrainingMonitor:
    def log_losses(self, loss_dict: dict[str, float]) -> None:
        ...

    def log_batch_fields(self, batch: dict) -> None:
        ...

    def check_forbidden_fields(self, batch: dict) -> None:
        ...

    def write_run_status(self, status: str, reason: str | None = None) -> None:
        ...
```

Kill conditions:

- hidden field in batch,
- NaN loss,
- leakage report missing,
- dataset version mismatch,
- no validation split,
- checkpoint save failure.

---

## 15. Evaluation Design

### 15.1 `evaluation/metrics.py`

Required metrics:

```python
def task_success_rate(episodes: list[EpisodeRecord]) -> float: ...
def normalized_return(episodes: list[EpisodeRecord]) -> float: ...
def wrong_control_grammar_persistence(episodes: list[EpisodeRecord]) -> MetricResult: ...
def failed_action_repetition_rate(episodes: list[EpisodeRecord]) -> float: ...
def recovery_delay(episodes: list[EpisodeRecord]) -> MetricResult: ...
def falsification_precision_recall(preds, labels) -> dict: ...
def falsification_calibration(preds, labels) -> dict: ...
def alternative_rollout_fidelity(preds, counterfactuals) -> MetricResult: ...
def progress_per_compute(results) -> float: ...
def false_planning_call_rate(results) -> float: ...
```

### 15.2 `evaluation/baselines.py`

Required baselines:

```python
class FrozenBaseAgent: ...
class ReactiveAgent: ...
class RetryAfterFailureAgent: ...
class VerifierOnlyAgent: ...
class FailureDiagnosisOnlyAgent: ...
class NextStateWMOnlyAgent: ...
class AlwaysPlanAgent: ...
class UncertaintyGatedAgent: ...
class RandomAlternativePlanner: ...
class OracleRegimeAgent: ...
class OracleControlGrammarAgent: ...
```

### 15.3 `evaluation/ablations.py`

Required ablations:

```python
ABLATIONS = [
    "no_control_grammar",
    "merged_regime_control_grammar",
    "collapsed_latent",
    "no_falsification",
    "uncertainty_instead_of_falsification",
    "no_alternative_hypothesis",
    "random_alternative",
    "no_rollout",
    "no_rewrite",
    "always_plan_no_gate",
    "no_progress_reward",
    "no_compute_penalty",
]
```

### 15.4 `evaluation/compute_budget.py`

```python
@dataclass
class ComputeBudgetLog:
    planning_calls: int
    rollout_steps: int
    candidate_actions_scored: int
    top_k_alternatives: int
    wall_clock_seconds: float | None
```

### 15.5 `evaluation/eval_runner.py`

```python
class EvaluationRunner:
    def run(self, model_or_agent: AgentLike, dataset: EvalDataset, config: EvalConfig) -> EvalResult:
        ...
```

Eval runner must enforce:

- same split,
- same base model,
- same observation fields,
- same compute budget where matched,
- required baselines present.

---

## 16. Reporting Design

### 16.1 `reporting/markdown_report.py`

```python
class MarkdownReportWriter:
    def write_metric_summary(self, eval_results: list[EvalResult]) -> Path:
        ...

    def write_ablation_summary(self, ablation_results: list[AblationResult]) -> Path:
        ...

    def write_failure_interpretation(self, eval_results: list[EvalResult]) -> Path:
        ...
```

### 16.2 Required Report Sections

| Report | Required Sections |
|---|---|
| metric summary | run manifest, dataset version, model version, metrics |
| ablation summary | ablation name, expected failure, observed metric delta, interpretation |
| compute report | planning calls, rollout steps, wall-clock proxy |
| failure cases | selection rule, examples, qualitative trace |
| leakage report | pass/fail, forbidden fields, action taken |

### 16.3 Report Guard

Report generator must fail if:

- metric artifact is missing,
- run manifest is missing,
- baseline artifact is missing for claim report,
- numbers are manually provided outside artifact loader,
- negative ablation results are omitted.

---

## 17. Config Design

### 17.1 Base Config Schema

```yaml
run:
  run_id: null
  seed: 42
  phase: text_smoke
  output_dir: outputs/runs
  fail_on_validation_error: true

dataset:
  root: data/frcgw/v0_1
  split: train
  schema_version: v0.1
  require_leakage_audit_passed: true

model:
  type: text_frcg
  backbone: none
  freeze_backbone: true
  latent_structure: four_latent
  use_screenshot: false
  use_dom: true
  use_action_effect_log: true

training:
  batch_size: 32
  learning_rate: 0.0003
  max_steps: 10000
  gradient_clip_norm: 1.0
  losses:
    action_effect: 1.0
    progress: 1.0
    control_grammar: 1.0
    falsification: 1.0
    mapping: 1.0

planning:
  top_k_alternatives: 3
  rollout_horizon: 3
  tau_f: 0.5
  tau_v: 0.0
  tau_action_switch: 0.1
  compute_cost: 0.01

evaluation:
  metrics:
    - success_rate
    - wrong_control_grammar_persistence
    - recovery_delay
    - failed_action_repetition
    - falsification_pr
    - progress_per_compute
  baselines_required:
    - frozen_base
    - verifier_only
    - next_state_wm_only
    - uncertainty_gated
    - always_plan
  ablations_required:
    - no_control_grammar
    - no_falsification
```

### 17.2 Config Validation

```python
def validate_config(config: dict) -> ConfigValidationResult:
    ...
```

Validation must fail if:

- `phase=paper_main` and previous gate artifacts missing,
- hidden fields listed in input fields,
- required baselines disabled,
- `freeze_backbone=false` without explicit override,
- compute budget logging disabled.

---

## 18. Script Design

| Script | Purpose | Required Input | Required Output |
|---|---|---|---|
| `00_validate_docs.py` | docs presence and required headings | docs path | doc validation report |
| `01_generate_text_data.py` | text data collection | data_collection_text.yaml | dataset shard + manifest |
| `02_train_text_smoke.py` | text model training | train_text.yaml | checkpoint + run manifest |
| `03_eval_text_smoke.py` | text eval/baselines | eval_text.yaml | metric report |
| `04_generate_gui_mve_data.py` | GUI MVE collection | data_collection_gui_mve.yaml | dataset shards |
| `05_validate_dataset.py` | leakage/replay/coverage audit | dataset root | audit reports |
| `06_train_vlm_mve.py` | frozen VLM MVE training | train_vlm_mve.yaml | checkpoint + metrics |
| `07_eval_vlm_mve.py` | VLM MVE eval | eval_gui_mve.yaml | eval artifacts |
| `08_run_core_ablations.py` | critical ablations | ablation_core.yaml | ablation artifacts |
| `09_generate_reports.py` | markdown/csv reports | run/eval artifacts | reports |

---

## 19. Testing Design

### 19.1 Unit Tests

| Test File | Covers |
|---|---|
| `test_visibility_contract.py` | forbidden fields |
| `test_episode_schema.py` | episode/step schemas |
| `test_counterfactual_exclusion.py` | counterfactual not input |
| `test_text_env.py` | symbolic transitions |
| `test_gui_event_scheduler.py` | reveal/shift/delay labels |
| `test_action_effect_logger.py` | effect diff |
| `test_leakage_auditor.py` | leakage detection |
| `test_coverage_auditor.py` | coverage thresholds |
| `test_falsification.py` | falsification scoring |
| `test_decision_gate.py` | VOC gate |
| `test_rewrite.py` | valid/invalid rewrite |
| `test_metrics.py` | metric calculations |
| `test_eval_runner.py` | baseline and compute matching |
| `test_config_validation.py` | invalid configs blocked |

### 19.2 Integration Tests

| Test | Scenario |
|---|---|
| `test_text_end_to_end.py` | generate small text data → train tiny model → eval |
| `test_gui_collection_dry_run.py` | generate 5 GUI episodes → replay → audit |
| `test_vlm_mve_batch_safety.py` | collate VLM batch → verify no hidden fields |
| `test_eval_required_baselines.py` | eval runner fails if verifier-only missing |
| `test_report_no_fake_numbers.py` | report fails without metric artifact |

### 19.3 Acceptance Tests

| Phase | Acceptance Test |
|---|---|
| P1 schema | all hidden leakage tests pass |
| P2 text data | coverage report pass |
| P3 text model | no-control-grammar/no-falsification degrade |
| P4 GUI data | replay/leakage/coverage pass |
| P5 VLM MVE | batch safety + baseline eval pass |
| P6 evaluation | compute-matched report generated |

---

## 20. Run Artifact Design

Every run must produce:

```text
outputs/runs/{run_id}/
  config.yaml
  config_hash.txt
  run_manifest.json
  stdout.log
  stderr.log
  metrics.json
  checkpoints/
  reports/
```

### 20.1 RunManifest

```json
{
  "run_id": "string",
  "phase": "text_smoke | gui_mve | vlm_mve | eval | ablation",
  "status": "success | failed | blocked",
  "reason": null,
  "dataset_version": "v0.1",
  "schema_version": "v0.1",
  "model_version": "v0.1",
  "config_hash": "sha256",
  "seed": 42,
  "started_at": "timestamp",
  "finished_at": "timestamp",
  "gate_results": {}
}
```

---

## 21. Failure and Blocker Design

| Failure | Where Detected | Blocked Phase |
|---|---|---|
| hidden label in batch | collator/monitor | training/eval |
| leakage audit fail | dataset validation | all downstream |
| coverage audit fail | dataset validation | training |
| replay validation fail | data collection | dataset export |
| required baseline missing | eval runner | claim report |
| compute budget missing | eval runner | planning claim |
| no-control-grammar no effect | ablation | control grammar claim |
| verifier-only matches | eval | falsification novelty |
| uncertainty-gated matches | eval | decision gate claim |
| fake report input | reporting | report generation |

---

## 22. Traceability to TRD

| TRD Requirement | TDD Implementation |
|---|---|
| SYS-REQ-001 text-only first | scripts 01~03, Phase P2/P3 |
| SYS-REQ-003 hidden label exclusion | visibility.py, validation.py, collator guard |
| DATA-REQ coverage | coverage_auditor.py |
| MODEL-REQ latent heads | latent_heads.py |
| TRAIN-REQ losses | objectives/losses.py |
| PLAN-REQ falsification/gate/rewrite | planning modules |
| EVAL-REQ baselines/metrics | evaluation package |
| REPORT-REQ no fake numbers | reporting guard |
| NFR-REPRO manifests | logging/manifest.py |
| NFR-SEC no private data | source audit/config guard |

---

## 23. Claude Code Implementation Order

Claude Code must implement in this order.

```text
1. utils/config, utils/seed, utils/hashing
2. schemas/visibility, episode_schema, step_schema, validation
3. tests for schema and visibility
4. text_env generator and collector
5. text data coverage/leakage audits
6. text FRCG model and losses
7. planning minimal modules for text
8. text evaluation metrics/baselines/ablations
9. synthetic GUI environment dry-run modules
10. GUI action-effect/counterfactual/replay logging
11. GUI dataset exporter and validator
12. frozen VLM adapter and VLM MVE model heads
13. VLM training loop with batch safety logging
14. evaluation runner with compute-matched baselines
15. reporting generator
```

Forbidden implementation order:

```text
- VLM adapter before schema tests
- GUI collector before visibility contract
- paper-main config before text smoke gate
- report generator before metric artifacts
```

---

## 24. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-15-01 | module architecture defined | PASS | §4 | 없음 |
| QG-15-02 | core data types defined | PASS | §5 | 없음 |
| QG-15-03 | schema validation design included | PASS | §6 | 없음 |
| QG-15-04 | text env design included | PASS | §7 | 없음 |
| QG-15-05 | synthetic GUI design included | PASS | §8 | 없음 |
| QG-15-06 | logging/counterfactual design included | PASS | §9 | 없음 |
| QG-15-07 | data pipeline design included | PASS | §10 | 없음 |
| QG-15-08 | model architecture design included | PASS | §11 | 없음 |
| QG-15-09 | objective design included | PASS | §12 | 없음 |
| QG-15-10 | planning design included | PASS | §13 | 없음 |
| QG-15-11 | training design included | PASS | §14 | 없음 |
| QG-15-12 | evaluation design included | PASS | §15 | 없음 |
| QG-15-13 | reporting design included | PASS | §16 | 없음 |
| QG-15-14 | config/script/test design included | PASS | §17~19 | 없음 |
| QG-15-15 | run artifact and failure design included | PASS | §20~21 | 없음 |
| QG-15-16 | no empirical result fabricated | PASS | status and wording | 없음 |

---

## 25. Final Statement

`15_TDD_TECHNICAL_DESIGN_DOCUMENT.md`는 최종 코드가 아니다.  
이 문서는 FRCG-WM repo를 구현하기 위한 기술 설계 계약서다.

가장 중요한 구현 원칙은 다음이다.

```text
The implementation must make invalid science hard.

Hidden label leakage should fail at schema/collator level.
Missing baselines should fail at evaluation/report level.
Fake reports should fail at reporting level.
Scaling before gates should fail at config/run level.
```

다음 필수 파일:

```text
16_REPO_SCAFFOLD_AND_TEST_PLAN.md
```
