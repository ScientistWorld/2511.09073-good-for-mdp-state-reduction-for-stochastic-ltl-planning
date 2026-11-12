# Overview

- **Paper ID:** 2511.09073
- **Title:** Good-for-MDP State Reduction for Stochastic LTL Planning
- **Domain:** Formal Methods / Stochastic Planning
- **TL;DR:** The paper reduces automata state spaces for LTL planning and gives a compact direct construction for repeated-reachability formulas.

## Short Summary

Stochastic planning with LTL goals often composes an MDP with an automaton, so automaton size directly affects planning scalability. The paper introduces a reduction pipeline for good-for-MDP automata and a specialised construction for `GF` co-safety formulas. This reproduction implements the specialised construction and evaluates it on the paper's Table 2 TDR and LIB benchmarks.

## Key Results

- Reproduced the proposed direct-construction state counts for TDR[6-10]: aggregate 45 states.
- Reproduced the proposed direct-construction state counts for LIB[6-9]: aggregate 64 states.
- Reproduced Appendix N direct-construction state counts for NCS[4-11]: aggregate 60 states.
- Semantic structure checks pass for all generated automata.

---

# Problem Definition

## Research Question

How can one construct small automata for Linear Temporal Logic objectives used in stochastic planning, especially objectives that require finite patterns to recur infinitely often?

## Why It Matters

MDP planning with temporal goals builds a product between the planning model and an automaton for the goal. Smaller automata reduce the size of this product and make strategy synthesis more scalable.

## Success Criteria

A successful solution produces automata with fewer states on the benchmark LTL families while preserving the intended acceptance behavior needed for planning.

---

# Paper's Method

## Key Contribution

The paper proposes state-space reduction for good-for-MDP automata used in stochastic LTL planning, and a specialised direct construction for formulas of the form `GF phi` where `phi` is co-safety.

## Approach

The general reduction pipeline converts a GFM Buchi automaton into a deterministic Buchi automaton by embedding nondeterministic successor choices into the alphabet, reinterprets it as a deterministic co-Buchi automaton, applies good-for-games co-Buchi minimisation, then treats the result as a Buchi automaton and resolves nondeterminism uniformly to obtain a 0/1 probabilistic automaton.

For the `GF phi` fragment, the paper starts from an NFA for the finite-trace co-safety property `phi`. It builds a Buchi automaton over the non-final NFA states, always allows resetting to the initial state, and marks reset transitions accepting exactly when the NFA could reach a final state on the current letter.

## Main Claims

The primary claim is that the proposed reductions substantially reduce automata state counts for stochastic LTL planning benchmarks. The secondary claim reproduced here is that the direct `GF phi` construction scales singly exponentially and produces much smaller automata on repeated-reachability families such as TDR.

---

# Evaluation

## Metrics

The primary metric is automaton state count; lower is better. The packaged evaluator reports aggregate state counts over benchmark families, structural semantic check pass rate, and ultimately-periodic trace semantic pass rate to ensure smaller automata still include required accepting behavior. Runtime is intentionally not scored because wall-clock measurements vary by hardware and scheduler conditions.

## Baselines and Targets

Reference targets are taken from the paper's Table 2 for delayed-response (`TDR`) and Liberouter (`LIB`) repeated-reachability formula families, plus Appendix N/Table 5 for Nested Conjunction Sequence (`NCS`) formulas. A candidate method should produce compact automata that preserve the specified recurring finite-pattern semantics and improve over the reported reduced Owl/Slim automata where applicable.

## Evaluation Protocol

Generate an artifact containing one automaton result per benchmark formula in `data/gf_benchmarks.json`, then run `bash scripts/evaluate.sh <artifact.json>`. By default, the evaluator reads `outputs/results.json` and writes `scoring/scores.json`.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 11m | **GPU**: 0.0h

<details>
<summary>Progress Log</summary>

<!-- Write your progress here -->

</details>

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 0m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 0m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 30m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 11m | **GPU**: 0.0h
- **Jobs**: 1 total (1 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 4m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 1m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 7m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 6m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h

<details>
<summary>Progress Log</summary>

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

</details>


---

# Reproduction Milestones

**Current: core_claim**

## Stop Justification
- Completed at milestone `core_claim`.
