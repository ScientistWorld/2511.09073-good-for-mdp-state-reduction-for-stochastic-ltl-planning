#!/bin/bash
# Job script: hardening audit, then regenerate the reference scores end to end.
#
# Runs inside the compute container (workspace at /home/user, no internet).

set -e

cd /home/user

# Hardening audit (reference, better/weaker variants, brute force, shortcuts),
# every case scored by the unmodified hidden evaluator.
bash redteam/hardening/run_audit.sh

# Reference end to end: register the method, score it on the public paper set
# (scoring/scores.json), the train slice and the hidden test.
rm -rf outputs/audit_all outputs/audit_default outputs/audit_ref
bash scripts/method.sh
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
python validate.py --compare
