#!/bin/bash
# Reproduce the paper's results end-to-end.
#
# Registers the paper's direct GFM construction as a constructor
# (outputs/gfm_gf.method.json), scores it on the public paper benchmark set
# (scoring/scores.json: TDR[6..10]=45, LIB[6..9]=64, NCS rows 1..8=60 states),
# on the visible train slice and on the held-out test, then validates.
#
# Assumes the container is built and the working directory is /home/user.

set -e

cd /home/user

bash scripts/method.sh
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
python validate.py --compare
