#!/bin/bash
# Evaluate every registered method (outputs/*.method.json) on the public
# benchmark set that mirrors the paper's tables (TDR[6..10], LIB[6..9],
# NCS rows 1..8 of Appendix N) plus the visible random GF(co-safety) formulas,
# and write scoring/scores.json for comparison with scoring/reference.json.
#
# This uses only code in eval/; it never imports method/.
#
# Usage: bash scripts/evaluate.sh [outputs_dir] [score_file]

set -e

cd /home/user

mkdir -p scoring

OUTPUTS_DIR="${1:-outputs}"
SCORE_FILE="${2:-scoring/scores.json}"

python eval/train/evaluate_gf.py --suite paper --outputs "$OUTPUTS_DIR" --output "$SCORE_FILE"
