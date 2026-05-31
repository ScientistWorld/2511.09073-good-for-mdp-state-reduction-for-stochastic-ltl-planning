# Research Direction

## Research Problem
The benchmark studies construction of small good-for-MDP automata for stochastic planning with temporal objectives. Improvements should address automata-state growth for repeated-reachability Linear Temporal Logic specifications.

## Core Contribution
Work should remain in the automata-construction and automata-reduction space: given the same temporal specifications, produce smaller automata that preserve the intended acceptance behavior and remain usable for MDP planning.

## Approach Scope
Acceptable approaches include improved co-safety finite-automaton construction, better state sharing, symbolic transition simplification, post-construction automata minimisation, or extensions of the paper's GFM/0-1 probabilistic automata pipeline.

## Out of Bounds
Do not replace the task with simulation, trace sampling, model checking over a fixed MDP, or learned predictors of automata size. Do not report a smaller number unless an automaton with the required acceptance structure is actually generated.
