# Problem Definition

## Research Question

How can one construct small automata for Linear Temporal Logic goals used in stochastic planning, specifically goals of the form `GF phi` ("a finite pattern `phi` recurs infinitely often", where `phi` is a co-safety formula built from atoms, negated atoms, `&`, `|`, `X`, `F` and `U`)?

## Why It Matters

Planning in a Markov decision process (MDP) with a temporal goal builds the product of the MDP with an automaton for the goal and then solves a reachability problem on that product. The automaton's size multiplies the size of the product, so smaller automata make strategy synthesis scale.

The automaton cannot be arbitrary, though. In the product the planning agent resolves the automaton's nondeterministic choices online: it sees the current letter but not the future. The automaton must be *good-for-MDPs*: for every finite MDP, the best probability achievable through the product equals the true optimal probability of satisfying the goal. A smaller automaton that recognises the right language but needs to guess the future is not acceptable.

## Success Criteria

For each benchmark formula, produce a Büchi automaton (transition-based acceptance) that
1. recognises exactly the language of `GF phi`,
2. is good-for-MDPs, and
3. has as few states (and transitions) as possible.

The formulas include the paper's benchmark families: delayed response `GF(a & X^n b)`, signal-change liveness over `n` signals, and nested conjunction sequences with fixed offsets. There are also randomly generated `GF(co-safety)` formulas. The held-out test uses unseen parameters, renamed atoms and freshly generated formulas, so a solution has to be a general construction procedure rather than a table of answers.
