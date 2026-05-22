"""frcgw.text_env — Symbolic text-only environment and trajectory collector.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §7

Hard constraints:
- Hidden control grammar must not appear in visible_text (TEXT-REQ-002).
- text_env depends on schemas, data, logging — not on VLM or model training (TDD §4).
- Text-only results must never be claimed as Web/GUI evidence (TEXT-REQ-006).
- Minimum 8 task families required (TEXT-REQ-001).
"""
from frcgw.text_env.state import TextEpisodeSpec, TextState, TextStepResult
from frcgw.text_env.grammar import ControlGrammar, GrammarEngine
from frcgw.text_env.generator import (
    TaskFamily,
    TaskFamilyTemplate,
    EpisodeSpecGenerator,
    TASK_FAMILY_TEMPLATES,
    build_initial_state,
)
from frcgw.text_env.policies import (
    Policy,
    OraclePolicy,
    WrongGrammarPolicy,
    RetryPolicy,
    RecoveryPolicy,
    RandomConstrainedPolicy,
    PolicyMixtureRunner,
)
from frcgw.text_env.collector import (
    CollectorConfig,
    collect_episode,
    build_public_observation,
)
from frcgw.text_env.replay import ReplayValidator

__all__ = [
    "TextState",
    "TextEpisodeSpec",
    "TextStepResult",
    "ControlGrammar",
    "GrammarEngine",
    "TaskFamily",
    "TaskFamilyTemplate",
    "EpisodeSpecGenerator",
    "TASK_FAMILY_TEMPLATES",
    "build_initial_state",
    "Policy",
    "OraclePolicy",
    "WrongGrammarPolicy",
    "RetryPolicy",
    "RecoveryPolicy",
    "RandomConstrainedPolicy",
    "PolicyMixtureRunner",
    "CollectorConfig",
    "collect_episode",
    "build_public_observation",
    "ReplayValidator",
]
