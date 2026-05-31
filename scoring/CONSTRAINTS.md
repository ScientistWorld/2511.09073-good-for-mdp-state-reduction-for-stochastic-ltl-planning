# Scientist Constraints

## Benchmark Set
Use only the benchmark specifications in `data/gf_benchmarks.json` for reported scores. Adding easier formulas or removing harder rows would change the benchmark rather than improve the construction.

## Output Contract
Method code must write `outputs/gfm_gf_results.json` with one entry per benchmark and must report actual generated automata, not only aggregate counts. The evaluator intentionally checks transition structure so that state counts cannot be reduced by omitting acceptance behavior.

## Metrics
Scores must be computed by `scripts/evaluate.sh` from generated method artifacts. Do not edit `eval/evaluate_gf.py` or `scoring/reference.json` when submitting an improved method, except to add clearly separate new experiments.

## Compliance Checklist
- [ ] All benchmark names from `data/gf_benchmarks.json` are present in the method output
- [ ] Generated automata include states, initial state, transitions, and accepting flags
- [ ] `scripts/evaluate.sh` is used to produce `scoring/scores.json`
- [ ] No benchmark rows are removed or replaced for the reported experiments
