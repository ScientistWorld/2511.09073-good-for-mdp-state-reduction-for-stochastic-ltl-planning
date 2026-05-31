# Progress

## What Works

- Implemented the paper's Section 6 direct GFM construction for formulas `GF phi` where `phi` is a co-safety finite-trace property.
- Added concrete NFA builders for the Table 2 TDR and LIB benchmark families.
- Added a method script that writes generated automata to `outputs/gfm_gf_results.json`.
- Added an independent evaluator that reads the method artifact and writes `scoring/scores.json`.
- Audited the reproduction and confirmed that the method code follows the paper's reset construction rather than a learned or hardcoded surrogate.

## Results Achieved

- TDR[6-10] reproduced proposed state counts exactly: aggregate `state_count_sum = 45`.
- LIB[6-9] reproduced proposed state counts exactly: aggregate `state_count_sum = 64`.
- Semantic check pass rate is `1.0` for both experiments.
- Container job `1707ed70-62d` completed successfully with exit code 0 and reran `scripts/reproduce.sh` plus `python validate.py --compare`.

## Deviations From Paper

- This reproduction targets the paper's direct `GF phi` construction rather than the full general Redux pipeline with Spot-based GFG minimisation.
- Runtime numbers are not expected to match the paper because this implementation uses a lightweight pure-Python construction for the selected benchmark families.

## What Remains

- Implement the full general state-reduction pipeline over arbitrary GFM automata.
- Add Owl/Slim generation and reduction baselines if Spot/Owl are packaged in a future iteration.
- Extend evaluation to BRP, EHP, NU, and LFR from Table 1.
- Higher milestones would require the full Redux pipeline or additional appendix experiments; this environment now satisfies the core direct-construction claim.

## Issues Encountered

- The login environment does not provide the Spot Python bindings, so the core reproduction avoids external automata dependencies and focuses on the explicit construction that can be implemented directly from the paper.
- A documentation sentence still mentioned runtime scoring after the evaluator had already removed it; corrected `briefing/evaluation.md` so the docs match the scoring contract.
