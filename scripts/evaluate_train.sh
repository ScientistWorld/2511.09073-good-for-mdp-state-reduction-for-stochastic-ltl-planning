#!/bin/bash
# Evaluate method artifacts on the visible train slice.
#
# Usage:
#   bash scripts/evaluate_train.sh [artifact_or_output_dir] [score_output]

set -e

cd /home/user

INPUT="${1:-outputs}"
OUTPUT="${2:-scoring/scores_train.json}"

python eval/train/evaluate_gf.py --input "$INPUT" --output "$OUTPUT"
