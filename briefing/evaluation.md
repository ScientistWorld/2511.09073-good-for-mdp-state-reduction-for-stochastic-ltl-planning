# Evaluation

## Interface

A method is a **constructor command** registered by a manifest `outputs/<name>.method.json`:

```json
{"method": "<name>", "command": ["python", "path/to/constructor.py"]}
```

The evaluators write their own benchmark specification file and run, from the workspace root,

```
<command...> <specs.json> <output.json>
```

`specs.json` is `{"benchmarks": [{"name": ..., "formula": "GF(...)", "atoms": [...]}, ...]}`. Formulas use atoms (`[a-z_][a-z0-9_]*`), `!` (on atoms only), `&`, `|`, `X`, `F`, `U`, `true`, `false` and parentheses. The method must write

```json
{"results": [{"name": "<benchmark name>",
              "gfm": {"states": ["q0", ...], "initial": "q0",
                      "transitions": [{"src": "q0", "dst": "q1",
                                       "condition": "a & !b", "accepting": false}, ...]}}]}
```

`condition` is a Boolean guard over the benchmark's atoms using `!`, `&`, `|`, parentheses, `true` and `false`. Atoms outside the benchmark's alphabet are false. `accepting` must be a JSON boolean and marks Büchi-accepting transitions. A word is accepted if some run takes accepting transitions infinitely often. Missing transitions mean rejection. Any other fields in a row are ignored.

`data/gf_benchmarks.json` lists the visible (train) specifications so a constructor can be developed and run by hand. The evaluators generate their own specs and do not read that file.

## Commands

- `bash scripts/evaluate_train.sh`: visible instances; writes `scoring/scores_train.json`.
- `bash scripts/evaluate.sh`: the public benchmark set that mirrors the paper's tables; writes `scoring/scores.json`.
- `bash scripts/evaluate_test.sh`: held-out instances (unseen parameters, renamed atoms, fresh random formulas generated at test time); writes `scoring/scores_test.json`.

All three take no arguments and score every manifest in `outputs/`.

## Metrics (per experiment, all recomputed from the returned automata)

- `state_count_size_weighted_mean`, `state_count_per_formula`, `state_count_sum`: automaton states. Lower is better.
- `transition_count_sum`: distinct `(source, target, accepting)` transitions with a satisfiable guard. Lower is better.
- `semantic_check_pass_rate`: agreement with the formula on label-balanced ultimately periodic words, including near-miss mutations.
- `generated_trace_pass_rate`: agreement on unconstrained dense random ultimately periodic words.
- `planning_value_agreement_rate`: on evaluator-generated MDPs, for each start state, the optimal probability obtained through the MDP × automaton product (the agent resolves the automaton's choices seeing only the current letter) must equal the true optimal probability of the goal. This is the good-for-MDPs requirement.

Correctness is a hard constraint. A method fails if its constructor errors or times out, any benchmark output is missing or malformed, an automaton exceeds 2048 states or 16384 transitions, or there is any disagreement in the three checks above (including extra checks seeded by the method's own output). A failed method receives the worst value of every metric in every experiment: rates 0, and sizes at the per-formula caps. A correct method has all rates equal to 1 and is ranked by size. Runtime is not scored. Constructors have a generous time limit (30 minutes per evaluation).

## Baselines

The paper reports reduced Owl (`owl_red`) and reduced "slim" GFM (`slim_red`) automaton sizes for its families (`scoring/reference.json`). `bash scripts/baseline.sh brute_force_dba` runs a deterministic Büchi automaton baseline, and `bash scripts/baseline.sh weaker_dfa` a determinised-pattern baseline, through the same interface.
