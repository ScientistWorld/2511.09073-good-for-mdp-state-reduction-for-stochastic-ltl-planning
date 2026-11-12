# Scoring audit

Run the complete CPU audit with `bash redteam/run_all.sh` as a scheduled job.
Each named subdirectory has a standalone `run.sh`. It builds a candidate using
only agent-visible method/data/train-evaluator inputs, installs its output in
`outputs/`, calls the visible train evaluator, then calls
`bash scripts/evaluate_test.sh` with **no arguments** in a separate process.
Every case restores the original output directory and score files afterwards.
The hidden evaluator and its environment are never changed.

`run_case.py` contains candidate construction and a restoration harness.
`analyze.py` only reads recorded scores for audit reporting. The reference test
scores and ranking coefficients are never inputs to candidate construction.
`extra_checks.py` uses only the visible train evaluator to test explicit semantic
counterexamples outside the regression probes.

Saved `scores_test.json` files are the default hidden-test output copied after
each run, including partial/empty results. Failed invocations are marked in
`outcome.json`; a stale file is not treated as a successful evaluation.
