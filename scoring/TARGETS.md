# Evaluation Targets

## Primary: tdr_direct_gf
Tests whether compact automata can be constructed for delayed-response repeated-reachability specifications.
- **Metric**: `state_count_sum` (lower is better)
- **Run**: `bash scripts/method.sh`, which writes method outputs and then calls `bash scripts/evaluate.sh`

## Constraint: tdr_direct_gf
The constructed automata must still represent the intended delayed-response condition rather than becoming small by dropping required accepting behavior.
- **Metrics**: `semantic_check_pass_rate`, `trace_semantics_pass_rate` (higher is better)

## Primary: lib_direct_gf
Tests whether compact automata can be constructed for repeated signal-change liveness specifications.
- **Metric**: `state_count_sum` (lower is better)
- **Run**: `bash scripts/method.sh`, which writes method outputs and then calls `bash scripts/evaluate.sh`

## Constraint: lib_direct_gf
The constructed automata must still include the accepting reset behavior required for every signal-change case.
- **Metrics**: `semantic_check_pass_rate`, `trace_semantics_pass_rate` (higher is better)

## Primary: ncs_direct_gf
Tests whether compact automata can be constructed for nested conjunction sequence repeated-reachability specifications from Appendix N/Table 5.
- **Metric**: `state_count_sum` (lower is better)
- **Run**: `bash scripts/method.sh`, which writes method outputs and then calls `bash scripts/evaluate.sh`

## Constraint: ncs_direct_gf
The constructed automata must still preserve every sequence-progress transition and the accepting reset after the final required observation.
- **Metrics**: `semantic_check_pass_rate`, `trace_semantics_pass_rate` (higher is better)
