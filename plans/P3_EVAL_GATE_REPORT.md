# P3 Evaluation Gate Report
Generated: 2026-05-13T10:16:04.210270+00:00
Eval artifacts: outputs\runs\p3_eval\metrics.json
Ablation artifacts: outputs\runs\p3_ablations\ablation_results.json

## Gate Results
| Gate | Status | Evidence |
| --- | --- | --- |
| CC-P3-G1 | FAIL | VerifierOnlyAgent recovery_delay=0.0; FrozenBaseAgent recovery_delay=0.0 |
| CC-P3-G2 | FAIL | VerifierOnlyAgent progress_per_compute=0.047361809045226126; UncertaintyGatedAgent progress_per_compute=0.09062499999999998 |
| CC-P3-G3 | FAIL | no_control_grammar wrong_control_grammar_persistence=0.0; FrozenBase wrong_control_grammar_persistence=0.0 |
| CC-P3-G4 | FAIL | no_falsification f1=0.0; baseline f1=0.0; no_falsification false_planning_call_rate=0.0; baseline false_planning_call_rate=0.0 |

## Metric Summary
| Agent | Split | Seed | Metric | Value |
| --- | --- | --- | --- | --- |
| BASE-001 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-001 | text_id | 0 | failed_action_repetition_rate | 0.5 |
| BASE-001 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-001 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-001 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-001 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-001 | text_id | 0 | progress_per_compute | 0.22848484848484846 |
| BASE-001 | text_id | 0 | recovery_delay | 0.0 |
| BASE-001 | text_id | 0 | task_success_rate | 1.0 |
| BASE-001 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-002 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-002 | text_id | 0 | failed_action_repetition_rate | 0.5 |
| BASE-002 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-002 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-002 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-002 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-002 | text_id | 0 | progress_per_compute | 0.22848484848484846 |
| BASE-002 | text_id | 0 | recovery_delay | 0.0 |
| BASE-002 | text_id | 0 | task_success_rate | 1.0 |
| BASE-002 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-003 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-003 | text_id | 0 | failed_action_repetition_rate | 0.5 |
| BASE-003 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-003 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-003 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-003 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-003 | text_id | 0 | progress_per_compute | 0.11424242424242423 |
| BASE-003 | text_id | 0 | recovery_delay | 0.0 |
| BASE-003 | text_id | 0 | task_success_rate | 1.0 |
| BASE-003 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-005 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-005 | text_id | 0 | failed_action_repetition_rate | 0.5 |
| BASE-005 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-005 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-005 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-005 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-005 | text_id | 0 | progress_per_compute | 0.047361809045226126 |
| BASE-005 | text_id | 0 | recovery_delay | 0.0 |
| BASE-005 | text_id | 0 | task_success_rate | 1.0 |
| BASE-005 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-009 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-009 | text_id | 0 | failed_action_repetition_rate | 0.125 |
| BASE-009 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-009 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-009 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-009 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-009 | text_id | 0 | progress_per_compute | 0.026419060967063767 |
| BASE-009 | text_id | 0 | recovery_delay | 0.0 |
| BASE-009 | text_id | 0 | task_success_rate | 1.0 |
| BASE-009 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-010 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-010 | text_id | 0 | failed_action_repetition_rate | 0.5 |
| BASE-010 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-010 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-010 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-010 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-010 | text_id | 0 | progress_per_compute | 0.047361809045226126 |
| BASE-010 | text_id | 0 | recovery_delay | 0.0 |
| BASE-010 | text_id | 0 | task_success_rate | 1.0 |
| BASE-010 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-012 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-012 | text_id | 0 | failed_action_repetition_rate | 0.19642857142857142 |
| BASE-012 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-012 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-012 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-012 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-012 | text_id | 0 | progress_per_compute | 0.09062499999999998 |
| BASE-012 | text_id | 0 | recovery_delay | 0.0 |
| BASE-012 | text_id | 0 | task_success_rate | 1.0 |
| BASE-012 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-014 | text_id | 0 | action_switch_delay | 0.0 |
| BASE-014 | text_id | 0 | failed_action_repetition_rate | 0.14285714285714285 |
| BASE-014 | text_id | 0 | false_planning_call_rate | 0.0 |
| BASE-014 | text_id | 0 | falsification_calibration | 0.30303030303030304 |
| BASE-014 | text_id | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-014 | text_id | 0 | normalized_return | 0.9999999918181818 |
| BASE-014 | text_id | 0 | progress_per_compute | 0.047361809045226126 |
| BASE-014 | text_id | 0 | recovery_delay | 0.0 |
| BASE-014 | text_id | 0 | task_success_rate | 1.0 |
| BASE-014 | text_id | 0 | wrong_control_grammar_persistence | 0.0 |
| BASE-001 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-001 | text_id | 1 | failed_action_repetition_rate | 0.5 |
| BASE-001 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-001 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-001 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-001 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-001 | text_id | 1 | progress_per_compute | 0.22848484848484846 |
| BASE-001 | text_id | 1 | recovery_delay | 0.0 |
| BASE-001 | text_id | 1 | task_success_rate | 1.0 |
| BASE-001 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-002 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-002 | text_id | 1 | failed_action_repetition_rate | 0.5 |
| BASE-002 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-002 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-002 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-002 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-002 | text_id | 1 | progress_per_compute | 0.22848484848484846 |
| BASE-002 | text_id | 1 | recovery_delay | 0.0 |
| BASE-002 | text_id | 1 | task_success_rate | 1.0 |
| BASE-002 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-003 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-003 | text_id | 1 | failed_action_repetition_rate | 0.5 |
| BASE-003 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-003 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-003 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-003 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-003 | text_id | 1 | progress_per_compute | 0.11424242424242423 |
| BASE-003 | text_id | 1 | recovery_delay | 0.0 |
| BASE-003 | text_id | 1 | task_success_rate | 1.0 |
| BASE-003 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-005 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-005 | text_id | 1 | failed_action_repetition_rate | 0.5 |
| BASE-005 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-005 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-005 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-005 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-005 | text_id | 1 | progress_per_compute | 0.047361809045226126 |
| BASE-005 | text_id | 1 | recovery_delay | 0.0 |
| BASE-005 | text_id | 1 | task_success_rate | 1.0 |
| BASE-005 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-009 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-009 | text_id | 1 | failed_action_repetition_rate | 0.125 |
| BASE-009 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-009 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-009 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-009 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-009 | text_id | 1 | progress_per_compute | 0.026419060967063767 |
| BASE-009 | text_id | 1 | recovery_delay | 0.0 |
| BASE-009 | text_id | 1 | task_success_rate | 1.0 |
| BASE-009 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-010 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-010 | text_id | 1 | failed_action_repetition_rate | 0.5 |
| BASE-010 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-010 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-010 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-010 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-010 | text_id | 1 | progress_per_compute | 0.047361809045226126 |
| BASE-010 | text_id | 1 | recovery_delay | 0.0 |
| BASE-010 | text_id | 1 | task_success_rate | 1.0 |
| BASE-010 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-012 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-012 | text_id | 1 | failed_action_repetition_rate | 0.19642857142857142 |
| BASE-012 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-012 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-012 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-012 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-012 | text_id | 1 | progress_per_compute | 0.09062499999999998 |
| BASE-012 | text_id | 1 | recovery_delay | 0.0 |
| BASE-012 | text_id | 1 | task_success_rate | 1.0 |
| BASE-012 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-014 | text_id | 1 | action_switch_delay | 0.0 |
| BASE-014 | text_id | 1 | failed_action_repetition_rate | 0.08928571428571429 |
| BASE-014 | text_id | 1 | false_planning_call_rate | 0.0 |
| BASE-014 | text_id | 1 | falsification_calibration | 0.30303030303030304 |
| BASE-014 | text_id | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-014 | text_id | 1 | normalized_return | 0.9999999918181818 |
| BASE-014 | text_id | 1 | progress_per_compute | 0.047361809045226126 |
| BASE-014 | text_id | 1 | recovery_delay | 0.0 |
| BASE-014 | text_id | 1 | task_success_rate | 1.0 |
| BASE-014 | text_id | 1 | wrong_control_grammar_persistence | 0.0 |
| BASE-001 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-001 | text_id | 2 | failed_action_repetition_rate | 0.5 |
| BASE-001 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-001 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-001 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-001 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-001 | text_id | 2 | progress_per_compute | 0.22848484848484846 |
| BASE-001 | text_id | 2 | recovery_delay | 0.0 |
| BASE-001 | text_id | 2 | task_success_rate | 1.0 |
| BASE-001 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-002 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-002 | text_id | 2 | failed_action_repetition_rate | 0.5 |
| BASE-002 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-002 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-002 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-002 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-002 | text_id | 2 | progress_per_compute | 0.22848484848484846 |
| BASE-002 | text_id | 2 | recovery_delay | 0.0 |
| BASE-002 | text_id | 2 | task_success_rate | 1.0 |
| BASE-002 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-003 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-003 | text_id | 2 | failed_action_repetition_rate | 0.5 |
| BASE-003 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-003 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-003 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-003 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-003 | text_id | 2 | progress_per_compute | 0.11424242424242423 |
| BASE-003 | text_id | 2 | recovery_delay | 0.0 |
| BASE-003 | text_id | 2 | task_success_rate | 1.0 |
| BASE-003 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-005 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-005 | text_id | 2 | failed_action_repetition_rate | 0.5 |
| BASE-005 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-005 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-005 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-005 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-005 | text_id | 2 | progress_per_compute | 0.047361809045226126 |
| BASE-005 | text_id | 2 | recovery_delay | 0.0 |
| BASE-005 | text_id | 2 | task_success_rate | 1.0 |
| BASE-005 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-009 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-009 | text_id | 2 | failed_action_repetition_rate | 0.125 |
| BASE-009 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-009 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-009 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-009 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-009 | text_id | 2 | progress_per_compute | 0.026419060967063767 |
| BASE-009 | text_id | 2 | recovery_delay | 0.0 |
| BASE-009 | text_id | 2 | task_success_rate | 1.0 |
| BASE-009 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-010 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-010 | text_id | 2 | failed_action_repetition_rate | 0.5 |
| BASE-010 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-010 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-010 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-010 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-010 | text_id | 2 | progress_per_compute | 0.047361809045226126 |
| BASE-010 | text_id | 2 | recovery_delay | 0.0 |
| BASE-010 | text_id | 2 | task_success_rate | 1.0 |
| BASE-010 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-012 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-012 | text_id | 2 | failed_action_repetition_rate | 0.19642857142857142 |
| BASE-012 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-012 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-012 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-012 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-012 | text_id | 2 | progress_per_compute | 0.09062499999999998 |
| BASE-012 | text_id | 2 | recovery_delay | 0.0 |
| BASE-012 | text_id | 2 | task_success_rate | 1.0 |
| BASE-012 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-014 | text_id | 2 | action_switch_delay | 0.0 |
| BASE-014 | text_id | 2 | failed_action_repetition_rate | 0.10714285714285714 |
| BASE-014 | text_id | 2 | false_planning_call_rate | 0.0 |
| BASE-014 | text_id | 2 | falsification_calibration | 0.30303030303030304 |
| BASE-014 | text_id | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-014 | text_id | 2 | normalized_return | 0.9999999918181818 |
| BASE-014 | text_id | 2 | progress_per_compute | 0.047361809045226126 |
| BASE-014 | text_id | 2 | recovery_delay | 0.0 |
| BASE-014 | text_id | 2 | task_success_rate | 1.0 |
| BASE-014 | text_id | 2 | wrong_control_grammar_persistence | 0.0 |
| BASE-001 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-001 | text_id | 3 | failed_action_repetition_rate | 0.5 |
| BASE-001 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-001 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-001 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-001 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-001 | text_id | 3 | progress_per_compute | 0.22848484848484846 |
| BASE-001 | text_id | 3 | recovery_delay | 0.0 |
| BASE-001 | text_id | 3 | task_success_rate | 1.0 |
| BASE-001 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-002 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-002 | text_id | 3 | failed_action_repetition_rate | 0.5 |
| BASE-002 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-002 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-002 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-002 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-002 | text_id | 3 | progress_per_compute | 0.22848484848484846 |
| BASE-002 | text_id | 3 | recovery_delay | 0.0 |
| BASE-002 | text_id | 3 | task_success_rate | 1.0 |
| BASE-002 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-003 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-003 | text_id | 3 | failed_action_repetition_rate | 0.5 |
| BASE-003 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-003 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-003 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-003 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-003 | text_id | 3 | progress_per_compute | 0.11424242424242423 |
| BASE-003 | text_id | 3 | recovery_delay | 0.0 |
| BASE-003 | text_id | 3 | task_success_rate | 1.0 |
| BASE-003 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-005 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-005 | text_id | 3 | failed_action_repetition_rate | 0.5 |
| BASE-005 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-005 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-005 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-005 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-005 | text_id | 3 | progress_per_compute | 0.047361809045226126 |
| BASE-005 | text_id | 3 | recovery_delay | 0.0 |
| BASE-005 | text_id | 3 | task_success_rate | 1.0 |
| BASE-005 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-009 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-009 | text_id | 3 | failed_action_repetition_rate | 0.125 |
| BASE-009 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-009 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-009 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-009 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-009 | text_id | 3 | progress_per_compute | 0.026419060967063767 |
| BASE-009 | text_id | 3 | recovery_delay | 0.0 |
| BASE-009 | text_id | 3 | task_success_rate | 1.0 |
| BASE-009 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-010 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-010 | text_id | 3 | failed_action_repetition_rate | 0.5 |
| BASE-010 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-010 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-010 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-010 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-010 | text_id | 3 | progress_per_compute | 0.047361809045226126 |
| BASE-010 | text_id | 3 | recovery_delay | 0.0 |
| BASE-010 | text_id | 3 | task_success_rate | 1.0 |
| BASE-010 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-012 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-012 | text_id | 3 | failed_action_repetition_rate | 0.19642857142857142 |
| BASE-012 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-012 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-012 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-012 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-012 | text_id | 3 | progress_per_compute | 0.09062499999999998 |
| BASE-012 | text_id | 3 | recovery_delay | 0.0 |
| BASE-012 | text_id | 3 | task_success_rate | 1.0 |
| BASE-012 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-014 | text_id | 3 | action_switch_delay | 0.0 |
| BASE-014 | text_id | 3 | failed_action_repetition_rate | 0.08928571428571429 |
| BASE-014 | text_id | 3 | false_planning_call_rate | 0.0 |
| BASE-014 | text_id | 3 | falsification_calibration | 0.30303030303030304 |
| BASE-014 | text_id | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-014 | text_id | 3 | normalized_return | 0.9999999918181818 |
| BASE-014 | text_id | 3 | progress_per_compute | 0.047361809045226126 |
| BASE-014 | text_id | 3 | recovery_delay | 0.0 |
| BASE-014 | text_id | 3 | task_success_rate | 1.0 |
| BASE-014 | text_id | 3 | wrong_control_grammar_persistence | 0.0 |
| BASE-001 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-001 | text_id | 4 | failed_action_repetition_rate | 0.5 |
| BASE-001 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-001 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-001 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-001 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-001 | text_id | 4 | progress_per_compute | 0.22848484848484846 |
| BASE-001 | text_id | 4 | recovery_delay | 0.0 |
| BASE-001 | text_id | 4 | task_success_rate | 1.0 |
| BASE-001 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |
| BASE-002 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-002 | text_id | 4 | failed_action_repetition_rate | 0.5 |
| BASE-002 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-002 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-002 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-002 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-002 | text_id | 4 | progress_per_compute | 0.22848484848484846 |
| BASE-002 | text_id | 4 | recovery_delay | 0.0 |
| BASE-002 | text_id | 4 | task_success_rate | 1.0 |
| BASE-002 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |
| BASE-003 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-003 | text_id | 4 | failed_action_repetition_rate | 0.5 |
| BASE-003 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-003 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-003 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-003 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-003 | text_id | 4 | progress_per_compute | 0.11424242424242423 |
| BASE-003 | text_id | 4 | recovery_delay | 0.0 |
| BASE-003 | text_id | 4 | task_success_rate | 1.0 |
| BASE-003 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |
| BASE-005 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-005 | text_id | 4 | failed_action_repetition_rate | 0.5 |
| BASE-005 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-005 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-005 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-005 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-005 | text_id | 4 | progress_per_compute | 0.047361809045226126 |
| BASE-005 | text_id | 4 | recovery_delay | 0.0 |
| BASE-005 | text_id | 4 | task_success_rate | 1.0 |
| BASE-005 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |
| BASE-009 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-009 | text_id | 4 | failed_action_repetition_rate | 0.125 |
| BASE-009 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-009 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-009 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-009 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-009 | text_id | 4 | progress_per_compute | 0.026419060967063767 |
| BASE-009 | text_id | 4 | recovery_delay | 0.0 |
| BASE-009 | text_id | 4 | task_success_rate | 1.0 |
| BASE-009 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |
| BASE-010 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-010 | text_id | 4 | failed_action_repetition_rate | 0.5 |
| BASE-010 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-010 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-010 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-010 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-010 | text_id | 4 | progress_per_compute | 0.047361809045226126 |
| BASE-010 | text_id | 4 | recovery_delay | 0.0 |
| BASE-010 | text_id | 4 | task_success_rate | 1.0 |
| BASE-010 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |
| BASE-012 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-012 | text_id | 4 | failed_action_repetition_rate | 0.19642857142857142 |
| BASE-012 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-012 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-012 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-012 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-012 | text_id | 4 | progress_per_compute | 0.09062499999999998 |
| BASE-012 | text_id | 4 | recovery_delay | 0.0 |
| BASE-012 | text_id | 4 | task_success_rate | 1.0 |
| BASE-012 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |
| BASE-014 | text_id | 4 | action_switch_delay | 0.0 |
| BASE-014 | text_id | 4 | failed_action_repetition_rate | 0.125 |
| BASE-014 | text_id | 4 | false_planning_call_rate | 0.0 |
| BASE-014 | text_id | 4 | falsification_calibration | 0.30303030303030304 |
| BASE-014 | text_id | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| BASE-014 | text_id | 4 | normalized_return | 0.9999999918181818 |
| BASE-014 | text_id | 4 | progress_per_compute | 0.047361809045226126 |
| BASE-014 | text_id | 4 | recovery_delay | 0.0 |
| BASE-014 | text_id | 4 | task_success_rate | 1.0 |
| BASE-014 | text_id | 4 | wrong_control_grammar_persistence | 0.0 |

