# Evaluation Targets

All targets are measured by `bash scripts/evaluate_test.sh` (held-out) and `bash scripts/evaluate_train.sh` (visible) on every method registered in `outputs/*.method.json`. Numbers are recomputed from the returned automata.

## Primary: tdr_delayed_response
Compact automata for delayed-response recurring goals.
- **Metric**: `state_count_size_weighted_mean` (lower is better); also `state_count_per_formula`, `state_count_sum`, `transition_count_sum`.
- **Paper reference**: proposed construction 45 states over TDR[6..10]; reduced Owl 1984, reduced slim 1002.

## Constraint: tdr_delayed_response
The automata must recognise the formula's language and be good-for-MDPs.
- **Metrics**: `semantic_check_pass_rate`, `generated_trace_pass_rate`, `planning_value_agreement_rate` (higher is better; any disagreement fails the run).

## Primary: lib_signal_change
Compact automata for signal-change liveness.
- **Metric**: `state_count_size_weighted_mean` (lower is better); also `state_count_per_formula`, `state_count_sum`, `transition_count_sum`.
- **Paper reference**: proposed construction 64 states over LIB[6..9]; reduced Owl 68.

## Constraint: lib_signal_change
- **Metrics**: `semantic_check_pass_rate`, `generated_trace_pass_rate`, `planning_value_agreement_rate`.

## Primary: ncs_ordered_sequence
Compact automata for nested conjunction sequences (Appendix N).
- **Metric**: `state_count_size_weighted_mean` (lower is better); also `state_count_per_formula`, `state_count_sum`, `transition_count_sum`.
- **Paper reference**: proposed construction 60 states over the eight Table 5 rows; reduced slim 1036.

## Constraint: ncs_ordered_sequence
- **Metrics**: `semantic_check_pass_rate`, `generated_trace_pass_rate`, `planning_value_agreement_rate`.

## Primary: random_cosafety_gf
Compact automata for randomly generated recurring co-safety goals (headroom experiment; no paper numbers).
- **Metric**: `state_count_size_weighted_mean` (lower is better); also `state_count_per_formula`, `state_count_sum`, `transition_count_sum`.

## Constraint: random_cosafety_gf
- **Metrics**: `semantic_check_pass_rate`, `generated_trace_pass_rate`, `planning_value_agreement_rate`.
