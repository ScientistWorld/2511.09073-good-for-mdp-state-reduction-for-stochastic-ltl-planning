# Evaluation

## Metrics

The primary metric is automaton state count; lower is better. The packaged evaluator reports aggregate state counts over benchmark families, structural semantic check pass rate, and ultimately-periodic trace semantic pass rate to ensure smaller automata still include required accepting behavior. Runtime is intentionally not scored because wall-clock measurements vary by hardware and scheduler conditions.

## Baselines and Targets

Reference targets are taken from the paper's Table 2 for delayed-response (`TDR`) and Liberouter (`LIB`) repeated-reachability formula families, plus Appendix N/Table 5 for Nested Conjunction Sequence (`NCS`) formulas. A candidate method should produce compact automata that preserve the specified recurring finite-pattern semantics and improve over the reported reduced Owl/Slim automata where applicable.

## Evaluation Protocol

Generate an artifact containing one automaton result per benchmark formula in `data/gf_benchmarks.json`, then run `bash scripts/evaluate.sh <artifact.json>`. By default, the evaluator reads `outputs/results.json` and writes `scoring/scores.json`.
