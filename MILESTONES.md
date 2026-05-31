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

### [2026-05-31 20:37] - core_claim
- Job `1707ed70-62d` completed successfully in the compute container with exit code 0.
- The job reproduced TDR aggregate state count `45` and LIB aggregate state count `64`, both matching the paper's GFM-GF Table 2 values.
- `python validate.py --compare` passed in the container, including scoring structure, import separation, method-output evaluation, and shared-path checks.

## Stop Justification
- Completed at milestone `core_claim`.
