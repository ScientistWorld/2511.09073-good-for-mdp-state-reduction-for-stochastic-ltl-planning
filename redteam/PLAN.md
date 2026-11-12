# Submitted audit plan

All computation runs in one CPU job. The login node was used only for reads,
source editing and syntax checks. No external datasets or packages are needed.

1. Regenerate the reference in three independent Python processes with hash
   seeds 11, 22 and 33 (the construction itself is deterministic).
2. Test a genuine improvement: retain only falling-edge LIB branches, preserving
   GF(any signal changes) while reducing actual automaton size.
3. Test a weaker variant: remove all accepting transitions.
4. Test shortcuts for self-reported counts, mutable ground-truth options,
   failure of the GFM property, sparse public trace templates, and pruning the
   mutable train-score registry. Test direct score and success-flag writing,
   degenerate constant outputs, omitted benchmarks, null counts and empty output.
5. Explicitly enumerate every n-bit pending-trigger history for TDR, producing a
   deterministic automaton instead of the compact nondeterministic construction.
6. Independently check dense LIB words and a fair-coin MDP, then summarize scores
   with directions and absolute coefficients, normalized by audit-cohort spread.

Every shortcut/variant has a standalone `run.sh`. Evaluation is always the default
hidden shell command with no arguments, in its own subprocess. All candidates
are generated using only public benchmark names, method source and train probe
patterns. No hidden test seed or hidden evaluator implementation is used in a
candidate. The original output directory and default score files are restored
after every case. The scheduled launcher and action file are restored at the
end of the audit; only redteam/ and REDTEAM.md will be committed as final changes.