## Ablation Summary
| Ablation | Split | Seed | Metric | Value |
| --- | --- | --- | --- | --- |
| no_control_grammar | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 0 | failed_action_repetition_rate | 0.125 |
| no_control_grammar | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| no_control_grammar | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| no_control_grammar | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_control_grammar | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| no_control_grammar | text_ood_grammar | 0 | progress_per_compute | 0.05974643423137876 |
| no_control_grammar | text_ood_grammar | 0 | recovery_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 0 | task_success_rate | 1.0 |
| no_control_grammar | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| no_control_grammar | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 1 | failed_action_repetition_rate | 0.125 |
| no_control_grammar | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| no_control_grammar | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| no_control_grammar | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_control_grammar | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| no_control_grammar | text_ood_grammar | 1 | progress_per_compute | 0.05974643423137876 |
| no_control_grammar | text_ood_grammar | 1 | recovery_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 1 | task_success_rate | 1.0 |
| no_control_grammar | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| no_control_grammar | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 2 | failed_action_repetition_rate | 0.125 |
| no_control_grammar | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| no_control_grammar | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| no_control_grammar | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_control_grammar | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| no_control_grammar | text_ood_grammar | 2 | progress_per_compute | 0.05974643423137876 |
| no_control_grammar | text_ood_grammar | 2 | recovery_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 2 | task_success_rate | 1.0 |
| no_control_grammar | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| no_control_grammar | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 3 | failed_action_repetition_rate | 0.125 |
| no_control_grammar | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| no_control_grammar | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| no_control_grammar | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_control_grammar | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| no_control_grammar | text_ood_grammar | 3 | progress_per_compute | 0.05974643423137876 |
| no_control_grammar | text_ood_grammar | 3 | recovery_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 3 | task_success_rate | 1.0 |
| no_control_grammar | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| no_control_grammar | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 4 | failed_action_repetition_rate | 0.125 |
| no_control_grammar | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| no_control_grammar | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| no_control_grammar | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_control_grammar | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| no_control_grammar | text_ood_grammar | 4 | progress_per_compute | 0.05974643423137876 |
| no_control_grammar | text_ood_grammar | 4 | recovery_delay | 0.0 |
| no_control_grammar | text_ood_grammar | 4 | task_success_rate | 1.0 |
| no_control_grammar | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| merged_regime_control_grammar | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| merged_regime_control_grammar | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| merged_regime_control_grammar | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| merged_regime_control_grammar | text_ood_grammar | 0 | progress_per_compute | 0.22848484848484846 |
| merged_regime_control_grammar | text_ood_grammar | 0 | recovery_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 0 | task_success_rate | 1.0 |
| merged_regime_control_grammar | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| merged_regime_control_grammar | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| merged_regime_control_grammar | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| merged_regime_control_grammar | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| merged_regime_control_grammar | text_ood_grammar | 1 | progress_per_compute | 0.22848484848484846 |
| merged_regime_control_grammar | text_ood_grammar | 1 | recovery_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 1 | task_success_rate | 1.0 |
| merged_regime_control_grammar | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| merged_regime_control_grammar | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| merged_regime_control_grammar | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| merged_regime_control_grammar | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| merged_regime_control_grammar | text_ood_grammar | 2 | progress_per_compute | 0.22848484848484846 |
| merged_regime_control_grammar | text_ood_grammar | 2 | recovery_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 2 | task_success_rate | 1.0 |
| merged_regime_control_grammar | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| merged_regime_control_grammar | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| merged_regime_control_grammar | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| merged_regime_control_grammar | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| merged_regime_control_grammar | text_ood_grammar | 3 | progress_per_compute | 0.22848484848484846 |
| merged_regime_control_grammar | text_ood_grammar | 3 | recovery_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 3 | task_success_rate | 1.0 |
| merged_regime_control_grammar | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| merged_regime_control_grammar | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| merged_regime_control_grammar | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| merged_regime_control_grammar | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| merged_regime_control_grammar | text_ood_grammar | 4 | progress_per_compute | 0.22848484848484846 |
| merged_regime_control_grammar | text_ood_grammar | 4 | recovery_delay | 0.0 |
| merged_regime_control_grammar | text_ood_grammar | 4 | task_success_rate | 1.0 |
| merged_regime_control_grammar | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| collapsed_latent | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| collapsed_latent | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| collapsed_latent | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| collapsed_latent | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| collapsed_latent | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| collapsed_latent | text_ood_grammar | 0 | progress_per_compute | 0.22848484848484846 |
| collapsed_latent | text_ood_grammar | 0 | recovery_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 0 | task_success_rate | 1.0 |
| collapsed_latent | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| collapsed_latent | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| collapsed_latent | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| collapsed_latent | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| collapsed_latent | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| collapsed_latent | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| collapsed_latent | text_ood_grammar | 1 | progress_per_compute | 0.22848484848484846 |
| collapsed_latent | text_ood_grammar | 1 | recovery_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 1 | task_success_rate | 1.0 |
| collapsed_latent | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| collapsed_latent | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| collapsed_latent | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| collapsed_latent | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| collapsed_latent | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| collapsed_latent | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| collapsed_latent | text_ood_grammar | 2 | progress_per_compute | 0.22848484848484846 |
| collapsed_latent | text_ood_grammar | 2 | recovery_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 2 | task_success_rate | 1.0 |
| collapsed_latent | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| collapsed_latent | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| collapsed_latent | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| collapsed_latent | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| collapsed_latent | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| collapsed_latent | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| collapsed_latent | text_ood_grammar | 3 | progress_per_compute | 0.22848484848484846 |
| collapsed_latent | text_ood_grammar | 3 | recovery_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 3 | task_success_rate | 1.0 |
| collapsed_latent | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| collapsed_latent | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| collapsed_latent | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| collapsed_latent | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| collapsed_latent | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| collapsed_latent | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| collapsed_latent | text_ood_grammar | 4 | progress_per_compute | 0.22848484848484846 |
| collapsed_latent | text_ood_grammar | 4 | recovery_delay | 0.0 |
| collapsed_latent | text_ood_grammar | 4 | task_success_rate | 1.0 |
| collapsed_latent | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| no_falsification | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| no_falsification | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| no_falsification | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| no_falsification | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| no_falsification | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_falsification | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| no_falsification | text_ood_grammar | 0 | progress_per_compute | 0.22848484848484846 |
| no_falsification | text_ood_grammar | 0 | recovery_delay | 0.0 |
| no_falsification | text_ood_grammar | 0 | task_success_rate | 1.0 |
| no_falsification | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| no_falsification | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| no_falsification | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| no_falsification | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| no_falsification | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| no_falsification | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_falsification | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| no_falsification | text_ood_grammar | 1 | progress_per_compute | 0.22848484848484846 |
| no_falsification | text_ood_grammar | 1 | recovery_delay | 0.0 |
| no_falsification | text_ood_grammar | 1 | task_success_rate | 1.0 |
| no_falsification | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| no_falsification | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| no_falsification | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| no_falsification | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| no_falsification | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| no_falsification | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_falsification | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| no_falsification | text_ood_grammar | 2 | progress_per_compute | 0.22848484848484846 |
| no_falsification | text_ood_grammar | 2 | recovery_delay | 0.0 |
| no_falsification | text_ood_grammar | 2 | task_success_rate | 1.0 |
| no_falsification | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| no_falsification | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| no_falsification | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| no_falsification | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| no_falsification | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| no_falsification | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_falsification | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| no_falsification | text_ood_grammar | 3 | progress_per_compute | 0.22848484848484846 |
| no_falsification | text_ood_grammar | 3 | recovery_delay | 0.0 |
| no_falsification | text_ood_grammar | 3 | task_success_rate | 1.0 |
| no_falsification | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| no_falsification | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| no_falsification | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| no_falsification | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| no_falsification | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| no_falsification | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_falsification | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| no_falsification | text_ood_grammar | 4 | progress_per_compute | 0.22848484848484846 |
| no_falsification | text_ood_grammar | 4 | recovery_delay | 0.0 |
| no_falsification | text_ood_grammar | 4 | task_success_rate | 1.0 |
| no_falsification | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | failed_action_repetition_rate | 0.19642857142857142 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | progress_per_compute | 0.09062499999999998 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | recovery_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | task_success_rate | 1.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | failed_action_repetition_rate | 0.19642857142857142 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | progress_per_compute | 0.09062499999999998 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | recovery_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | task_success_rate | 1.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | failed_action_repetition_rate | 0.19642857142857142 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | progress_per_compute | 0.09062499999999998 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | recovery_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | task_success_rate | 1.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | failed_action_repetition_rate | 0.19642857142857142 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | progress_per_compute | 0.09062499999999998 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | recovery_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | task_success_rate | 1.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | failed_action_repetition_rate | 0.19642857142857142 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | progress_per_compute | 0.09062499999999998 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | recovery_delay | 0.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | task_success_rate | 1.0 |
| uncertainty_instead_of_falsification | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| no_alternative_hypothesis | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| no_alternative_hypothesis | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_alternative_hypothesis | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| no_alternative_hypothesis | text_ood_grammar | 0 | progress_per_compute | 0.11424242424242423 |
| no_alternative_hypothesis | text_ood_grammar | 0 | recovery_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 0 | task_success_rate | 1.0 |
| no_alternative_hypothesis | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| no_alternative_hypothesis | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| no_alternative_hypothesis | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_alternative_hypothesis | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| no_alternative_hypothesis | text_ood_grammar | 1 | progress_per_compute | 0.11424242424242423 |
| no_alternative_hypothesis | text_ood_grammar | 1 | recovery_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 1 | task_success_rate | 1.0 |
| no_alternative_hypothesis | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| no_alternative_hypothesis | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| no_alternative_hypothesis | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_alternative_hypothesis | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| no_alternative_hypothesis | text_ood_grammar | 2 | progress_per_compute | 0.11424242424242423 |
| no_alternative_hypothesis | text_ood_grammar | 2 | recovery_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 2 | task_success_rate | 1.0 |
| no_alternative_hypothesis | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| no_alternative_hypothesis | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| no_alternative_hypothesis | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_alternative_hypothesis | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| no_alternative_hypothesis | text_ood_grammar | 3 | progress_per_compute | 0.11424242424242423 |
| no_alternative_hypothesis | text_ood_grammar | 3 | recovery_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 3 | task_success_rate | 1.0 |
| no_alternative_hypothesis | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| no_alternative_hypothesis | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| no_alternative_hypothesis | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_alternative_hypothesis | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| no_alternative_hypothesis | text_ood_grammar | 4 | progress_per_compute | 0.11424242424242423 |
| no_alternative_hypothesis | text_ood_grammar | 4 | recovery_delay | 0.0 |
| no_alternative_hypothesis | text_ood_grammar | 4 | task_success_rate | 1.0 |
| no_alternative_hypothesis | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| random_alternative | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| random_alternative | text_ood_grammar | 0 | failed_action_repetition_rate | 0.08928571428571429 |
| random_alternative | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| random_alternative | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| random_alternative | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| random_alternative | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| random_alternative | text_ood_grammar | 0 | progress_per_compute | 0.047361809045226126 |
| random_alternative | text_ood_grammar | 0 | recovery_delay | 0.0 |
| random_alternative | text_ood_grammar | 0 | task_success_rate | 1.0 |
| random_alternative | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| random_alternative | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| random_alternative | text_ood_grammar | 1 | failed_action_repetition_rate | 0.08928571428571429 |
| random_alternative | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| random_alternative | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| random_alternative | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| random_alternative | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| random_alternative | text_ood_grammar | 1 | progress_per_compute | 0.047361809045226126 |
| random_alternative | text_ood_grammar | 1 | recovery_delay | 0.0 |
| random_alternative | text_ood_grammar | 1 | task_success_rate | 1.0 |
| random_alternative | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| random_alternative | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| random_alternative | text_ood_grammar | 2 | failed_action_repetition_rate | 0.08928571428571429 |
| random_alternative | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| random_alternative | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| random_alternative | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| random_alternative | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| random_alternative | text_ood_grammar | 2 | progress_per_compute | 0.047361809045226126 |
| random_alternative | text_ood_grammar | 2 | recovery_delay | 0.0 |
| random_alternative | text_ood_grammar | 2 | task_success_rate | 1.0 |
| random_alternative | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| random_alternative | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| random_alternative | text_ood_grammar | 3 | failed_action_repetition_rate | 0.08928571428571429 |
| random_alternative | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| random_alternative | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| random_alternative | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| random_alternative | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| random_alternative | text_ood_grammar | 3 | progress_per_compute | 0.047361809045226126 |
| random_alternative | text_ood_grammar | 3 | recovery_delay | 0.0 |
| random_alternative | text_ood_grammar | 3 | task_success_rate | 1.0 |
| random_alternative | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| random_alternative | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| random_alternative | text_ood_grammar | 4 | failed_action_repetition_rate | 0.08928571428571429 |
| random_alternative | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| random_alternative | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| random_alternative | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| random_alternative | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| random_alternative | text_ood_grammar | 4 | progress_per_compute | 0.047361809045226126 |
| random_alternative | text_ood_grammar | 4 | recovery_delay | 0.0 |
| random_alternative | text_ood_grammar | 4 | task_success_rate | 1.0 |
| random_alternative | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| no_rollout | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| no_rollout | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| no_rollout | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| no_rollout | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| no_rollout | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rollout | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| no_rollout | text_ood_grammar | 0 | progress_per_compute | 0.047361809045226126 |
| no_rollout | text_ood_grammar | 0 | recovery_delay | 0.0 |
| no_rollout | text_ood_grammar | 0 | task_success_rate | 1.0 |
| no_rollout | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| no_rollout | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| no_rollout | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| no_rollout | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| no_rollout | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| no_rollout | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rollout | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| no_rollout | text_ood_grammar | 1 | progress_per_compute | 0.047361809045226126 |
| no_rollout | text_ood_grammar | 1 | recovery_delay | 0.0 |
| no_rollout | text_ood_grammar | 1 | task_success_rate | 1.0 |
| no_rollout | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| no_rollout | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| no_rollout | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| no_rollout | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| no_rollout | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| no_rollout | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rollout | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| no_rollout | text_ood_grammar | 2 | progress_per_compute | 0.047361809045226126 |
| no_rollout | text_ood_grammar | 2 | recovery_delay | 0.0 |
| no_rollout | text_ood_grammar | 2 | task_success_rate | 1.0 |
| no_rollout | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| no_rollout | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| no_rollout | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| no_rollout | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| no_rollout | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| no_rollout | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rollout | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| no_rollout | text_ood_grammar | 3 | progress_per_compute | 0.047361809045226126 |
| no_rollout | text_ood_grammar | 3 | recovery_delay | 0.0 |
| no_rollout | text_ood_grammar | 3 | task_success_rate | 1.0 |
| no_rollout | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| no_rollout | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| no_rollout | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| no_rollout | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| no_rollout | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| no_rollout | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rollout | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| no_rollout | text_ood_grammar | 4 | progress_per_compute | 0.047361809045226126 |
| no_rollout | text_ood_grammar | 4 | recovery_delay | 0.0 |
| no_rollout | text_ood_grammar | 4 | task_success_rate | 1.0 |
| no_rollout | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| no_rewrite | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| no_rewrite | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| no_rewrite | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| no_rewrite | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| no_rewrite | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rewrite | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| no_rewrite | text_ood_grammar | 0 | progress_per_compute | 0.22848484848484846 |
| no_rewrite | text_ood_grammar | 0 | recovery_delay | 0.0 |
| no_rewrite | text_ood_grammar | 0 | task_success_rate | 1.0 |
| no_rewrite | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| no_rewrite | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| no_rewrite | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| no_rewrite | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| no_rewrite | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| no_rewrite | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rewrite | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| no_rewrite | text_ood_grammar | 1 | progress_per_compute | 0.22848484848484846 |
| no_rewrite | text_ood_grammar | 1 | recovery_delay | 0.0 |
| no_rewrite | text_ood_grammar | 1 | task_success_rate | 1.0 |
| no_rewrite | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| no_rewrite | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| no_rewrite | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| no_rewrite | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| no_rewrite | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| no_rewrite | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rewrite | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| no_rewrite | text_ood_grammar | 2 | progress_per_compute | 0.22848484848484846 |
| no_rewrite | text_ood_grammar | 2 | recovery_delay | 0.0 |
| no_rewrite | text_ood_grammar | 2 | task_success_rate | 1.0 |
| no_rewrite | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| no_rewrite | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| no_rewrite | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| no_rewrite | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| no_rewrite | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| no_rewrite | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rewrite | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| no_rewrite | text_ood_grammar | 3 | progress_per_compute | 0.22848484848484846 |
| no_rewrite | text_ood_grammar | 3 | recovery_delay | 0.0 |
| no_rewrite | text_ood_grammar | 3 | task_success_rate | 1.0 |
| no_rewrite | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| no_rewrite | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| no_rewrite | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| no_rewrite | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| no_rewrite | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| no_rewrite | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_rewrite | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| no_rewrite | text_ood_grammar | 4 | progress_per_compute | 0.22848484848484846 |
| no_rewrite | text_ood_grammar | 4 | recovery_delay | 0.0 |
| no_rewrite | text_ood_grammar | 4 | task_success_rate | 1.0 |
| no_rewrite | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| always_plan_no_gate | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| always_plan_no_gate | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| always_plan_no_gate | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| always_plan_no_gate | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| always_plan_no_gate | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| always_plan_no_gate | text_ood_grammar | 0 | progress_per_compute | 0.047361809045226126 |
| always_plan_no_gate | text_ood_grammar | 0 | recovery_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 0 | task_success_rate | 1.0 |
| always_plan_no_gate | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| always_plan_no_gate | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| always_plan_no_gate | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| always_plan_no_gate | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| always_plan_no_gate | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| always_plan_no_gate | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| always_plan_no_gate | text_ood_grammar | 1 | progress_per_compute | 0.047361809045226126 |
| always_plan_no_gate | text_ood_grammar | 1 | recovery_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 1 | task_success_rate | 1.0 |
| always_plan_no_gate | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| always_plan_no_gate | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| always_plan_no_gate | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| always_plan_no_gate | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| always_plan_no_gate | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| always_plan_no_gate | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| always_plan_no_gate | text_ood_grammar | 2 | progress_per_compute | 0.047361809045226126 |
| always_plan_no_gate | text_ood_grammar | 2 | recovery_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 2 | task_success_rate | 1.0 |
| always_plan_no_gate | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| always_plan_no_gate | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| always_plan_no_gate | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| always_plan_no_gate | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| always_plan_no_gate | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| always_plan_no_gate | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| always_plan_no_gate | text_ood_grammar | 3 | progress_per_compute | 0.047361809045226126 |
| always_plan_no_gate | text_ood_grammar | 3 | recovery_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 3 | task_success_rate | 1.0 |
| always_plan_no_gate | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| always_plan_no_gate | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| always_plan_no_gate | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| always_plan_no_gate | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| always_plan_no_gate | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| always_plan_no_gate | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| always_plan_no_gate | text_ood_grammar | 4 | progress_per_compute | 0.047361809045226126 |
| always_plan_no_gate | text_ood_grammar | 4 | recovery_delay | 0.0 |
| always_plan_no_gate | text_ood_grammar | 4 | task_success_rate | 1.0 |
| always_plan_no_gate | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| no_progress_reward | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 0 | failed_action_repetition_rate | 0.16071428571428573 |
| no_progress_reward | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| no_progress_reward | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| no_progress_reward | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_progress_reward | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| no_progress_reward | text_ood_grammar | 0 | progress_per_compute | 0.026419060967063767 |
| no_progress_reward | text_ood_grammar | 0 | recovery_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 0 | task_success_rate | 1.0 |
| no_progress_reward | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| no_progress_reward | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 1 | failed_action_repetition_rate | 0.16071428571428573 |
| no_progress_reward | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| no_progress_reward | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| no_progress_reward | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_progress_reward | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| no_progress_reward | text_ood_grammar | 1 | progress_per_compute | 0.026419060967063767 |
| no_progress_reward | text_ood_grammar | 1 | recovery_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 1 | task_success_rate | 1.0 |
| no_progress_reward | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| no_progress_reward | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 2 | failed_action_repetition_rate | 0.16071428571428573 |
| no_progress_reward | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| no_progress_reward | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| no_progress_reward | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_progress_reward | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| no_progress_reward | text_ood_grammar | 2 | progress_per_compute | 0.026419060967063767 |
| no_progress_reward | text_ood_grammar | 2 | recovery_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 2 | task_success_rate | 1.0 |
| no_progress_reward | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| no_progress_reward | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 3 | failed_action_repetition_rate | 0.16071428571428573 |
| no_progress_reward | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| no_progress_reward | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| no_progress_reward | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_progress_reward | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| no_progress_reward | text_ood_grammar | 3 | progress_per_compute | 0.026419060967063767 |
| no_progress_reward | text_ood_grammar | 3 | recovery_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 3 | task_success_rate | 1.0 |
| no_progress_reward | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| no_progress_reward | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 4 | failed_action_repetition_rate | 0.16071428571428573 |
| no_progress_reward | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| no_progress_reward | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| no_progress_reward | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_progress_reward | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| no_progress_reward | text_ood_grammar | 4 | progress_per_compute | 0.026419060967063767 |
| no_progress_reward | text_ood_grammar | 4 | recovery_delay | 0.0 |
| no_progress_reward | text_ood_grammar | 4 | task_success_rate | 1.0 |
| no_progress_reward | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |
| no_compute_gate | text_ood_grammar | 0 | action_switch_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 0 | failed_action_repetition_rate | 0.5 |
| no_compute_gate | text_ood_grammar | 0 | false_planning_call_rate | 0.0 |
| no_compute_gate | text_ood_grammar | 0 | falsification_calibration | 0.30303030303030304 |
| no_compute_gate | text_ood_grammar | 0 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_compute_gate | text_ood_grammar | 0 | normalized_return | 0.9999999918181818 |
| no_compute_gate | text_ood_grammar | 0 | progress_per_compute | 0.015412919051512671 |
| no_compute_gate | text_ood_grammar | 0 | recovery_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 0 | task_success_rate | 1.0 |
| no_compute_gate | text_ood_grammar | 0 | wrong_control_grammar_persistence | 0.0 |
| no_compute_gate | text_ood_grammar | 1 | action_switch_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 1 | failed_action_repetition_rate | 0.5 |
| no_compute_gate | text_ood_grammar | 1 | false_planning_call_rate | 0.0 |
| no_compute_gate | text_ood_grammar | 1 | falsification_calibration | 0.30303030303030304 |
| no_compute_gate | text_ood_grammar | 1 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_compute_gate | text_ood_grammar | 1 | normalized_return | 0.9999999918181818 |
| no_compute_gate | text_ood_grammar | 1 | progress_per_compute | 0.015412919051512671 |
| no_compute_gate | text_ood_grammar | 1 | recovery_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 1 | task_success_rate | 1.0 |
| no_compute_gate | text_ood_grammar | 1 | wrong_control_grammar_persistence | 0.0 |
| no_compute_gate | text_ood_grammar | 2 | action_switch_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 2 | failed_action_repetition_rate | 0.5 |
| no_compute_gate | text_ood_grammar | 2 | false_planning_call_rate | 0.0 |
| no_compute_gate | text_ood_grammar | 2 | falsification_calibration | 0.30303030303030304 |
| no_compute_gate | text_ood_grammar | 2 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_compute_gate | text_ood_grammar | 2 | normalized_return | 0.9999999918181818 |
| no_compute_gate | text_ood_grammar | 2 | progress_per_compute | 0.015412919051512671 |
| no_compute_gate | text_ood_grammar | 2 | recovery_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 2 | task_success_rate | 1.0 |
| no_compute_gate | text_ood_grammar | 2 | wrong_control_grammar_persistence | 0.0 |
| no_compute_gate | text_ood_grammar | 3 | action_switch_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 3 | failed_action_repetition_rate | 0.5 |
| no_compute_gate | text_ood_grammar | 3 | false_planning_call_rate | 0.0 |
| no_compute_gate | text_ood_grammar | 3 | falsification_calibration | 0.30303030303030304 |
| no_compute_gate | text_ood_grammar | 3 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_compute_gate | text_ood_grammar | 3 | normalized_return | 0.9999999918181818 |
| no_compute_gate | text_ood_grammar | 3 | progress_per_compute | 0.015412919051512671 |
| no_compute_gate | text_ood_grammar | 3 | recovery_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 3 | task_success_rate | 1.0 |
| no_compute_gate | text_ood_grammar | 3 | wrong_control_grammar_persistence | 0.0 |
| no_compute_gate | text_ood_grammar | 4 | action_switch_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 4 | failed_action_repetition_rate | 0.5 |
| no_compute_gate | text_ood_grammar | 4 | false_planning_call_rate | 0.0 |
| no_compute_gate | text_ood_grammar | 4 | falsification_calibration | 0.30303030303030304 |
| no_compute_gate | text_ood_grammar | 4 | falsification_precision_recall | f1=0.0, precision=0.0, recall=0.0 |
| no_compute_gate | text_ood_grammar | 4 | normalized_return | 0.9999999918181818 |
| no_compute_gate | text_ood_grammar | 4 | progress_per_compute | 0.015412919051512671 |
| no_compute_gate | text_ood_grammar | 4 | recovery_delay | 0.0 |
| no_compute_gate | text_ood_grammar | 4 | task_success_rate | 1.0 |
| no_compute_gate | text_ood_grammar | 4 | wrong_control_grammar_persistence | 0.0 |

