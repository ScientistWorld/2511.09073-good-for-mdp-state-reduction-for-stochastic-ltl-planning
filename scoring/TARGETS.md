# Evaluation Targets

## Primary: tdr_delayed_response
Tests whether compact automata can be constructed for delayed-response repeated-reachability specifications.
- **Metric**: `state_count_size_weighted_mean` (lower is better)
- **Run**: `bash scripts/method.sh`, which writes method outputs and then calls `bash scripts/evaluate.sh`

## Constraint: tdr_delayed_response
The constructed automata must still represent the intended delayed-response condition rather than becoming small by dropping required accepting behavior.
- **Metrics**: `semantic_check_pass_rate`, `trace_semantics_pass_rate` (higher is better)

## Primary: lib_signal_change
Tests whether compact automata can be constructed for repeated signal-change liveness specifications.
- **Metric**: `state_count_size_weighted_mean` (lower is better)
- **Run**: `bash scripts/method.sh`, which writes method outputs and then calls `bash scripts/evaluate.sh`

## Constraint: lib_signal_change
The constructed automata must still accept recurring signal changes and reject traces where monitored signals remain fixed.
- **Metrics**: `semantic_check_pass_rate`, `trace_semantics_pass_rate` (higher is better)

## Primary: ncs_ordered_sequence
Tests whether compact automata can be constructed for nested conjunction sequence repeated-reachability specifications from Appendix N/Table 5.
- **Metric**: `state_count_size_weighted_mean` (lower is better)
- **Run**: `bash scripts/method.sh`, which writes method outputs and then calls `bash scripts/evaluate.sh`

## Constraint: ncs_ordered_sequence
The constructed automata must still accept recurring ordered observation sequences and reject traces that omit or misorder required observations.
- **Metrics**: `semantic_check_pass_rate`, `trace_semantics_pass_rate` (higher is better)
