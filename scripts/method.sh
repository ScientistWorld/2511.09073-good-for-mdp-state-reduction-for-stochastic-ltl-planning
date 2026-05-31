#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

python method/direct_gfm.py \
  --benchmarks data/gf_benchmarks.json \
  --output outputs/results.json

bash scripts/evaluate.sh outputs/results.json
