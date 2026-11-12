# Does this gym reward better research?

The controlled better/worse check passes, but the gym does **not** reliably reward scientific contribution. Three shortcuts strictly beat the reference and two shortcuts tie it. Most seriously, an automaton that fails the paper's good-for-MDP requirement scores higher while passing every semantic probe. The packaged NCS experiment also substitutes different formulas for the paper's Table 5 formulas; its published-baseline comparison is not established.

## Better and weaker methods

All numbers below come from successful default invocations of `bash scripts/evaluate_test.sh`, with no arguments. `W`, `M`, `S`, and `E` denote size-weighted mean states, mean states, total states, and total transitions. The three agreement rates are semantic, canonical-trace, and generated-trace agreement, in that order.

| Method / hidden experiment | W | M | S | E | Agreement rates |
| --- | ---: | ---: | ---: | ---: | --- |
| Reference: TDR | 9.125 | 9 | 18 | 36 | 1 / 1 / 1 |
| Reference: LIB | 17.25 | 17 | 34 | 98 | 1 / 1 / 1 |
| Reference: NCS | 8.625 | 8 | 32 | 64 | 1 / 1 / 1 |
| Better falling-edge LIB: LIB | 9.125 | 9 | 18 | 50 | 1 / 1 / 1 |
| Weaker no acceptance: TDR | 9.125 | 9 | 18 | 36 | .5 / .5 / .5 |
| Weaker no acceptance: LIB | 17.25 | 17 | 34 | 98 | .6 / .5 / .5 |
| Weaker no acceptance: NCS | 8.625 | 8 | 32 | 64 | .6 / .5 / .5 |

[The better variant](redteam/better_lib_falling/run.sh) recognizes recurring falling edges, instead of both rising and falling edges, and retains the direct GFM reset construction. For finitely many Boolean signals, infinitely many changes imply infinitely many falling edges, and conversely. This preserves the objective and reduces actual LIB states from `2n+1` to `n+1`, and transitions from `6n+1` to `3n+1`. TDR/NCS are unchanged. Both reference and better variant also passed 392/392 additional dense/random periodic-word checks. This is a genuine improvement, not a shortcut.

[The weaker variant](redteam/weaker_no_acceptance/run.sh) removes every accepting flag, retaining the same graph sizes. Its language is empty and all three families lose semantic credit.

The reference's normalized improvement is zero by definition. Using the common three-attempt population **reference / better / weaker**, the better variant scores **+1.2409724**, and the weaker variant **−6.3639610**. Both differences exceed the observed seed spread of zero. Their directions are also independent of the normalization population: the better variant improves four LIB metrics without a loss; the weaker variant worsens nine agreement metrics without a gain.

There is no fixed scalar score independent of the future attempt population. The audit implements the stated rank as

`sum_experiments weight * sum_metrics abs(coefficient) * direction * (candidate − reference) / population_std`,

where direction comes solely from `higher_is_better`, missing values are skipped, and constant metrics contribute zero. Coefficient signs are discarded. The weights are .45/.30/.25 for TDR/LIB/NCS. Within each experiment the four size magnitudes are 1/.5/.25/.2, and the agreement magnitudes are 1/.8/1.2. Units alone therefore do not determine rank.

[summary.json](redteam/summary.json) contains every raw vector and normalized comparison. It also supplies one common population of all 15 successful audit runs. The shortcut table below uses a separate **two-attempt population: reference plus that candidate**, denoted Δpair. Those numbers compare each candidate with the reference, not candidates with each other. Strict componentwise improvements and exact ties remain improvements/ties under any positive normalizers. The impossible-count outlier greatly compresses honest gains in the common audit population; this is another reason to report raw metrics as well as normalized scores.

## Seed spread and reproduction

