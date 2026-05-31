# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-05-31 20:39] - core_claim
- Implemented the paper's Section 6 direct GFM construction for `GF phi` formulas using NFA states, unconditional reset transitions, and accepting resets when the NFA can reach a final state.
- Reproduced the Table 2 direct-construction state counts for TDR[6-10] and LIB[6-9] with semantic structure checks passing.
- Verified the packaged workflow with `python validate.py --compare`; an earlier container job also completed `scripts/reproduce.sh` successfully.

### [2026-05-31 20:41] - core_claim
- Audited the inherited workspace and confirmed the method and evaluation are real, separated, and validated.
- Added Appendix N/Table 5 NCS[4-11] direct-construction benchmarks and reproduced the paper's aggregate `GFM-GF` state count locally.
- Submitted a CPU container validation job before raising the milestone beyond `core_claim`.

### [2026-05-31 20:43] - core_claim_plus
- CPU container job `d5313962-fe4` completed successfully with exit code 0.
- The packaged workflow reproduced TDR[6-10], LIB[6-9], and NCS[4-11] aggregate `GFM-GF` state counts exactly, with semantic checks and target-match checks at `1.0`.
- Raised the milestone to `core_claim_plus` because the reproduction now covers the core direct-construction claim plus an additional appendix benchmark family.

## Stop Justification
- Completed at milestone `core_claim_plus`.
