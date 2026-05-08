# FRCG-WM: Stop hook — response format reminder
# Fires when Claude Code finishes its response.
# Always exits 0 (non-blocking).
# Output is injected as context for the next turn, reminding Claude to use the required format.

Write-Output ""
Write-Output "[FRCG-WM] Required response format for any task-based reply:"
Write-Output ""
Write-Output "  Read:"
Write-Output "    - List MD files read this turn."
Write-Output ""
Write-Output "  Phase:"
Write-Output "    - Current phase (P0-P8) and gate status (passed / pending / blocked)."
Write-Output ""
Write-Output "  Changed/Created:"
Write-Output "    - List files modified or created."
Write-Output ""
Write-Output "  Tests/Gates:"
Write-Output "    - Tests run, tests needed, or gate status."
Write-Output ""
Write-Output "  Blockers:"
Write-Output "    - Any blockers, UNKNOWN items, or deferred actions."
Write-Output ""
Write-Output "[FRCG-WM] Research contract reminders:"
Write-Output "  - Hidden labels (true_regime, true_control_grammar, oracle_*, split_id, seed) must not appear in inference input."
Write-Output "  - Do not silently remove baselines or ablations."
Write-Output "  - Do not fabricate empirical results."
Write-Output "  - Do not skip phase gate checks."

exit 0
