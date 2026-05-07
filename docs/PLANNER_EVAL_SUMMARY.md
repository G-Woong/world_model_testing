# Planner Evaluation Summary

input: `outputs\planner_eval_main_summary`

## 1. Planner × Model 요약

| planner | model | n_episodes | return_mean | success_rate | completed_mean | planning_calls_mean | rollout_steps_mean | compute_normalized_return | wrong_hypothesis_persistence_mean | recovery_delay_after_change_mean | false_planning_call_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| reactive | full | 900.000 | -627.081 | 0.000 | 0.000 | 600.000 | 9.589e+03 | -0.065 | 193.820 | 24.111 | 1.000 |
| fixed_k | full | 900.000 | -615.137 | 0.000 | 0.000 | 120.000 | 1.727e+04 | -0.036 | 221.837 | 18.275 | 1.000 |
| always_plan | full | 900.000 | -600.356 | 0.000 | 0.000 | 600.000 | 4.800e+04 | -0.013 | 246.287 | 0.000 | 1.000 |
| uncertainty_gate | full | 900.000 | -624.405 | 0.000 | 0.000 | 8.352 | 1.012e+04 | -0.062 | 197.732 | 25.245 | 1.000 |
| adaptive_lookahead | full | 900.000 | -812.494 | 0.000 | 0.000 | 600.000 | 1.326e+04 | -0.062 | 40.746 | 4.934 | 1.000 |
| event_only | full | 900.000 | -622.958 | 0.000 | 0.000 | 13.288 | 1.044e+04 | -0.061 | 213.497 | 25.591 | 0.412 |
| ours_frc | full | 900.000 | -626.722 | 0.000 | 0.000 | 0.486 | 9.588e+03 | -0.065 | 193.276 | 37.872 | 0.202 |
| reactive | no_regime | 900.000 | -612.930 | 0.000 | 0.000 | 600.000 | 9.581e+03 | -0.064 | 0.000 | 0.000 | 1.000 |
| fixed_k | no_regime | 900.000 | -631.587 | 0.000 | 0.000 | 120.000 | 1.728e+04 | -0.037 | 0.000 | 0.000 | 1.000 |
| always_plan | no_regime | 900.000 | -642.704 | 0.000 | 0.012 | 600.000 | 4.800e+04 | -0.013 | 0.000 | 0.000 | 1.000 |
| uncertainty_gate | no_regime | 900.000 | -649.806 | 0.000 | 0.006 | 579.428 | 4.668e+04 | -0.014 | 0.000 | 0.000 | 1.000 |
| adaptive_lookahead | no_regime | 900.000 | -613.086 | 0.000 | 0.000 | 600.000 | 1.064e+05 | -0.006 | 0.000 | 0.000 | 1.000 |
| event_only | no_regime | 900.000 | -614.219 | 0.000 | 0.000 | 4.244 | 9.859e+03 | -0.063 | 0.000 | 0.000 | 0.403 |
| ours_frc | no_regime | 900.000 | -613.151 | 0.000 | 0.000 | 0.094 | 9.585e+03 | -0.064 | 0.000 | 0.000 | 0.066 |
| reactive | no_change_point | 900.000 | -604.912 | 0.000 | 0.000 | 600.000 | 9.590e+03 | -0.063 | 258.194 | 5.526 | 1.000 |
| fixed_k | no_change_point | 900.000 | -601.684 | 0.000 | 0.000 | 120.000 | 1.728e+04 | -0.035 | 379.902 | 51.333 | 1.000 |
| always_plan | no_change_point | 900.000 | -600.012 | 0.000 | 0.000 | 600.000 | 4.800e+04 | -0.013 | 260.711 | 0.000 | 1.000 |
| uncertainty_gate | no_change_point | 900.000 | -603.262 | 0.000 | 0.000 | 5.022 | 9.919e+03 | -0.061 | 319.592 | 0.250 | 1.000 |
| adaptive_lookahead | no_change_point | 900.000 | -815.179 | 0.000 | 0.000 | 600.000 | 1.279e+04 | -0.064 | 26.156 | 2.039 | 1.000 |
| event_only | no_change_point | 900.000 | -603.575 | 0.000 | 0.000 | 14.076 | 1.050e+04 | -0.060 | 298.477 | 0.778 | 0.801 |
| ours_frc | no_change_point | 900.000 | -604.998 | 0.000 | 0.000 | 0.000 | 9.589e+03 | -0.063 | 250.591 | 0.636 | 0.000 |


