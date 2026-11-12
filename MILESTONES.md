# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

### [2026-05-31 21:16] - core_claim
- Final verification cleaned method-agnostic scoring names, the reusable artifact path, and benchmark data separation.
- Re-ran `scripts/method.sh`, train/test evaluators, `python validate.py --compare`, Python compilation, and JSON validation successfully.
- Kept the milestone at `core_claim`; the environment is usable as a gym for the packaged recurring co-safety benchmark claim.

### [2026-05-31 21:19] - core_claim
- Made the submitted `scripts/run.sh` path self-contained by regenerating method artifacts before evaluation.
- Re-ran the full lightweight flow locally: method generation, full/train/test evaluation, `python validate.py --compare`, and Python bytecode compilation.
- Submitting a CPU test job to verify the same end-to-end path in the packaged scheduler environment.

### [2026-05-31 21:22] - core_claim
- CPU test job `dc7532ce-d83` completed successfully with exit code 0, regenerating method artifacts, running full/train/test evaluation, and validating the packaged scores.
- Final verification confirmed that scoring, method/problem separation, train/test artifacts, and documentation are consistent for the packaged recurring co-safety benchmark gym.
- Kept the milestone at `core_claim`; the documented limitation remains that this is the direct `GF phi` construction reproduction rather than the full general Redux pipeline.

### [2026-11-12] - core_claim
- Hardening iteration 11 answered the red-team audit:
  - methods are now constructor commands, and the evaluator owns the specs (hidden test with unseen sizes, renamed atoms and random formulas);
  - counts are recomputed from the automata;
  - planning-value agreement on generated MDPs closes the non-GFM shortcut;
  - dense lasso probes close the sparse-guard shortcut;
  - any failure gets worst values.
- CPU job `273cd0cc-ead` (exit 0): no shortcut beats the reference, a better variant shows real headroom (+1.95 Δpair), brute-force and weaker baselines score below the reference, and `python validate.py --compare` passes. Details in `HARDENING.md`.
- The milestone stays at `core_claim`: the scope is still the Section 6 direct construction, not the general Redux pipeline.

## Stop Justification
- Completed at milestone `core_claim`.
