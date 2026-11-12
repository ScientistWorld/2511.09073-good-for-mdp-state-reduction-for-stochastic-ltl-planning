#!/bin/bash
# Hidden-test evaluation. Runs with no arguments and scores every method on disk.
#
# A method is registered by a manifest outputs/<name>.method.json:
#   {"method": "<name>", "command": ["python", "path/to/constructor.py"]}
# The evaluator generates the held-out benchmark instances itself, runs
#   <command...> <specs.json> <output.json>
# for every registered method, recomputes every scored number from the returned
# automata, and writes scoring/scores_test.json (one entry per method and
# experiment; failed methods receive the worst value of every metric).
#
# Usage: bash scripts/evaluate_test.sh [outputs_dir] [score_file]

set -e

cd /home/user

OUTPUTS_DIR="${1:-outputs}"
SCORE_FILE="${2:-scoring/scores_test.json}"

python eval/test/evaluate_gf.py --outputs "$OUTPUTS_DIR" --output "$SCORE_FILE"