## 2. Model Ablation × Planner

| planner | model | n_episodes | return_mean | success_rate | compute_normalized_return | wrong_hypothesis_persistence_mean | recovery_delay_after_change_mean |
|---|---|---|---|---|---|---|---|
| reactive | full | 900.000 | -627.081 | 0.000 | -0.065 | 193.820 | 24.111 |
| reactive | no_regime | 900.000 | -612.930 | 0.000 | -0.064 | 0.000 | 0.000 |
| reactive | no_change_point | 900.000 | -604.912 | 0.000 | -0.063 | 258.194 | 5.526 |
| fixed_k | full | 900.000 | -615.137 | 0.000 | -0.036 | 221.837 | 18.275 |
| fixed_k | no_regime | 900.000 | -631.587 | 0.000 | -0.037 | 0.000 | 0.000 |
| fixed_k | no_change_point | 900.000 | -601.684 | 0.000 | -0.035 | 379.902 | 51.333 |
| always_plan | full | 900.000 | -600.356 | 0.000 | -0.013 | 246.287 | 0.000 |
| always_plan | no_regime | 900.000 | -642.704 | 0.000 | -0.013 | 0.000 | 0.000 |
| always_plan | no_change_point | 900.000 | -600.012 | 0.000 | -0.013 | 260.711 | 0.000 |
| uncertainty_gate | full | 900.000 | -624.405 | 0.000 | -0.062 | 197.732 | 25.245 |
| uncertainty_gate | no_regime | 900.000 | -649.806 | 0.000 | -0.014 | 0.000 | 0.000 |
| uncertainty_gate | no_change_point | 900.000 | -603.262 | 0.000 | -0.061 | 319.592 | 0.250 |
| adaptive_lookahead | full | 900.000 | -812.494 | 0.000 | -0.062 | 40.746 | 4.934 |
| adaptive_lookahead | no_regime | 900.000 | -613.086 | 0.000 | -0.006 | 0.000 | 0.000 |
| adaptive_lookahead | no_change_point | 900.000 | -815.179 | 0.000 | -0.064 | 26.156 | 2.039 |
| event_only | full | 900.000 | -622.958 | 0.000 | -0.061 | 213.497 | 25.591 |
| event_only | no_regime | 900.000 | -614.219 | 0.000 | -0.063 | 0.000 | 0.000 |
| event_only | no_change_point | 900.000 | -603.575 | 0.000 | -0.060 | 298.477 | 0.778 |
| ours_frc | full | 900.000 | -626.722 | 0.000 | -0.065 | 193.276 | 37.872 |
| ours_frc | no_regime | 900.000 | -613.151 | 0.000 | -0.064 | 0.000 | 0.000 |
| ours_frc | no_change_point | 900.000 | -604.998 | 0.000 | -0.063 | 250.591 | 0.636 |


## 3. OOD breakdown

