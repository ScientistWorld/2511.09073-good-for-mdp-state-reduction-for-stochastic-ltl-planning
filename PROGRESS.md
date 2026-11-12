# Progress

## What Works

- `method/direct_gfm.py` implements the paper's Section 6 direct GFM construction for `GF(phi)` with `phi` co-safety:
  - it builds an NFA for `phi` from the parsed formula, using partial derivatives with NFA reduction;
  - it keeps the non-final reachable states and progress transitions;
  - it resets to the initial state on every letter, and a reset is accepting when the NFA could reach a final state.
- Methods are constructor commands registered as `outputs/<name>.method.json`. The train and test evaluators each generate their own benchmark specs, run every registered constructor, and recompute every scored number from the returned automata. `eval/` never imports `method/`.
- Correctness gates: lasso-word language probes (balanced and dense random) and planning-value agreement on evaluator-generated MDPs. Any failure gives the worst value of every metric.
- Runnable baselines: `bash scripts/baseline.sh brute_force_dba` and `bash scripts/baseline.sh weaker_dfa`.
- Hardening audit: `redteam/hardening/run_audit.sh`. Results are in `HARDENING.md`.

## Results Achieved

- Paper set (`scoring/scores.json`), matching the paper's proposed-method counts exactly:
  - TDR[6..10] `state_count_sum = 45` (Table 2);
  - LIB[6..9] `64` (Table 2);
  - NCS (8 rows) `60` (Appendix N, Table 5).
- All correctness gates pass at 1.0, for the paper, train and hidden-test suites.
- Paper-reported baselines for comparison:
  - TDR: Owl-Red 1984 and Slim-Red 1002 states;
  - LIB: Owl-Red 68 states;
  - NCS: Slim-Red 1036 states.
- CPU job `273cd0cc-ead` (iteration 11, exit 0) ran the hardening audit, regenerated paper/train/test scores and passed `python validate.py --compare`:
  - no red-team shortcut beats the reference;
  - a GF-level rewriting variant shows real headroom (LIB 55→29, RND 60→45 states on the hidden test);
  - brute-force and weaker baselines score below the reference.
- Reference scores are deterministic across `PYTHONHASHSEED` values (max difference 0.0).

## Deviations From Paper

- Only the Section 6 direct `GF(co-safety)` construction is reproduced. The general Redux pipeline (GFG co-Büchi minimisation over arbitrary GFM automata) and the stochastic planning case studies are not.
- Owl/Slim are not packaged. Their numbers are paper-reported values from `scoring/reference.json`.
- The extracted Table 5 NCS formulas are garbled. The offsets were rebuilt from the visible prefixes and the reported sizes.
- Runtime is not scored. The implementation is pure Python.
- `random_cosafety_gf` is a headroom experiment that is not in the paper.

## What Remains

- The full Redux pipeline over arbitrary GFM automata, and Table 1 families BRP, EHP, NU and LFR.
- Owl/Slim baselines rerun from source, if those tools can be packaged.

## Issues Encountered

- Spot/Owl are not available offline, so the reproduction avoids external automata tools.
- The live sandbox bind-mounts tracked `README.md` and `manifest.json` to `/dev/null`, so they show as modified locally. The committed content is unaffected.
- Running the audit locally writes audit methods into `scoring/scores_*.json` through the default-path check. `scripts/run.sh` regenerates the real score files after the audit, so always use `scripts/run.sh`, not the audit alone.
