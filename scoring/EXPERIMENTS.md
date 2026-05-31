# Experiment Overview

## tdr_direct_gf
Evaluates automata size on delayed-response liveness specifications where a trigger must be followed by a response after a fixed number of steps, and this requirement must recur infinitely often. The experiment asks whether the produced automata stay small as the delay grows while preserving the expected accepting behavior.

## lib_direct_gf
Evaluates automata size on repeated liveness specifications requiring at least one monitored Boolean signal to change value. The experiment asks whether the produced automata remain compact across increasing numbers of signals while preserving the expected accepting behavior for every signal.
