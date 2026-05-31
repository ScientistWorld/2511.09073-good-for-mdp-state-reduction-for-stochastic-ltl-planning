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

## Stop Justification
- Completed at milestone `core_claim` for the direct GFM-GF construction claim. Higher milestones require implementing the full general Redux pipeline and external automata-tool baselines.
