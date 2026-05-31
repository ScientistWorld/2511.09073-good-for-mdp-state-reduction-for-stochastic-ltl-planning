# Progress

## What Works

- Implemented the paper's Section 6 direct GFM construction for formulas `GF phi` where `phi` is a co-safety finite-trace property.
- Added concrete NFA builders for the Table 2 TDR and LIB benchmark families.
- Added a method script that writes generated automata to `outputs/results.json`.
- Added an independent evaluator that reads the method artifact and writes `scoring/scores.json`.
- Audited the reproduction and confirmed that the method code follows the paper's reset construction rather than a learned or hardcoded surrogate.
- Tightened the generated reset transitions so final-reaching letters have the accepting reset transition prescribed by the paper instead of a parallel non-accepting duplicate reset.
- Added method-independent ultimately-periodic trace checks to the evaluator so candidate automata must accept representative satisfying traces and reject matched violating traces.

## Results Achieved

- TDR[6-10] reproduced proposed state counts exactly: aggregate `state_count_sum = 45`.
- LIB[6-9] reproduced proposed state counts exactly: aggregate `state_count_sum = 64`.
- NCS[4-11] from Appendix N/Table 5 reproduced proposed state counts exactly: aggregate `state_count_sum = 60`.
- Semantic check pass rate is `1.0` for all three experiments.
- Trace semantic pass rate is `1.0` for all three experiments.
- Continuation audit on 2026-05-31 reran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python compilation successfully.
- Container job `1707ed70-62d` completed successfully with exit code 0 and reran `scripts/reproduce.sh` plus `python validate.py --compare`.
- Container job `d5313962-fe4` completed successfully with exit code 0 and validated the extended TDR, LIB, and NCS scoring suite inside the packaged environment.
- Updated `scripts/run.sh` so submitted jobs regenerate `outputs/results.json` before full/train/test evaluation instead of relying on existing local artifacts.
- Local 2026-05-31 rerun of `scripts/run.sh`, `python validate.py --compare`, and Python bytecode compilation passed after the run-script change.

## Deviations From Paper

- This reproduction targets the paper's direct `GF phi` construction rather than the full general Redux pipeline with Spot-based GFG minimisation.
- The direct construction is implemented for the benchmark NFA families TDR, LIB, and NCS rather than for an arbitrary parsed co-safety LTL formula.
- Runtime numbers are not expected to match the paper because this implementation uses a lightweight pure-Python construction for the selected benchmark families.

## What Remains

- Implement the full general state-reduction pipeline over arbitrary GFM automata.
- Add Owl/Slim generation and reduction baselines if Spot/Owl are packaged in a future iteration.
- Extend evaluation to BRP, EHP, NU, and LFR from Table 1.
- Higher milestones would require the full Redux pipeline or additional appendix experiments; this environment now satisfies the core direct-construction claim.

## Issues Encountered

- The login environment does not provide the Spot Python bindings, so the core reproduction avoids external automata dependencies and focuses on the explicit construction that can be implemented directly from the paper.
- A documentation sentence still mentioned runtime scoring after the evaluator had already removed it; corrected `briefing/evaluation.md` so the docs match the scoring contract.
- `reference.json` originally listed evaluator-only semantic pass targets as if they were paper-reported values; removed those result values while keeping the metrics as reproduced correctness constraints.
