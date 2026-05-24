"""R4 falsification gate package.

Source: docs/idea/02_FALSIFICATION_THEORY.md §B-C (standardized residual + conformal).
        reports/R3_SMOKE_CLOSURE_REPORT.md §H (R4 PASS gate proposal).
"""

from .conformal import coverage, ece, fit_per_group_thresholds, fit_threshold
from .gate import auroc_from_scores, beta_t_boolean, beta_t_continuous, cusum_score
from .residuals import (
    directional_bias_score,
    group_falsification_scores,
    signed_residual_mean,
    standardized_residual,
    total_falsification_score,
)

__all__ = [
    "standardized_residual",
    "group_falsification_scores",
    "total_falsification_score",
    "signed_residual_mean",
    "directional_bias_score",
    "fit_threshold",
    "fit_per_group_thresholds",
    "ece",
    "coverage",
    "beta_t_continuous",
    "beta_t_boolean",
    "cusum_score",
    "auroc_from_scores",
]
