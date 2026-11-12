# Overview

- **Paper ID:** 2511.09073
- **Title:** Good-for-MDP State Reduction for Stochastic LTL Planning
- **Domain:** Formal Methods / Stochastic Planning
- **TL;DR:** Small good-for-MDP automata for LTL planning goals; a direct, singly-exponential construction for recurring co-safety goals `GF phi`.

## Short Summary

Stochastic planning with LTL goals composes an MDP with an automaton, so automaton size drives planning scalability. The paper introduces a reduction pipeline for good-for-MDP automata and a specialised construction for `GF phi` with co-safety `phi`. This gym asks for small automata for `GF phi` goals that are correct and good-for-MDPs. It covers the paper's delayed-response (TDR), signal-change (LIB) and nested-conjunction (NCS) families, plus random recurring co-safety goals. Held-out instances are generated at test time.

## Key Results (reproduced)

- TDR[6..10]: 45 states in total, matching the paper's GFM-GF column (reduced Owl 1984, reduced slim 1002).
- LIB[6..9]: 64 states in total, matching the paper (reduced Owl 68).
- NCS (Appendix N, eight rows): 60 states in total, matching the paper (reduced slim 1036).
- Every reproduced automaton passes the language checks and the MDP planning-value (good-for-MDPs) checks.
