# Train/Test Evaluation Design Notes

## Checks Performed

- Compared `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh`: train calls `eval/train/evaluate_gf.py` and writes `scoring/scores_train.json`; test calls `eval/test/evaluate_gf.py` and writes `scoring/scores_test.json`.
- Checked that both scripts discover method artifacts through the evaluator input path rather than hardcoding a method name.
- Checked that train/test evaluators read method-produced JSON artifacts and do not regenerate the method inline.
- Grepped for train/test cross-imports inside `eval/train/` and `eval/test/`; none were found.
- Confirmed that no `scoring/scores_train.json` or `scoring/scores_test.json` stub exists.
- Ran `bash -n` on both train/test evaluation scripts.

## Changes Made

- Added `generated_trace_pass_rate` to both slices. It evaluates each generated automaton on deterministic pseudo-random periodic words, using different seeds for train and held-out test. This makes shortcut methods that memorize the visible curated traces more likely to separate from methods that implement the actual automaton semantics.
- Added `transition_count_sum` to both slices. This penalizes oversized transition-enumerating automata that may pass trace checks without improving the compact construction objective.
- Updated `scoring/reference.json` so every nonzero metric has `higher_is_better`, `coefficient`, and `description`.
- Reweighted trace metrics slightly: canonical trace agreement remains visible, but the broader generated trace agreement receives higher weight because it better probes semantic generalization.

## Runtime Concerns For Next Iteration

- `jq` was not installed in this environment, so JSON syntax was inspected by reading rather than by a JSON parser.
- The top-level legacy evaluator `eval/evaluate_gf.py` still contains the original combined benchmark scoring path used by `scripts/evaluate.sh`. It was outside this iteration's allowed edit scope, but future hiding/packaging should ensure a scientist agent only sees `eval/train/` and not held-out test shape through legacy top-level files.
- The generated trace metric is deterministic and lightweight, but the runner should confirm it does not saturate for trivial always-accepting or always-rejecting automata.
