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