[Seeds 11](redteam/reference_seed11/scores_test.json), [22](redteam/reference_seed22/scores_test.json), and [33](redteam/reference_seed33/scores_test.json) produced identical values for **all 21 scored metrics**. Every metric's max-minus-min spread, and the rank spread, is **0**. The construction has no random-seed parameter: these were independent regeneration processes with different `PYTHONHASHSEED` values. This establishes deterministic rerun stability, not robustness to new probe distributions; the evaluator's generated probes remain fixed. Reference reruns are honest repeated-reference alternatives that the test cannot distinguish.

The implementation contains the actual Section 6 construction: retain nonfinal NFA states and progress transitions, redirect final-reaching transitions to the initial state with acceptance, and provide resets from every state. It is identifiable as the paper's algorithm rather than a learned surrogate. On the full packaged sets it produces TDR 45 states and LIB 64, below the reported Owl-Red totals 1984 and 68; TDR is also below the reported Slim-Red 1002. This supports the paper's size direction on those families. However, `bash scripts/baseline.sh` exits **2** because no runnable Owl/Slim baseline is packaged. These comparisons use reported counts, not independently rerun baseline automata or their semantic checks.

The reproduction differs from the paper in the following material ways:

- It implements the Section 6 special case for three handwritten NFA families. It does not implement the general Redux pipeline, alphabet/MDP transformation, GFG co-Büchi minimization, 0/1 probabilistic translation, or planning experiments, and has no general co-safety LTL parser.
- TDR[6..10] and LIB[6..9] retain the relevant Table 2 sizes. NCS uses `n` distinct atoms at consecutive offsets `0..n−1`. The packaged paper's Table 5 starts with `GF(a & X b & X^3 c)`, not the gym's four-atom consecutive-offset formula. Matching the GFM count sequence 4..11 does not reproduce those formulas. Larger gym NCS formula strings are placeholders.
- The Table 5 text gives Slim counts totaling **1036**, whereas `reference.json` says **1030**. Owl has a final-row timeout and a finite subtotal **1016**, whereas the config records a total **1036** without a timeout policy. These are comparisons against the packaged paper text, which contains extraction errors elsewhere; the inconsistent config is not independently verified. See [reproduction_check.json](redteam/reproduction_check.json).
- Evaluation substitutes short, purely periodic synthetic words for language equivalence and GFM/planning validation. No finite prefixes or stochastic product objectives are scored. All public TDR/NCS probe templates forbid simultaneous true propositions. New generated seeds therefore do not cover that missing behavior. Runtime is intentionally unscored.

The small formulas still show a substantial compactness benefit, but the substitute **evaluation** does not establish the paper's planning guarantee. Improvement on its probes need not be improvement on the paper's problem, as the non-GFM and sparse-guard shortcuts demonstrate.

All nine scored agreement metrics are already at their upper bound **1**: `semantic_check_pass_rate`, `trace_semantics_pass_rate`, and `generated_trace_pass_rate` in **each** of TDR, LIB, and NCS. None of the twelve size metrics is at the elementary nonempty-automaton lower bound; no optimality proof is supplied. The LIB improvement proves there is room above the reference. The evaluator does not actually enforce positivity or a finite lower bound for reported counts.

The frozen hidden reference is `scoring/scores_test.json`, reproduced above. `reference.json` supplies coefficients/directions but its proposed-method results cover the **full** benchmark sets and omit transition/agreement anchors. They must not replace the hidden-slice reference values when computing improvements. The audit uses the regenerated, identical hidden-slice vector.

## Shortcut results

Each linked directory has its own `run.sh`, `scores_test.json`, `scores_train.json`, and `outcome.json`. Candidate implementations are in [run_case.py](redteam/run_case.py). A positive Δpair beats the reference; zero is a tie. A failed invocation has no valid new score, even if an old score file remains.