| split | planner | model | n_episodes | return_mean | return_ci_lo | return_ci_hi | success_rate | compute_normalized_return |
|---|---|---|---|---|---|---|---|---|
| test_id | reactive | full | 150.000 | -625.120 | -628.684 | -621.660 | 0.000 | -0.065 |
| test_id | fixed_k | full | 150.000 | -614.985 | -617.657 | -612.370 | 0.000 | -0.036 |
| test_id | always_plan | full | 150.000 | -600.260 | -600.559 | -600.028 | 0.000 | -0.013 |
| test_id | uncertainty_gate | full | 150.000 | -626.717 | -630.506 | -623.168 | 0.000 | -0.062 |
| test_id | adaptive_lookahead | full | 150.000 | -813.223 | -815.882 | -810.777 | 0.000 | -0.062 |
| test_id | event_only | full | 150.000 | -621.903 | -624.794 | -619.051 | 0.000 | -0.061 |
| test_id | ours_frc | full | 150.000 | -625.798 | -629.478 | -622.376 | 0.000 | -0.065 |
| ood_room_perm | reactive | full | 150.000 | -625.627 | -629.537 | -622.125 | 0.000 | -0.065 |
| ood_room_perm | fixed_k | full | 150.000 | -615.027 | -617.542 | -612.729 | 0.000 | -0.036 |
| ood_room_perm | always_plan | full | 150.000 | -600.453 | -600.982 | -600.080 | 0.000 | -0.013 |
| ood_room_perm | uncertainty_gate | full | 150.000 | -623.280 | -626.501 | -619.970 | 0.000 | -0.062 |
| ood_room_perm | adaptive_lookahead | full | 150.000 | -813.055 | -815.703 | -810.475 | 0.000 | -0.062 |
| ood_room_perm | event_only | full | 150.000 | -623.405 | -626.896 | -619.903 | 0.000 | -0.061 |
| ood_room_perm | ours_frc | full | 150.000 | -628.042 | -632.298 | -624.146 | 0.000 | -0.066 |
| ood_factor_recomb | reactive | full | 150.000 | -627.537 | -631.678 | -623.580 | 0.000 | -0.066 |
| ood_factor_recomb | fixed_k | full | 150.000 | -614.778 | -617.700 | -611.955 | 0.000 | -0.036 |
| ood_factor_recomb | always_plan | full | 150.000 | -600.290 | -600.667 | -600.032 | 0.000 | -0.013 |
| ood_factor_recomb | uncertainty_gate | full | 150.000 | -623.967 | -627.530 | -620.374 | 0.000 | -0.062 |
| ood_factor_recomb | adaptive_lookahead | full | 150.000 | -810.012 | -813.993 | -805.833 | 0.000 | -0.062 |
| ood_factor_recomb | event_only | full | 150.000 | -624.480 | -628.252 | -621.000 | 0.000 | -0.062 |
| ood_factor_recomb | ours_frc | full | 150.000 | -625.697 | -629.418 | -622.464 | 0.000 | -0.065 |
| ood_param_shift | reactive | full | 150.000 | -630.573 | -634.496 | -626.969 | 0.000 | -0.066 |
| ood_param_shift | fixed_k | full | 150.000 | -615.268 | -618.086 | -612.533 | 0.000 | -0.036 |
| ood_param_shift | always_plan | full | 150.000 | -600.377 | -600.819 | -600.025 | 0.000 | -0.013 |
| ood_param_shift | uncertainty_gate | full | 150.000 | -624.140 | -627.574 | -620.943 | 0.000 | -0.062 |
| ood_param_shift | adaptive_lookahead | full | 150.000 | -809.558 | -812.572 | -806.440 | 0.000 | -0.062 |
| ood_param_shift | event_only | full | 150.000 | -622.023 | -624.989 | -619.354 | 0.000 | -0.061 |
| ood_param_shift | ours_frc | full | 150.000 | -626.157 | -630.110 | -622.483 | 0.000 | -0.065 |
| ood_obs_shift | reactive | full | 150.000 | -627.597 | -631.413 | -624.307 | 0.000 | -0.065 |
| ood_obs_shift | fixed_k | full | 150.000 | -616.940 | -620.397 | -613.890 | 0.000 | -0.036 |
| ood_obs_shift | always_plan | full | 150.000 | -600.528 | -601.030 | -600.135 | 0.000 | -0.013 |
| ood_obs_shift | uncertainty_gate | full | 150.000 | -622.903 | -626.383 | -619.942 | 0.000 | -0.062 |
| ood_obs_shift | adaptive_lookahead | full | 150.000 | -814.843 | -818.577 | -810.623 | 0.000 | -0.062 |
| ood_obs_shift | event_only | full | 150.000 | -622.882 | -626.205 | -619.431 | 0.000 | -0.062 |
| ood_obs_shift | ours_frc | full | 150.000 | -628.037 | -631.688 | -624.895 | 0.000 | -0.065 |
| ood_field_placement | reactive | full | 150.000 | -626.035 | -629.372 | -622.725 | 0.000 | -0.065 |
| ood_field_placement | fixed_k | full | 150.000 | -613.823 | -615.932 | -611.658 | 0.000 | -0.036 |
| ood_field_placement | always_plan | full | 150.000 | -600.227 | -600.492 | -600.048 | 0.000 | -0.013 |
| ood_field_placement | uncertainty_gate | full | 150.000 | -625.425 | -629.461 | -621.660 | 0.000 | -0.063 |
| ood_field_placement | adaptive_lookahead | full | 150.000 | -814.273 | -817.055 | -811.618 | 0.000 | -0.062 |
| ood_field_placement | event_only | full | 150.000 | -623.057 | -626.183 | -620.110 | 0.000 | -0.062 |
| ood_field_placement | ours_frc | full | 150.000 | -626.603 | -630.904 | -622.533 | 0.000 | -0.065 |
| test_id | reactive | no_regime | 150.000 | -612.062 | -613.285 | -610.705 | 0.000 | -0.064 |
| test_id | fixed_k | no_regime | 150.000 | -628.867 | -631.090 | -626.698 | 0.000 | -0.036 |
| test_id | always_plan | no_regime | 150.000 | -639.308 | -644.771 | -634.316 | 0.000 | -0.013 |
| test_id | uncertainty_gate | no_regime | 150.000 | -649.798 | -655.188 | -644.269 | 0.000 | -0.014 |
| test_id | adaptive_lookahead | no_regime | 150.000 | -613.007 | -615.450 | -610.701 | 0.000 | -0.006 |
| test_id | event_only | no_regime | 150.000 | -612.858 | -614.358 | -611.515 | 0.000 | -0.063 |
| test_id | ours_frc | no_regime | 150.000 | -611.313 | -612.730 | -610.160 | 0.000 | -0.064 |
| ood_room_perm | reactive | no_regime | 150.000 | -612.163 | -613.539 | -610.918 | 0.000 | -0.064 |
| ood_room_perm | fixed_k | no_regime | 150.000 | -631.687 | -634.251 | -629.068 | 0.000 | -0.037 |
| ood_room_perm | always_plan | no_regime | 150.000 | -642.828 | -647.512 | -637.857 | 0.000 | -0.013 |
| ood_room_perm | uncertainty_gate | no_regime | 150.000 | -647.418 | -652.917 | -642.141 | 0.000 | -0.014 |
| ood_room_perm | adaptive_lookahead | no_regime | 150.000 | -612.225 | -614.220 | -610.160 | 0.000 | -0.006 |
| ood_room_perm | event_only | no_regime | 150.000 | -613.770 | -615.665 | -612.086 | 0.000 | -0.063 |
| ood_room_perm | ours_frc | no_regime | 150.000 | -612.747 | -614.062 | -611.451 | 0.000 | -0.064 |
| ood_factor_recomb | reactive | no_regime | 150.000 | -613.190 | -615.346 | -611.420 | 0.000 | -0.064 |
| ood_factor_recomb | fixed_k | no_regime | 150.000 | -631.505 | -633.805 | -629.190 | 0.000 | -0.037 |
| ood_factor_recomb | always_plan | no_regime | 150.000 | -642.127 | -647.207 | -636.806 | 0.000 | -0.013 |
| ood_factor_recomb | uncertainty_gate | no_regime | 150.000 | -653.155 | -658.589 | -647.568 | 0.000 | -0.014 |
| ood_factor_recomb | adaptive_lookahead | no_regime | 150.000 | -612.830 | -614.920 | -610.786 | 0.000 | -0.006 |
| ood_factor_recomb | event_only | no_regime | 150.000 | -614.650 | -616.247 | -613.013 | 0.000 | -0.063 |
| ood_factor_recomb | ours_frc | no_regime | 150.000 | -614.190 | -615.597 | -612.770 | 0.000 | -0.064 |
| ood_param_shift | reactive | no_regime | 150.000 | -612.930 | -614.837 | -611.345 | 0.000 | -0.064 |
| ood_param_shift | fixed_k | no_regime | 150.000 | -632.350 | -634.547 | -630.170 | 0.000 | -0.037 |
| ood_param_shift | always_plan | no_regime | 150.000 | -640.538 | -645.854 | -635.212 | 0.000 | -0.013 |
| ood_param_shift | uncertainty_gate | no_regime | 150.000 | -652.307 | -657.399 | -646.858 | 0.000 | -0.014 |
| ood_param_shift | adaptive_lookahead | no_regime | 150.000 | -612.393 | -614.589 | -610.403 | 0.000 | -0.006 |
| ood_param_shift | event_only | no_regime | 150.000 | -615.055 | -617.095 | -613.114 | 0.000 | -0.063 |
| ood_param_shift | ours_frc | no_regime | 150.000 | -612.463 | -614.200 | -610.883 | 0.000 | -0.064 |
| ood_obs_shift | reactive | no_regime | 150.000 | -613.807 | -615.569 | -612.068 | 0.000 | -0.064 |
| ood_obs_shift | fixed_k | no_regime | 150.000 | -633.462 | -635.916 | -631.043 | 0.000 | -0.037 |
| ood_obs_shift | always_plan | no_regime | 150.000 | -642.855 | -648.385 | -637.126 | 0.000 | -0.013 |
| ood_obs_shift | uncertainty_gate | no_regime | 150.000 | -645.662 | -651.061 | -639.802 | 0.000 | -0.014 |
| ood_obs_shift | adaptive_lookahead | no_regime | 150.000 | -613.855 | -615.997 | -611.852 | 0.000 | -0.006 |
| ood_obs_shift | event_only | no_regime | 150.000 | -615.110 | -617.372 | -613.215 | 0.000 | -0.063 |
| ood_obs_shift | ours_frc | no_regime | 150.000 | -614.437 | -616.147 | -612.852 | 0.000 | -0.064 |
| ood_field_placement | reactive | no_regime | 150.000 | -613.428 | -615.229 | -611.776 | 0.000 | -0.064 |
| ood_field_placement | fixed_k | no_regime | 150.000 | -631.650 | -634.029 | -629.477 | 0.000 | -0.037 |
| ood_field_placement | always_plan | no_regime | 150.000 | -648.565 | -653.970 | -642.675 | 0.000 | -0.014 |
| ood_field_placement | uncertainty_gate | no_regime | 150.000 | -650.495 | -655.852 | -644.840 | 0.000 | -0.014 |
| ood_field_placement | adaptive_lookahead | no_regime | 150.000 | -614.207 | -616.718 | -611.948 | 0.000 | -0.006 |
| ood_field_placement | event_only | no_regime | 150.000 | -613.870 | -615.883 | -612.060 | 0.000 | -0.063 |
| ood_field_placement | ours_frc | no_regime | 150.000 | -613.757 | -615.304 | -612.211 | 0.000 | -0.064 |
| test_id | reactive | no_change_point | 150.000 | -605.423 | -607.009 | -604.193 | 0.000 | -0.063 |
| test_id | fixed_k | no_change_point | 150.000 | -601.378 | -601.910 | -600.992 | 0.000 | -0.035 |
| test_id | always_plan | no_change_point | 150.000 | -600.013 | -600.023 | -600.003 | 0.000 | -0.013 |
| test_id | uncertainty_gate | no_change_point | 150.000 | -603.303 | -604.293 | -602.458 | 0.000 | -0.061 |
| test_id | adaptive_lookahead | no_change_point | 150.000 | -822.685 | -826.192 | -818.401 | 0.000 | -0.065 |
| test_id | event_only | no_change_point | 150.000 | -603.542 | -604.360 | -602.805 | 0.000 | -0.060 |
| test_id | ours_frc | no_change_point | 150.000 | -605.345 | -606.690 | -604.133 | 0.000 | -0.063 |
| ood_room_perm | reactive | no_change_point | 150.000 | -604.437 | -605.405 | -603.598 | 0.000 | -0.063 |
| ood_room_perm | fixed_k | no_change_point | 150.000 | -601.728 | -602.461 | -601.187 | 0.000 | -0.035 |
| ood_room_perm | always_plan | no_change_point | 150.000 | -600.017 | -600.030 | -600.007 | 0.000 | -0.013 |
| ood_room_perm | uncertainty_gate | no_change_point | 150.000 | -603.325 | -604.482 | -602.343 | 0.000 | -0.061 |
| ood_room_perm | adaptive_lookahead | no_change_point | 150.000 | -812.845 | -817.652 | -808.047 | 0.000 | -0.064 |
| ood_room_perm | event_only | no_change_point | 150.000 | -604.825 | -606.400 | -603.477 | 0.000 | -0.060 |
| ood_room_perm | ours_frc | no_change_point | 150.000 | -604.775 | -605.923 | -603.772 | 0.000 | -0.063 |
| ood_factor_recomb | reactive | no_change_point | 150.000 | -604.737 | -606.202 | -603.538 | 0.000 | -0.063 |
| ood_factor_recomb | fixed_k | no_change_point | 150.000 | -601.600 | -602.143 | -601.120 | 0.000 | -0.035 |
| ood_factor_recomb | always_plan | no_change_point | 150.000 | -600.010 | -600.018 | -600.003 | 0.000 | -0.013 |
| ood_factor_recomb | uncertainty_gate | no_change_point | 150.000 | -602.880 | -603.668 | -602.198 | 0.000 | -0.061 |
| ood_factor_recomb | adaptive_lookahead | no_change_point | 150.000 | -817.558 | -822.182 | -812.245 | 0.000 | -0.064 |
| ood_factor_recomb | event_only | no_change_point | 150.000 | -603.145 | -603.800 | -602.595 | 0.000 | -0.060 |
| ood_factor_recomb | ours_frc | no_change_point | 150.000 | -604.857 | -605.927 | -603.920 | 0.000 | -0.063 |
| ood_param_shift | reactive | no_change_point | 150.000 | -605.115 | -606.354 | -603.995 | 0.000 | -0.063 |
| ood_param_shift | fixed_k | no_change_point | 150.000 | -601.318 | -601.795 | -600.893 | 0.000 | -0.035 |
| ood_param_shift | always_plan | no_change_point | 150.000 | -600.013 | -600.025 | -600.003 | 0.000 | -0.013 |
| ood_param_shift | uncertainty_gate | no_change_point | 150.000 | -603.015 | -603.937 | -602.261 | 0.000 | -0.061 |
| ood_param_shift | adaptive_lookahead | no_change_point | 150.000 | -811.430 | -815.613 | -806.854 | 0.000 | -0.063 |
| ood_param_shift | event_only | no_change_point | 150.000 | -603.343 | -604.260 | -602.573 | 0.000 | -0.060 |
| ood_param_shift | ours_frc | no_change_point | 150.000 | -604.678 | -606.049 | -603.593 | 0.000 | -0.063 |
| ood_obs_shift | reactive | no_change_point | 150.000 | -605.633 | -607.059 | -604.536 | 0.000 | -0.063 |
| ood_obs_shift | fixed_k | no_change_point | 150.000 | -602.413 | -603.843 | -601.347 | 0.000 | -0.035 |
| ood_obs_shift | always_plan | no_change_point | 150.000 | -600.008 | -600.017 | -600.002 | 0.000 | -0.013 |
| ood_obs_shift | uncertainty_gate | no_change_point | 150.000 | -603.657 | -604.709 | -602.797 | 0.000 | -0.061 |
| ood_obs_shift | adaptive_lookahead | no_change_point | 150.000 | -813.742 | -818.393 | -808.834 | 0.000 | -0.064 |
| ood_obs_shift | event_only | no_change_point | 150.000 | -603.565 | -604.887 | -602.478 | 0.000 | -0.061 |
| ood_obs_shift | ours_frc | no_change_point | 150.000 | -605.455 | -606.856 | -604.290 | 0.000 | -0.063 |
| ood_field_placement | reactive | no_change_point | 150.000 | -604.128 | -605.073 | -603.355 | 0.000 | -0.063 |
| ood_field_placement | fixed_k | no_change_point | 150.000 | -601.668 | -602.395 | -601.062 | 0.000 | -0.035 |
| ood_field_placement | always_plan | no_change_point | 150.000 | -600.008 | -600.017 | -600.002 | 0.000 | -0.013 |
| ood_field_placement | uncertainty_gate | no_change_point | 150.000 | -603.393 | -604.287 | -602.608 | 0.000 | -0.061 |
| ood_field_placement | adaptive_lookahead | no_change_point | 150.000 | -812.815 | -818.539 | -806.704 | 0.000 | -0.064 |
| ood_field_placement | event_only | no_change_point | 150.000 | -603.030 | -603.910 | -602.295 | 0.000 | -0.060 |
| ood_field_placement | ours_frc | no_change_point | 150.000 | -604.878 | -606.030 | -603.971 | 0.000 | -0.063 |


