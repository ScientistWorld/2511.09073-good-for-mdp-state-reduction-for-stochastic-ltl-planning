# Problem Definition

## Research Question

How can one construct small automata for Linear Temporal Logic objectives used in stochastic planning, especially objectives that require finite patterns to recur infinitely often?

## Why It Matters

MDP planning with temporal goals builds a product between the planning model and an automaton for the goal. Smaller automata reduce the size of this product and make strategy synthesis more scalable.

## Success Criteria

A successful solution produces automata with fewer states on the benchmark LTL families while preserving the intended acceptance behavior needed for planning.
