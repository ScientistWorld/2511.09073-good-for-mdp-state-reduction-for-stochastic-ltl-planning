# Experiment Overview

## tdr_delayed_response
Evaluates automata size on delayed-response liveness specifications where a trigger must be followed by a response after a fixed number of steps, and this requirement must recur infinitely often. The experiment asks whether the produced automata stay small as the delay grows while preserving the expected accepting behavior.

## lib_signal_change
Evaluates automata size on repeated liveness specifications requiring at least one monitored Boolean signal to change value. The experiment asks whether the produced automata remain compact across increasing numbers of signals while preserving the expected accepting behavior for every signal.

## ncs_ordered_sequence
Evaluates automata size on nested conjunction sequence liveness specifications where a fixed ordered pattern of observations must recur. The experiment asks whether compact automata persist as the required sequence length grows while preserving the accepting transition at the end of each completed sequence.
