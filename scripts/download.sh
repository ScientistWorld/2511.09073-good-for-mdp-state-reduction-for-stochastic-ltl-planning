#!/bin/bash
# Download all data and models needed for this environment.
#
# Run on a node with internet access BEFORE building the container
# or submitting compute jobs.
#
# This script should be idempotent — safe to run multiple times.
# It should skip files that already exist.
#
# Update the storage estimate below as you add downloads.
#
# Estimated total download size: 0 GB
# Estimated disk usage after extraction: <1 MB
#
# This reproduction has no external downloads. If future work adds resources,
# fetch them into workspace-local paths such as data/downloads/ so a fresh clone
# can be repopulated without machine-specific caches.

set -e

cd /home/user

# The reproduction uses small benchmark specifications tracked in git under
# data/gf_benchmarks.json and has no external datasets or pretrained models.
mkdir -p data/downloads
