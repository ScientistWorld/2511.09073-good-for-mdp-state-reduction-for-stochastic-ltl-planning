# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-31 20:39] - core_claim
- Implemented the paper's Section 6 direct GFM construction for `GF phi` formulas using NFA states, unconditional reset transitions, and accepting resets when the NFA can reach a final state.
- Reproduced the Table 2 direct-construction state counts for TDR[6-10] and LIB[6-9] with semantic structure checks passing.
- Verified the packaged workflow with `python validate.py --compare`; an earlier container job also completed `scripts/reproduce.sh` successfully.

## Stop Justification
- Completed at milestone `core_claim`.
