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

The primary metric is automaton state count; lower is better. The packaged evaluator reports aggregate state counts over benchmark families and semantic check pass rate to ensure smaller automata still include required accepting behavior. Runtime is intentionally not scored because wall-clock measurements vary by hardware and scheduler conditions.

## Baselines and Targets

Reference targets are taken from the paper's Table 2 for delayed-response (`TDR`) and Liberouter (`LIB`) repeated-reachability formula families. The target method should match the proposed construction's state counts and improve over the reported reduced Owl/Slim automata where applicable.

## Evaluation Protocol

Run `bash scripts/method.sh` to generate automata for all benchmark formulas in `data/gf_benchmarks.json` and evaluate them. `scripts/evaluate.sh` reads `outputs/gfm_gf_results.json` and writes `scoring/scores.json`.

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


---

# Reproduction Milestones

**Current: core_claim**

## Stop Justification
- Completed at milestone `core_claim`.
