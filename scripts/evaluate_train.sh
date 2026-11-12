#!/bin/bash
# Train-slice evaluation (visible instances). Same interface as the hidden test:
# every outputs/*.method.json manifest is run on the train benchmark specs
# (listed in data/gf_benchmarks.json) and scored from its returned automata.
#
# Usage: bash scripts/evaluate_train.sh [outputs_dir] [score_file]

set -e

cd /home/user

OUTPUTS_DIR="${1:-outputs}"
SCORE_FILE="${2:-scoring/scores_train.json}"

python eval/train/evaluate_gf.py --outputs "$OUTPUTS_DIR" --output "$SCORE_FILE"
