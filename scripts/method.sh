#!/bin/bash
# Register the paper's method (direct GFM construction for GF(co-safety)
# formulas, Section 6) as a constructor and score it on the public paper set.
#
# The constructor is method/direct_gfm.py <specs.json> <output.json>; the
# evaluators run it on their own benchmark specs.
#
# Usage: bash scripts/method.sh

set -e

cd /home/user

mkdir -p outputs
cat > outputs/gfm_gf.method.json <<'JSON'
{"method": "gfm_gf", "command": ["python", "method/direct_gfm.py"]}
JSON

# Convenience artifact: automata for the public benchmark list.
python method/direct_gfm.py data/gf_benchmarks.json outputs/gfm_gf_public_automata.json

bash scripts/evaluate.sh
