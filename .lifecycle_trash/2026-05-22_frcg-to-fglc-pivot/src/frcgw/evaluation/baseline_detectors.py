"""Statistical baseline detectors for regime-switch detection.

Sources:
- Page, E.S. (1954). Continuous Inspection Schemes. Biometrika 41(1/2):100–115.
- Wald, A. (1945). Sequential Tests of Statistical Hypotheses. AoMS 16(2):117–186.
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md BASE-001 (frozen statistical baseline)

Used as comparison floor for the Learned Falsification Detector (LFD).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CUSUMDetector:
    """CUSUM change-point detector (Page 1954) for effect-type mismatch.

    Operates on a scalar LLR stream: positive values = mismatch evidence.
    Raises alarm when cumulative sum exceeds decision interval h.
    """
    k: float = 0.5    # reference value (allowance)
    h: float = 4.0    # decision interval (alarm threshold)
    S_pos: float = field(default=0.0, init=False, repr=False)
    S_neg: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.S_pos = 0.0
        self.S_neg = 0.0

    def update(self, llr: float) -> tuple[float, bool]:
        """Update CUSUM statistic with new LLR observation.

        Returns:
            (S_t, alarm_raised): current statistic and whether threshold crossed.
        """
        self.S_pos = max(0.0, self.S_pos + llr - self.k)
        self.S_neg = max(0.0, self.S_neg - llr - self.k)
        alarm = (self.S_pos >= self.h) or (self.S_neg >= self.h)
        return max(self.S_pos, self.S_neg), alarm

    def reset(self) -> None:
        self.S_pos = 0.0
        self.S_neg = 0.0

    @property
    def statistic(self) -> float:
        return max(self.S_pos, self.S_neg)


@dataclass
class SPRTDetector:
    """SPRT-style log-likelihood ratio test (Wald 1945).

    Accumulates LLR increments and makes a decision once the ratio
    crosses one of two thresholds A (reject H0) or B (accept H0).
    """
    A: float = 10.0   # upper threshold → reject H0 (change detected)
    B: float = 0.1    # lower threshold → accept H0 (no change)
    llr: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.llr = 0.0

    def update(self, llr_increment: float) -> str:
        """Add LLR increment and return decision.

        Returns:
            'reject_H0' | 'accept_H0' | 'continue'
        """
        self.llr += llr_increment
        if self.llr >= self.A:
            return "reject_H0"
        if self.llr <= self.B:
            return "accept_H0"
        return "continue"

    def reset(self) -> None:
        self.llr = 0.0


def compute_effect_llr(
    observed_effect_type: int,
    expected_effect_type: int,
    mismatch_weight: float = 1.0,
) -> float:
    """Compute LLR for one effect observation.

    Mismatch (wrong-grammar evidence) → positive LLR.
    Match (correct-grammar evidence) → negative LLR (stable evidence).
    """
    if observed_effect_type != expected_effect_type:
        return mismatch_weight
    return -mismatch_weight / 2.0


def run_cusum_on_episode(
    effect_types: list[int],
    expected_effect_type: int = 0,
    k: float = 0.5,
    h: float = 4.0,
    mismatch_weight: float = 1.0,
) -> dict:
    """Run CUSUM over a single episode's effect-type stream.

    Stops at first alarm (does not accumulate further alarms after first crossing).
    Statistical Validity Critic finding: once S_t >= h, subsequent steps remain above
    threshold — only the first crossing is a meaningful detection event.

    Returns:
        alarm_steps: list with at most one element (the first alarm step index)
        S_t_trace: CUSUM statistic at each step (up to and including first alarm)
        first_alarm: int | None
    """
    detector = CUSUMDetector(k=k, h=h)
    alarm_steps: list[int] = []
    S_t_trace: list[float] = []

    for step_idx, eff in enumerate(effect_types):
        llr = compute_effect_llr(eff, expected_effect_type, mismatch_weight)
        S_t, alarm = detector.update(llr)
        S_t_trace.append(S_t)
        if alarm:
            alarm_steps.append(step_idx)
            break  # stop at first alarm — subsequent steps remain above threshold

    return {
        "alarm_steps": alarm_steps,
        "S_t_trace": S_t_trace,
        "first_alarm": alarm_steps[0] if alarm_steps else None,
    }


def run_sprt_on_episode(
    effect_types: list[int],
    expected_effect_type: int = 0,
    A: float = 10.0,
    B: float = 0.1,
    mismatch_weight: float = 1.0,
) -> dict:
    """Run SPRT over a single episode's effect-type stream."""
    detector = SPRTDetector(A=A, B=B)
    alarm_steps: list[int] = []
    decisions: list[str] = []

    for step_idx, eff in enumerate(effect_types):
        llr = compute_effect_llr(eff, expected_effect_type, mismatch_weight)
        decision = detector.update(llr)
        decisions.append(decision)
        if decision == "reject_H0":
            alarm_steps.append(step_idx)
            break  # stop at first alarm — matches CUSUM single-alarm convention

    return {
        "alarm_steps": alarm_steps,
        "decisions": decisions,
        "first_alarm": alarm_steps[0] if alarm_steps else None,
    }
