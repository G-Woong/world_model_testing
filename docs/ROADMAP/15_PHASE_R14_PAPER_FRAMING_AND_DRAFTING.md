# Phase R14 — Paper Framing and Drafting

## Goal
Draft all paper sections from real experimental artifacts (no placeholder numbers).

## Section Structure

1. **Abstract** — from 25_PAPER_TITLE_CONTRIBUTIONS.md (fill in X% and Y× from R7+R10 results)
2. **Introduction** — wrong-dynamics-hypothesis persistence; 4 sub-problems
3. **Related Work** — TD-MPC2, DreamerV3, HiP-RSSM, PLSM, ReDRAW, AdaWM, conformal-RL
   See 22_NOVELTY_AND_THREATS.md for differentiation table
4. **Method** — 3 sections: (a) base WM, (b) falsification gate, (c) CIRCA algorithm
5. **Experiments** — 4-axis metrics; 4-algorithm comparison; ablation table; baseline table
6. **Discussion** — failure modes, open questions, limitations (24_OPEN_QUESTIONS.md)
7. **Conclusion** — 5 contribution bullets from 25_PAPER_TITLE_CONTRIBUTIONS.md

## Invariants

- No placeholder numbers in any section
- All figures generated from output artifacts (no manually drawn figures)
- Every claim in text must have a corresponding row in metrics table

## Agent Team Trigger
T5 required before drafting related work and claims sections (reviewer-2-attack-agent).
Already completed: reviewer2_attack_fglc_R1.md — incorporate defenses into paper text.

## Gate Criteria
- [ ] All 7 sections drafted
- [ ] No X% placeholders in main text (all filled from experiments)
- [ ] T5 agent team review completed on related work section
- [ ] fglc-related-work-scout run on final related work section