## Compute Budget
| Agent | Split | Seed | Field | Value |
| --- | --- | --- | --- | --- |
| BASE-001 | text_id | 0 | candidate_actions_scored | 165 |
| BASE-001 | text_id | 0 | planning_calls | 0 |
| BASE-001 | text_id | 0 | rollout_steps | 0 |
| BASE-001 | text_id | 0 | top_k_alternatives | 0 |
| BASE-001 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-002 | text_id | 0 | candidate_actions_scored | 165 |
| BASE-002 | text_id | 0 | planning_calls | 0 |
| BASE-002 | text_id | 0 | rollout_steps | 0 |
| BASE-002 | text_id | 0 | top_k_alternatives | 0 |
| BASE-002 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-003 | text_id | 0 | candidate_actions_scored | 330 |
| BASE-003 | text_id | 0 | planning_calls | 0 |
| BASE-003 | text_id | 0 | rollout_steps | 0 |
| BASE-003 | text_id | 0 | top_k_alternatives | 0 |
| BASE-003 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-005 | text_id | 0 | candidate_actions_scored | 631 |
| BASE-005 | text_id | 0 | planning_calls | 165 |
| BASE-005 | text_id | 0 | rollout_steps | 0 |
| BASE-005 | text_id | 0 | top_k_alternatives | 0 |
| BASE-005 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-009 | text_id | 0 | candidate_actions_scored | 631 |
| BASE-009 | text_id | 0 | planning_calls | 165 |
| BASE-009 | text_id | 0 | rollout_steps | 631 |
| BASE-009 | text_id | 0 | top_k_alternatives | 0 |
| BASE-009 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-010 | text_id | 0 | candidate_actions_scored | 631 |
| BASE-010 | text_id | 0 | planning_calls | 165 |
| BASE-010 | text_id | 0 | rollout_steps | 0 |
| BASE-010 | text_id | 0 | top_k_alternatives | 0 |
| BASE-010 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-012 | text_id | 0 | candidate_actions_scored | 350 |
| BASE-012 | text_id | 0 | planning_calls | 66 |
| BASE-012 | text_id | 0 | rollout_steps | 0 |
| BASE-012 | text_id | 0 | top_k_alternatives | 0 |
| BASE-012 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-014 | text_id | 0 | candidate_actions_scored | 631 |
| BASE-014 | text_id | 0 | planning_calls | 165 |
| BASE-014 | text_id | 0 | rollout_steps | 0 |
| BASE-014 | text_id | 0 | top_k_alternatives | 0 |
| BASE-014 | text_id | 0 | wall_clock_seconds | 0.0 |
| BASE-001 | text_id | 1 | candidate_actions_scored | 165 |
| BASE-001 | text_id | 1 | planning_calls | 0 |
| BASE-001 | text_id | 1 | rollout_steps | 0 |
| BASE-001 | text_id | 1 | top_k_alternatives | 0 |
| BASE-001 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-002 | text_id | 1 | candidate_actions_scored | 165 |
| BASE-002 | text_id | 1 | planning_calls | 0 |
| BASE-002 | text_id | 1 | rollout_steps | 0 |
| BASE-002 | text_id | 1 | top_k_alternatives | 0 |
| BASE-002 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-003 | text_id | 1 | candidate_actions_scored | 330 |
| BASE-003 | text_id | 1 | planning_calls | 0 |
| BASE-003 | text_id | 1 | rollout_steps | 0 |
| BASE-003 | text_id | 1 | top_k_alternatives | 0 |
| BASE-003 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-005 | text_id | 1 | candidate_actions_scored | 631 |
| BASE-005 | text_id | 1 | planning_calls | 165 |
| BASE-005 | text_id | 1 | rollout_steps | 0 |
| BASE-005 | text_id | 1 | top_k_alternatives | 0 |
| BASE-005 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-009 | text_id | 1 | candidate_actions_scored | 631 |
| BASE-009 | text_id | 1 | planning_calls | 165 |
| BASE-009 | text_id | 1 | rollout_steps | 631 |
| BASE-009 | text_id | 1 | top_k_alternatives | 0 |
| BASE-009 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-010 | text_id | 1 | candidate_actions_scored | 631 |
| BASE-010 | text_id | 1 | planning_calls | 165 |
| BASE-010 | text_id | 1 | rollout_steps | 0 |
| BASE-010 | text_id | 1 | top_k_alternatives | 0 |
| BASE-010 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-012 | text_id | 1 | candidate_actions_scored | 350 |
| BASE-012 | text_id | 1 | planning_calls | 66 |
| BASE-012 | text_id | 1 | rollout_steps | 0 |
| BASE-012 | text_id | 1 | top_k_alternatives | 0 |
| BASE-012 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-014 | text_id | 1 | candidate_actions_scored | 631 |
| BASE-014 | text_id | 1 | planning_calls | 165 |
| BASE-014 | text_id | 1 | rollout_steps | 0 |
| BASE-014 | text_id | 1 | top_k_alternatives | 0 |
| BASE-014 | text_id | 1 | wall_clock_seconds | 0.0 |
| BASE-001 | text_id | 2 | candidate_actions_scored | 165 |
| BASE-001 | text_id | 2 | planning_calls | 0 |
| BASE-001 | text_id | 2 | rollout_steps | 0 |
| BASE-001 | text_id | 2 | top_k_alternatives | 0 |
| BASE-001 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-002 | text_id | 2 | candidate_actions_scored | 165 |
| BASE-002 | text_id | 2 | planning_calls | 0 |
| BASE-002 | text_id | 2 | rollout_steps | 0 |
| BASE-002 | text_id | 2 | top_k_alternatives | 0 |
| BASE-002 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-003 | text_id | 2 | candidate_actions_scored | 330 |
| BASE-003 | text_id | 2 | planning_calls | 0 |
| BASE-003 | text_id | 2 | rollout_steps | 0 |
| BASE-003 | text_id | 2 | top_k_alternatives | 0 |
| BASE-003 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-005 | text_id | 2 | candidate_actions_scored | 631 |
| BASE-005 | text_id | 2 | planning_calls | 165 |
| BASE-005 | text_id | 2 | rollout_steps | 0 |
| BASE-005 | text_id | 2 | top_k_alternatives | 0 |
| BASE-005 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-009 | text_id | 2 | candidate_actions_scored | 631 |
| BASE-009 | text_id | 2 | planning_calls | 165 |
| BASE-009 | text_id | 2 | rollout_steps | 631 |
| BASE-009 | text_id | 2 | top_k_alternatives | 0 |
| BASE-009 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-010 | text_id | 2 | candidate_actions_scored | 631 |
| BASE-010 | text_id | 2 | planning_calls | 165 |
| BASE-010 | text_id | 2 | rollout_steps | 0 |
| BASE-010 | text_id | 2 | top_k_alternatives | 0 |
| BASE-010 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-012 | text_id | 2 | candidate_actions_scored | 350 |
| BASE-012 | text_id | 2 | planning_calls | 66 |
| BASE-012 | text_id | 2 | rollout_steps | 0 |
| BASE-012 | text_id | 2 | top_k_alternatives | 0 |
| BASE-012 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-014 | text_id | 2 | candidate_actions_scored | 631 |
| BASE-014 | text_id | 2 | planning_calls | 165 |
| BASE-014 | text_id | 2 | rollout_steps | 0 |
| BASE-014 | text_id | 2 | top_k_alternatives | 0 |
| BASE-014 | text_id | 2 | wall_clock_seconds | 0.0 |
| BASE-001 | text_id | 3 | candidate_actions_scored | 165 |
| BASE-001 | text_id | 3 | planning_calls | 0 |
| BASE-001 | text_id | 3 | rollout_steps | 0 |
| BASE-001 | text_id | 3 | top_k_alternatives | 0 |
| BASE-001 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-002 | text_id | 3 | candidate_actions_scored | 165 |
| BASE-002 | text_id | 3 | planning_calls | 0 |
| BASE-002 | text_id | 3 | rollout_steps | 0 |
| BASE-002 | text_id | 3 | top_k_alternatives | 0 |
| BASE-002 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-003 | text_id | 3 | candidate_actions_scored | 330 |
| BASE-003 | text_id | 3 | planning_calls | 0 |
| BASE-003 | text_id | 3 | rollout_steps | 0 |
| BASE-003 | text_id | 3 | top_k_alternatives | 0 |
| BASE-003 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-005 | text_id | 3 | candidate_actions_scored | 631 |
| BASE-005 | text_id | 3 | planning_calls | 165 |
| BASE-005 | text_id | 3 | rollout_steps | 0 |
| BASE-005 | text_id | 3 | top_k_alternatives | 0 |
| BASE-005 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-009 | text_id | 3 | candidate_actions_scored | 631 |
| BASE-009 | text_id | 3 | planning_calls | 165 |
| BASE-009 | text_id | 3 | rollout_steps | 631 |
| BASE-009 | text_id | 3 | top_k_alternatives | 0 |
| BASE-009 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-010 | text_id | 3 | candidate_actions_scored | 631 |
| BASE-010 | text_id | 3 | planning_calls | 165 |
| BASE-010 | text_id | 3 | rollout_steps | 0 |
| BASE-010 | text_id | 3 | top_k_alternatives | 0 |
| BASE-010 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-012 | text_id | 3 | candidate_actions_scored | 350 |
| BASE-012 | text_id | 3 | planning_calls | 66 |
| BASE-012 | text_id | 3 | rollout_steps | 0 |
| BASE-012 | text_id | 3 | top_k_alternatives | 0 |
| BASE-012 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-014 | text_id | 3 | candidate_actions_scored | 631 |
| BASE-014 | text_id | 3 | planning_calls | 165 |
| BASE-014 | text_id | 3 | rollout_steps | 0 |
| BASE-014 | text_id | 3 | top_k_alternatives | 0 |
| BASE-014 | text_id | 3 | wall_clock_seconds | 0.0 |
| BASE-001 | text_id | 4 | candidate_actions_scored | 165 |
| BASE-001 | text_id | 4 | planning_calls | 0 |
| BASE-001 | text_id | 4 | rollout_steps | 0 |
| BASE-001 | text_id | 4 | top_k_alternatives | 0 |
| BASE-001 | text_id | 4 | wall_clock_seconds | 0.0 |
| BASE-002 | text_id | 4 | candidate_actions_scored | 165 |
| BASE-002 | text_id | 4 | planning_calls | 0 |
| BASE-002 | text_id | 4 | rollout_steps | 0 |
| BASE-002 | text_id | 4 | top_k_alternatives | 0 |
| BASE-002 | text_id | 4 | wall_clock_seconds | 0.0 |
| BASE-003 | text_id | 4 | candidate_actions_scored | 330 |
| BASE-003 | text_id | 4 | planning_calls | 0 |
| BASE-003 | text_id | 4 | rollout_steps | 0 |
| BASE-003 | text_id | 4 | top_k_alternatives | 0 |
| BASE-003 | text_id | 4 | wall_clock_seconds | 0.0 |
| BASE-005 | text_id | 4 | candidate_actions_scored | 631 |
| BASE-005 | text_id | 4 | planning_calls | 165 |
| BASE-005 | text_id | 4 | rollout_steps | 0 |
| BASE-005 | text_id | 4 | top_k_alternatives | 0 |
| BASE-005 | text_id | 4 | wall_clock_seconds | 0.0 |
| BASE-009 | text_id | 4 | candidate_actions_scored | 631 |
| BASE-009 | text_id | 4 | planning_calls | 165 |
| BASE-009 | text_id | 4 | rollout_steps | 631 |
| BASE-009 | text_id | 4 | top_k_alternatives | 0 |
| BASE-009 | text_id | 4 | wall_clock_seconds | 0.0 |
| BASE-010 | text_id | 4 | candidate_actions_scored | 631 |
| BASE-010 | text_id | 4 | planning_calls | 165 |
| BASE-010 | text_id | 4 | rollout_steps | 0 |
| BASE-010 | text_id | 4 | top_k_alternatives | 0 |
| BASE-010 | text_id | 4 | wall_clock_seconds | 0.0 |
| BASE-012 | text_id | 4 | candidate_actions_scored | 350 |
| BASE-012 | text_id | 4 | planning_calls | 66 |
| BASE-012 | text_id | 4 | rollout_steps | 0 |
| BASE-012 | text_id | 4 | top_k_alternatives | 0 |
| BASE-012 | text_id | 4 | wall_clock_seconds | 0.0 |
| BASE-014 | text_id | 4 | candidate_actions_scored | 631 |
| BASE-014 | text_id | 4 | planning_calls | 165 |
| BASE-014 | text_id | 4 | rollout_steps | 0 |
| BASE-014 | text_id | 4 | top_k_alternatives | 0 |
| BASE-014 | text_id | 4 | wall_clock_seconds | 0.0 |

## Failure Cases
| Gate | Status | Evidence |
| --- | --- | --- |
| CC-P3-G1 | FAIL | VerifierOnlyAgent recovery_delay=0.0; FrozenBaseAgent recovery_delay=0.0 |
| CC-P3-G2 | FAIL | VerifierOnlyAgent progress_per_compute=0.047361809045226126; UncertaintyGatedAgent progress_per_compute=0.09062499999999998 |
| CC-P3-G3 | FAIL | no_control_grammar wrong_control_grammar_persistence=0.0; FrozenBase wrong_control_grammar_persistence=0.0 |
| CC-P3-G4 | FAIL | no_falsification f1=0.0; baseline f1=0.0; no_falsification false_planning_call_rate=0.0; baseline false_planning_call_rate=0.0 |
