# Paper's Method

## Key Contribution

The paper proposes state-space reduction for good-for-MDP automata used in stochastic LTL planning, and a specialised direct construction for formulas of the form `GF phi` where `phi` is co-safety.

## Approach

The general reduction pipeline converts a GFM Buchi automaton into a deterministic Buchi automaton by embedding nondeterministic successor choices into the alphabet, reinterprets it as a deterministic co-Buchi automaton, applies good-for-games co-Buchi minimisation, then treats the result as a Buchi automaton and resolves nondeterminism uniformly to obtain a 0/1 probabilistic automaton.

For the `GF phi` fragment, the paper starts from an NFA for the finite-trace co-safety property `phi`. It builds a Buchi automaton over the non-final NFA states, always allows resetting to the initial state, and marks reset transitions accepting exactly when the NFA could reach a final state on the current letter.

## Main Claims

The primary claim is that the proposed reductions substantially reduce automata state counts for stochastic LTL planning benchmarks. The secondary claim reproduced here is that the direct `GF phi` construction scales singly exponentially and produces much smaller automata on repeated-reachability families such as TDR.
