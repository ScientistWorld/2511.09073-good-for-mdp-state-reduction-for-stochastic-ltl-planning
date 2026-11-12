#!/bin/bash
# Hardening audit: run every case through the unmodified hidden evaluator.
set -euo pipefail
cd /home/user
H=redteam/hardening

# 1. all cases (reference, better/weaker variants, brute force, shortcuts) in one directory
AUD=outputs/audit_all
rm -rf "$AUD" && mkdir -p "$AUD"
python "$H/variants.py" --register "$AUD"
bash scripts/evaluate_test.sh "$AUD" "$H/scores_test_audit.json" 2>&1 | tee "$H/test_audit.log"
bash scripts/evaluate_train.sh "$AUD" "$H/scores_train_audit.json" 2>&1 | tee "$H/train_audit.log"

# 2. default score path: forged score files are overwritten, the train-score
#    registry is not consulted, every manifest on disk is scored
DEF=outputs/audit_default
rm -rf "$DEF" && mkdir -p "$DEF"
for c in gfm_gf_reference shortcut_direct_scores shortcut_prune_registry; do
  cp "$AUD/$c.method.json" "$DEF/"
done
bash scripts/evaluate_test.sh "$DEF" 2>&1 | tee "$H/default_path.log"
cp scoring/scores_test.json "$H/default_path_scores_test.json"

# 3. determinism of the reference under different hash seeds
REF=outputs/audit_ref
rm -rf "$REF" && mkdir -p "$REF"
cp "$AUD/gfm_gf_reference.method.json" "$REF/"
for seed in 11 22; do
  PYTHONHASHSEED=$seed bash scripts/evaluate_test.sh "$REF" "$H/reference_seed$seed.json"
done

python "$H/analyze.py" | tee "$H/summary.md"
