# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-31 20:25] - none
- Started reproduction work and read the paper markdown.
- Identified the main automata-reduction contribution and the direct `GF phi` construction.

### [2026-05-31 20:31] - core_claim
- Implemented the paper's Section 6 direct GFM construction for Table 2 TDR and LIB repeated-reachability formulas.
- Reproduced the proposed state counts exactly for TDR[6-10] and LIB[6-9] in a local smoke run.
- Added scoring, semantic checks, scripts, and documentation for the reusable benchmark environment.

### [2026-05-31 20:35] - core_claim
- Audited the inherited implementation against the paper and confirmed it implements the Section 6 direct `GF phi` automaton construction.
- Verified that evaluation reads generated method artifacts, remains independent from `method/`, and scores the reproduced Table 2 state counts plus semantic constraints.
- Corrected documentation drift around runtime scoring and prepared another CPU container smoke test.

## Stop Justification

Not stopped.
