# Evaluation

## Metrics

The primary metric is automaton state count; lower is better. The packaged evaluator reports aggregate state counts over benchmark families, structural semantic check pass rate, and ultimately-periodic trace semantic pass rate to ensure smaller automata still include required accepting behavior. Runtime is intentionally not scored because wall-clock measurements vary by hardware and scheduler conditions.

## Baselines and Targets

Reference targets are taken from the paper's Table 2 for delayed-response (`TDR`) and Liberouter (`LIB`) repeated-reachability formula families, plus Appendix N/Table 5 for Nested Conjunction Sequence (`NCS`) formulas. The target method should match the proposed construction's state counts and improve over the reported reduced Owl/Slim automata where applicable.

## Evaluation Protocol

Run `bash scripts/method.sh` to generate automata for all benchmark formulas in `data/gf_benchmarks.json` and evaluate them. `scripts/evaluate.sh` reads `outputs/gfm_gf_results.json` and writes `scoring/scores.json`.
