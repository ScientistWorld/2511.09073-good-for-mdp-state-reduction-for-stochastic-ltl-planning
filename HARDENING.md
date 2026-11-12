# Hardening (iteration 11)

This iteration answered the red-team audit in `REDTEAM.md`. All numbers below come from CPU job `273cd0cc-ead` (exit 0), which ran `bash scripts/run.sh`. The job ran the audit harness `redteam/hardening/run_audit.sh` and then regenerated the reference scores. Raw vectors: `redteam/hardening/summary.json`. Table: `redteam/hardening/summary.md`.

## What changed in the gym

| Red-team finding | Fix |
| --- | --- |
| Reported state/transition counts were trusted | The evaluator recomputes counts from the declared automaton. It counts states, and distinct `(src, dst, accepting)` edges whose guard is satisfiable. All self-reported fields are ignored. |
| The candidate could choose its own formula/family/size ("ground-truth options") | Methods are constructor commands: `<command> <specs.json> <output.json>`. The evaluator writes the specs: formulas, atoms and sizes. The hidden test uses unseen sizes, renamed atoms and 16 random formulas drawn at test time. |
| A non-GFM automaton (right word language, wrong planning value) beat the reference | New `planning_value_agreement_rate` check. On evaluator-generated MDPs, the optimal satisfaction probability through the MDP × automaton product must equal the true optimal value. The true value comes from a deterministic monitor plus MEC analysis. |
| Probes forbade simultaneous true atoms, so sparse guards tied | Probes now include unconstrained dense random lasso words and iid-letter MDPs over the full alphabet. |
| Fixed probes could be fitted | Additional probes and MDPs are seeded by a hash of the method's own output. |
| Missing values were skipped, and missing/null/empty output crashed without a score | Any disagreement, malformed row, missing benchmark, cap violation (2048 states / 16384 edges per formula), crash or timeout fails the method. A failed method gets the worst value of every metric in every experiment. |
| The registry could be pruned and score files forged | Every `outputs/*.method.json` is scored. Score files are written only by the evaluators and never read back. |
| `scripts/baseline.sh` exited 2 | Two runnable baselines (`baseline/gf_baselines.py`) use the same interface: `brute_force_dba` (an explicit deterministic Büchi automaton) and `weaker_dfa` (the reset construction on a deterministic automaton). |
| NCS formulas did not match Table 5 | NCS offsets were rebuilt from the visible Table 5 prefixes (`a`, `X b`, `X^3 c`, …) and the reported sizes (span + 1). The Slim-Red total is the Table 5 column sum, 1036. Owl-Red is omitted because its last row timed out. |
| Agreement metrics were at their ceiling with no size headroom | Agreement metrics are now pass/fail gates. A fourth experiment, `random_cosafety_gf`, adds size headroom; the paper reports no numbers for it. |

## Audit results (hidden test, unmodified evaluator)

`S/E` means total states / transitions. `Δpair` is the weighted, normalised difference from the reference, using a population of just the reference and that candidate.

| Case | Failed | TDR S/E | LIB S/E | NCS S/E | RND S/E | Δpair |
| --- | --- | --- | --- | --- | --- | ---: |
| reference (`gfm_gf`) | no | 30/60 | 55/159 | 32/64 | 60/171 | 0 |
| better: GF-level rewriting | no | 30/60 | **29/81** | 32/64 | **45/126** | **+1.950** |
| weaker: reset construction on a DFA | no | 30/60 | 55/159 | 32/64 | 62/185 | −0.975 |
| brute force: DBA on TDR only | no | 2688/6720 | 55/159 | 32/64 | 60/171 | −1.365 |
| brute force: DBA | no | 2688/6720 | 55/159 | 1360/9680 | 83/275 | −2.925 |
| weaker: no accepting edges | yes | worst | worst | worst | worst | −10.300 |
| shortcut: reported counts / null count | no | = ref | = ref | = ref | = ref | 0 (counts ignored) |
| shortcut: direct score writing | no | = ref | = ref | = ref | = ref | 0 (forgery overwritten) |
| shortcut: ground-truth options, non-GFM, sparse guards, registry pruning, flags, constant accept/reject | yes | worst | worst | worst | worst | −10.300 |
| shortcut: missing benchmark, empty output, crash, undeclared states, string `accepting` | yes | worst | worst | worst | worst | −10.300 |

- The DBA baseline falls back to the reference construction when a formula has more than 6 atoms, because explicit determinisation over that alphabet is too large. That is why its LIB row equals the reference.
- No shortcut beats the reference. The three ties submit the reference automata unchanged, so they are not real gains.
- The better variant improves LIB and RND sizes and passes every correctness gate. That shows real headroom above the reference.
- Default path (`bash scripts/evaluate_test.sh`, no arguments): every manifest on disk was scored, no forged value survived, and every metric is present.
- Determinism: reference scores with `PYTHONHASHSEED` 11 and 22 differ from the default run by 0.0.
- After the audit, `scripts/method.sh`, `scripts/evaluate_train.sh`, `scripts/evaluate_test.sh` and `python validate.py --compare` all passed. The reference matches the paper's proposed-method counts: TDR 45, LIB 64, NCS 60.

## Known limitations

- **Rank compression.** A failed method gets cap-sized worst values, such as 6144 states for three TDR formulas. When failed methods are in the population, those values dominate the per-metric standard deviation, so honest differences look small. Example: in the all-cases population the better variant ranks only +0.004. The order of non-failing methods does not change, because every candidate shares the same normaliser. Read the raw metrics or `Δpair` alongside the population rank.
- **Scope.** The gym covers the paper's Section 6 direct `GF(co-safety)` construction. It does not cover the general Redux pipeline. Owl/Slim values are paper-reported, not rerun.
- **Coverage of the gates.** Planning and language checks are sampled: lasso words and small evaluator-generated MDPs. They are strong evidence of correctness, not a proof of GFM-ness.