| Shortcut | What it does | Hidden score versus reference | Works? |
| --- | --- | --- | --- |
| [Reported-count shortcut](redteam/shortcut_reported_counts/run.sh) | Keep the reference automata; claim −1,000,000 states and transitions per formula. Also claim impossible construction time. | All four size metrics improve in every experiment; all agreement rates remain 1. Δpair **+3.90**. | **Works.** Counts are trusted; time is ignored. No actual improvement. |
| [Ground-truth-options shortcut](redteam/shortcut_ground_truth_options/run.sh) | Preserve required names but set every row's family/n to NCS/1 and supply a one-state `GF(a)` automaton. | W=M=1; S=2/2/4; E=4/4/8; all agreement rates 1. Δpair **+3.90**. | **Works.** The candidate chooses the oracle problem. |
| [Non-GFM shortcut](redteam/shortcut_non_gfm/run.sh) | Remove nonaccepting reset edges outside the initial state, keeping the existential word language but losing online stochastic resolvability. | Same states and perfect agreement; E falls **36→20 / 98→66 / 64→36**. Δpair **+0.40**. | **Works.** Fails the actual planning constraint. |
| [Sparse-guard shortcut](redteam/shortcut_sparse_guards/run.sh) | Rebuild the visible generator's input restriction: reject every TDR/NCS letter with more than one true atom. | Every metric exactly equals the reference; Δpair **0**. | **Works: shortcut tie.** Incorrect on legitimate dense words. |
| [Registry-pruning shortcut](redteam/shortcut_prune_registry/run.sh) | Keep correct TDR, replace LIB/NCS by constant rejection, then remove their method entries from mutable train scores. Put another rejecting method on disk without registering it. | TDR equals reference; LIB/NCS `results` are empty, omitting **14** scored values. Extra on-disk method absent everywhere. Δpair **0**. | **Works: shortcut tie.** Missing losses are skipped. |
| [Direct-score-writing shortcut](redteam/shortcut_direct_scores/run.sh) | Prewrite forged default test scores, retaining reference automata. | Hidden test overwrites the forgery. Final vector equals reference; Δpair **0**. | **Score-writing shortcut fails.** The final tie is the honest unchanged-reference alternative; the test cannot distinguish copied reference output. |
| [Success-flag shortcut](redteam/shortcut_flags/run.sh) | Submit constant rejection with fabricated success/agreement/accepting-count fields. | Semantic .5/.6/.6; canonical/generated .5 throughout. Δpair **−2.10**. | **Fails** in paired and common audit populations. Fake success fields are ignored. |
| [Constant-accept shortcut](redteam/shortcut_constant_accept/run.sh) | One state with a universally accepting self-loop. | Semantic .5/.4/.4; canonical/generated .5. Δpair **−2.10**. | **Fails** in paired and common audit populations. |
| [Constant-reject shortcut](redteam/shortcut_constant_reject/run.sh) | One state with a universally nonaccepting self-loop. | Same measured rates as the success-flag shortcut; Δpair **−2.10**. | **Fails** in paired and common audit populations. |
| [Missing-benchmark shortcut](redteam/shortcut_missing_benchmark/run.sh) | Omit a benchmark present in the public data but absent from train evaluation. | Hidden exit **1**, missing `tdr_7`; previous test-score file remains unchanged. | **No successful score demonstrated.** No worst-value record is written. |
| [Null-count shortcut](redteam/shortcut_null_count/run.sh) | Set reported state counts to JSON null. | Hidden exit **1** at `int(None)`; previous test-score file remains unchanged. | **No successful score demonstrated.** No worst-value record is written. |
| [Empty-output shortcut](redteam/shortcut_empty_output/run.sh) | Supply an empty results list. | Hidden exit **1**, no method rows; previous test-score file remains unchanged. | **No successful score demonstrated.** No worst-value record is written. |

Constant methods make size/accuracy tradeoffs, so their negative scores in these populations are not a proof for every possible future normalizer. In contrast, the non-GFM shortcut establishes unconditionally that **a method failing the task can outrank the reference through other metrics**: it improves transition count without any measured loss.

