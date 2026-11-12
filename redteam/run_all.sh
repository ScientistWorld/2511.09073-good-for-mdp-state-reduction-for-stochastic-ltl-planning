#!/bin/bash
set -euo pipefail
cd /home/user
for name in reference_seed11 reference_seed22 reference_seed33 better_lib_falling weaker_no_acceptance shortcut_reported_counts shortcut_ground_truth_options shortcut_non_gfm shortcut_sparse_guards shortcut_prune_registry shortcut_direct_scores shortcut_flags shortcut_constant_accept shortcut_constant_reject shortcut_missing_benchmark shortcut_null_count shortcut_empty_output brute_force_history; do
    bash "redteam/$name/run.sh"
done
python redteam/extra_checks.py
python redteam/analyze.py
python redteam/reproduction_check.py
