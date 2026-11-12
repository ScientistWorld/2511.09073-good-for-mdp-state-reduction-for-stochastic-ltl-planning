# Scientist Constraints

## Interface
Register each method as `outputs/<name>.method.json` with `{"method": "<name>", "command": [...]}`. The evaluators call `<command> <specs.json> <output.json>` on benchmark specs they generate themselves (see `briefing/evaluation.md`). The method must be a general procedure. The held-out test uses formulas the method has never seen, and they are only revealed when the evaluator runs it.

## Correctness is a hard constraint
Every returned automaton must recognise exactly the language of its `GF phi` formula and must be good-for-MDPs. That means the optimal probability obtained through the MDP × automaton product, with the agent resolving nondeterminism from the current letter only, equals the true optimum on every MDP. A single disagreement on any probe, a malformed or missing automaton, more than 2048 states or 16384 transitions for one formula, or a constructor error or timeout marks the method as failed. It then gets the worst value of every metric in every experiment.

## What counts
Only the automata count. Self-reported counts, flags, rates or scores in the output are ignored, and the evaluator recomputes everything. Runtime is not scored.

## Do not
- Do not edit `eval/`, `scoring/reference.json` or the score files to change results.
- Do not special-case the visible benchmark names or formulas; the held-out instances differ.
- Do not read evaluator code or files from inside a constructor.

## Compliance Checklist
- [ ] `outputs/<name>.method.json` registers a runnable constructor command
- [ ] The constructor handles any `GF(phi)` with co-safety `phi` over the given atoms
- [ ] Output rows carry `name` and a `gfm` object with states, initial state, guarded transitions and boolean `accepting` flags
- [ ] `bash scripts/evaluate_train.sh` reports the method as `ok` (not `FAILED`)
