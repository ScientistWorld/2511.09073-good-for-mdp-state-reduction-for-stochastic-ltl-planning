#!/bin/bash
# Evaluate method artifacts on the held-out test slice.
#
# Usage:
#   bash scripts/evaluate_test.sh [artifact_or_output_dir] [score_output] [train_scores]

set -e

cd /home/user

INPUT="${1:-outputs}"
OUTPUT="${2:-scoring/scores_test.json}"
TRAIN_SCORES="${3:-scoring/scores_train.json}"

python eval/test/evaluate_gf.py \
  --input "$INPUT" \
  --output "$OUTPUT" \
  --train-scores "$TRAIN_SCORES"