## 4. Compute frontier

| planner | model | return_mean | planning_calls_mean | rollout_steps_mean | return_per_1k_rollout_steps | compute_normalized_return |
|---|---|---|---|---|---|---|
| reactive | full | -627.081 | 600.000 | 9.589e+03 | -65.394 | -0.065 |
| fixed_k | full | -615.137 | 120.000 | 1.727e+04 | -35.628 | -0.036 |
| always_plan | full | -600.356 | 600.000 | 4.800e+04 | -12.507 | -0.013 |
| uncertainty_gate | full | -624.405 | 8.352 | 1.012e+04 | -61.685 | -0.062 |
| adaptive_lookahead | full | -812.494 | 600.000 | 1.326e+04 | -61.294 | -0.062 |
| event_only | full | -622.958 | 13.288 | 1.044e+04 | -59.655 | -0.061 |
| ours_frc | full | -626.722 | 0.486 | 9.588e+03 | -65.365 | -0.065 |
| reactive | no_regime | -612.930 | 600.000 | 9.581e+03 | -63.977 | -0.064 |
| fixed_k | no_regime | -631.587 | 120.000 | 1.728e+04 | -36.553 | -0.037 |
| always_plan | no_regime | -642.704 | 600.000 | 4.800e+04 | -13.390 | -0.013 |
| uncertainty_gate | no_regime | -649.806 | 579.428 | 4.668e+04 | -13.919 | -0.014 |
| adaptive_lookahead | no_regime | -613.086 | 600.000 | 1.064e+05 | -5.760 | -0.006 |
| event_only | no_regime | -614.219 | 4.244 | 9.859e+03 | -62.299 | -0.063 |
| ours_frc | no_regime | -613.151 | 0.094 | 9.585e+03 | -63.967 | -0.064 |
| reactive | no_change_point | -604.912 | 600.000 | 9.590e+03 | -63.080 | -0.063 |
| fixed_k | no_change_point | -601.684 | 120.000 | 1.728e+04 | -34.820 | -0.035 |
| always_plan | no_change_point | -600.012 | 600.000 | 4.800e+04 | -12.500 | -0.013 |
| uncertainty_gate | no_change_point | -603.262 | 5.022 | 9.919e+03 | -60.818 | -0.061 |
| adaptive_lookahead | no_change_point | -815.179 | 600.000 | 1.279e+04 | -63.713 | -0.064 |
| event_only | no_change_point | -603.575 | 14.076 | 1.050e+04 | -57.505 | -0.060 |
| ours_frc | no_change_point | -604.998 | 0.000 | 9.589e+03 | -63.094 | -0.063 |


## 5. 해석 가이드

- 같은 planner를 model variant 간 비교: `full > no_regime` (특히 control-drift OOD에서)
- Ours(`ours_frc`) vs `always_plan`: compute_normalized_return에서 우위해야 함
- Ours vs `fixed_k`/`uncertainty_gate`/`adaptive_lookahead`: WHPT 감소 + recovery delay 감소
- `event_only` vs Ours: small drift OOD에서 Ours가 더 나아야 함
- 결과가 안 좋으면 paper-main 주장을 약화하거나 ablation으로 위치 조정 필요 (정직하게)
