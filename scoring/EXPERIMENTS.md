# Experiment Overview

Every experiment scores automata that a method builds for formulas it is given at evaluation time. Correctness (the right language, and usability for MDP planning when the agent resolves the automaton's choices online) is a hard constraint for all of them. Among correct methods, smaller automata score higher.

## tdr_delayed_response
Delayed-response liveness: a trigger must be followed by a response a fixed number of steps later, infinitely often. The experiment establishes whether automata stay small as the delay grows. Naive deterministic approaches grow exponentially with the delay. The held-out test uses delays not in the visible set, with renamed atoms.

## lib_signal_change
Signal-change liveness over `n` Boolean signals: infinitely often some signal changes value. The experiment establishes whether automata stay compact as the number of signals grows. Determinising this pattern is exponential in `n`, and there is room below the paper's reported sizes. The held-out test uses unseen signal counts.

## ncs_ordered_sequence
Nested conjunction sequences: several observations at fixed relative offsets must recur together infinitely often (paper Appendix N). The experiment establishes whether compactness persists as the pattern span grows. The held-out test uses other offset patterns from the same table, with renamed atoms.

## random_cosafety_gf
Randomly generated recurring co-safety goals mixing next, eventually, until, conjunction and disjunction. The paper reports nothing for this family. It is the experiment where generic constructions leave the most room: different formulas expose different redundancies. The held-out test generates fresh formulas at test time, so only a general construction procedure can do well.