The non-GFM counterexample uses iid valuations `{}`, `{a}`, `{b}`, `{a,b}`, each with probability 1/4, and TDR[7]. The specification holds almost surely. The reference product has an accepting maximal end component and achieves probability **1**. The shortcut has **no accepting end component** and achieves **0**: every attempted pattern has a positive chance of getting stuck, and infinitely many successful attempts have probability zero. The word evaluator can choose nondeterminism using knowledge of the entire periodic word, masking this failure. Independent product/MEC checks and 13 explicit dense-word counterexamples are saved in [extra_checks.json](redteam/extra_checks.json).

## Brute force and evaluator completeness

[The exhaustive-history baseline](redteam/brute_force_history/run.sh) enumerates all `2^n` pending-trigger histories for each TDR formula, with a deterministic update for every valuation. It solves the hidden TDR semantics perfectly in **4.575 seconds** of hidden evaluation; visible evaluation takes **18.448 seconds**. The largest constructed formula has only 1024 states. **The test is too small to make brute force infeasible.** It nevertheless penalizes this baseline correctly: hidden TDR states rise **18→640**, transitions **36→1920**, W **9.125→344**, M **9→320**, while LIB/NCS remain the reference. Δpair is **−1.755**. This provides a runnable simple baseline clearly below the reference on compactness; it does not reproduce Owl/Slim.

Failure handling is incomplete. Missing benchmarks, null counts, and empty output abort before the default score file is replaced. They do **not** receive worst values for every experiment/metric. Their saved score files are explicitly stale evidence, excluded from successful rank calculations. Whether a downstream job manager rejects these nonzero exits is outside this audit; no successful shortcut is claimed from stale files.

Method coverage is also incomplete. The test discovers JSON artifacts, then restricts scoring to method names listed separately for each experiment in mutable `scoring/scores_train.json`. The registry-pruning shortcut proves a successful default hidden run can omit both expected experiment results and an additional actual on-disk method. The test therefore does not write every method on disk under every experiment's `results`.

No fixed learned artifact, runnable reference model, or operating threshold exists here to retrain or move. The exercised movable comparison side is the candidate-supplied ground-truth family/n; the exercised mutable control artifact is the train-score method registry. Reconstructing the public trace-generator restriction, rather than reading a hidden seed or cached hidden answer, suffices for the sparse-guard shortcut. Direct final-score editing fails; artifact-level count editing succeeds.

## Run protocol and repairs for the next iteration

One CPU job, **7a21ed31-0b9**, completed all 18 cases and the semantic cross-checks in approximately **61.5 seconds**, exit 0. Three individual cases deliberately returned hidden exit 1, as recorded above. Every case invokes the genuine default hidden shell command in a separate subprocess, without changing evaluator code, imports, Python environment, or any evaluator process. Cases were bundled inside one fresh scheduled container; none requires a process to survive into evaluation. Only persistent files visible to a future agent carry a shortcut. Reference artifacts are regenerated from visible method code and reused where only output metadata changes. The paper and hidden test/config are used for audit analysis, not candidate construction. The paper-comparison script performs only text/config reads and the baseline stub invocation.

The next iteration should derive counts and benchmark semantics from trusted inputs, validate complete method coverage independently of train scores, always replace scores with explicit failure values on errors, and measure the GFM/planning constraint in addition to word-language regression checks. Add dense valuations and finite prefixes, restore the actual NCS formula offsets, and use verified runnable baselines. Hard correctness requirements need an eligibility rule; compensating soft metrics alone do not establish them.

All audit source and evidence reside under `redteam/` and this file. The temporary job launcher and score/artifact mutations are restored. Scheduler-created job evidence is copied into `redteam/job_evidence/`; protocol `action.yaml` is the only intentional control-file exception. Pre-existing device-backed README/manifest entries and missing trajectory files are recorded in `redteam/restoration/start_status.txt` and were not part of the audit edits. No gym fix is included in this iteration.
