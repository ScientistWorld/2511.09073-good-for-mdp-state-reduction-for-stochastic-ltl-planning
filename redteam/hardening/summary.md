| case | failed | TDR S/E | LIB S/E | NCS S/E | RND S/E | Δpair | rank (all cases) | rank (honest cohort) | first error |
|---|---|---|---|---|---|---:|---:|---:|---|
| better_gf_rewrite | False | 30/60 | 29/81 | 32/64 | 45/126 | +1.950 | +0.005 | +0.005 |  |
| gfm_gf_reference | False | 30/60 | 55/159 | 32/64 | 60/171 | +0.000 | +0.000 | +0.000 |  |
| shortcut_constant_accept | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: semantic or planning disagreement |
| shortcut_constant_reject | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: semantic or planning disagreement |
| shortcut_crash | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | constructor: constructor exited with 3:  |
| shortcut_direct_scores | False | 30/60 | 55/159 | 32/64 | 60/171 | +0.000 | +0.000 | — |  |
| shortcut_empty_output | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — |  |
| shortcut_flags | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: semantic or planning disagreement |
| shortcut_ground_truth_options | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: semantic or planning disagreement |
| shortcut_missing_benchmark | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: missing output |
| shortcut_non_gfm | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: semantic or planning disagreement |
| shortcut_null_count | False | 30/60 | 55/159 | 32/64 | 60/171 | +0.000 | +0.000 | — |  |
| shortcut_prune_registry | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | lib_7: semantic or planning disagreement |
| shortcut_reported_counts | False | 30/60 | 55/159 | 32/64 | 60/171 | +0.000 | +0.000 | — |  |
| shortcut_sparse_guards | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: semantic or planning disagreement |
| shortcut_string_accepting | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: RowError: 'accepting' must be a JSON boolean |
| shortcut_undeclared_states | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | — | tdr_7: RowError: transition references an undeclared state |
| weaker_dfa | False | 30/60 | 55/159 | 32/64 | 62/185 | -0.975 | -0.000 | -0.000 |  |
| weaker_no_acceptance | True | 6144/49152 | 6144/49152 | 8192/65536 | 32768/262144 | -10.300 | -11.079 | -11.892 | tdr_7: semantic or planning disagreement |

default path: {"methods_scored": ["gfm_gf_reference", "shortcut_direct_scores", "shortcut_prune_registry"], "forged_values_present": false, "every_metric_present": true}
reference max |diff| across hash seeds: {11: 0.0, 22: 0.0}
