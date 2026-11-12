# Paper's Method

## Key Contribution

The paper proposes a state-space reduction for good-for-MDP (GFM) automata used in stochastic LTL planning, and a specialised direct construction for formulas `GF phi` where `phi` is co-safety.

## Approach

The general reduction pipeline (Section 5) turns a GFM Büchi automaton into a deterministic Büchi automaton by embedding nondeterministic successor choices into the alphabet. It reinterprets that automaton as a deterministic co-Büchi automaton, applies good-for-games co-Büchi minimisation, and resolves the remaining nondeterminism uniformly to obtain a 0/1 probabilistic automaton.

For the `GF phi` fragment (Section 6), the paper starts from an NFA for the finite-trace co-safety property `phi`. It builds a Büchi automaton over the non-final NFA states (plus the initial state). The construction keeps the NFA's transitions that stay non-final, always allows a reset to the initial state on every letter, and marks a reset transition `(q, sigma, q0)` accepting exactly when the NFA can reach a final state from `q` on `sigma`. The result recognises `GF phi`, is GFM (Theorem 5), and is singly exponential in `|phi|`. Its size is the size of the NFA.

## This reproduction

`method/direct_gfm.py <specs.json> <output.json>` implements Section 6 for arbitrary co-safety `phi`:
1. Parse `GF(phi)`.
2. Build an NFA for `phi` by partial derivatives (linear forms). States are residual obligations, transitions are labelled by cubes, and the obligation `true` is final. Apply language-preserving NFA reductions: merge states with equal residual languages (checked exactly by progression), treat valid residuals as final, and drop nondeterministic targets whose language is covered by another target on a weaker guard. When a determinised automaton for `phi` (merged up to language equivalence) gives a smaller result, it is used as the NFA instead. The paper builds its NFAs with an optimising tool chain; these reductions stand in for that.
3. Apply the paper's reset construction.

On the paper's families this gives exactly the reported GFM-GF sizes: TDR[n] has n+1 states, LIB[n] 2n+1, and NCS has span+1. The Section 5 Redux pipeline (Spot GFG minimisation) and the Owl/Slim baselines are not reimplemented; their sizes come from the paper's tables.

## Main Claims

The primary claim is that the proposed constructions substantially reduce automaton state counts for stochastic LTL planning benchmarks. The claim reproduced here is that the direct `GF phi` construction yields GFM automata whose size grows linearly where the reduced Owl and slim GFM automata grow exponentially (TDR, NCS). It is also slightly smaller than reduced Owl on LIB.
