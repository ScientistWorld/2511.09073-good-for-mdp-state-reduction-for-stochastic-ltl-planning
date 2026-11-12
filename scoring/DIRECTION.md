# Research Direction

## Research Problem
Construct small good-for-MDP automata for recurring co-safety LTL goals `GF phi`, so that MDP × automaton products used for stochastic planning stay small without losing optimality.

## Core Contribution
Work should stay in automata construction and reduction. Given the same formulas, produce automata with fewer states (and transitions) that recognise the same language and remain good-for-MDPs. Gains should come from a construction that generalises to unseen formulas.

## Approach Scope
In scope: better finite-pattern automata (smaller nondeterministic automata, simulation- or language-based state merging), semantics-preserving formula rewriting at the level of the recurring goal, minimisation of the produced automata that preserves good-for-MDPness (for example the good-for-games co-Büchi minimisation route the paper also proposes), symbolic transition simplification, and portfolios that keep the smallest correct automaton.

## Out of Bounds
Do not replace the task with simulation, sampling, learned predictors or tables keyed on benchmark names. Do not output automata that are only correct on likely probes. Do not use nondeterminism that needs knowledge of future letters, which breaks the planning guarantee. Do not fit outputs to the evaluator's probes.
