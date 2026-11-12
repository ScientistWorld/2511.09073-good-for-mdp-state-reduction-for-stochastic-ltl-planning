#!/bin/bash
# Run a runnable baseline from the hardening audit and score it like any method.
#
# Available baselines (all registered through the same manifest interface):
#   brute_force_dba  deterministic Buchi automaton of GF(phi) (pending-attempt
#                    monitor) -- the determinisation the paper's construction avoids
#   weaker_dfa       the paper's reset construction applied to a deterministic
#                    automaton for phi instead of a small NFA
# Owl/Owl-Red and Slim/Slim-Red numbers are paper-reported values in
# scoring/reference.json (those tools are not packaged).
#
# Usage: bash scripts/baseline.sh <brute_force_dba|weaker_dfa>

set -e

cd /home/user

NAME="${1:?usage: bash scripts/baseline.sh <brute_force_dba|weaker_dfa>}"
case "$NAME" in
  brute_force_dba|weaker_dfa) ;;
  *) echo "unknown baseline: $NAME" >&2; exit 2 ;;
esac

DIR="outputs/baseline_$NAME"
rm -rf "$DIR"
mkdir -p "$DIR"
cat > "$DIR/$NAME.method.json" <<JSON
{"method": "$NAME", "command": ["python", "baseline/gf_baselines.py", "$NAME"]}
JSON
python eval/train/evaluate_gf.py --outputs "$DIR" --output "$DIR/scores_train.json"
python eval/train/evaluate_gf.py --suite paper --outputs "$DIR" --output "$DIR/scores_paper.json"
