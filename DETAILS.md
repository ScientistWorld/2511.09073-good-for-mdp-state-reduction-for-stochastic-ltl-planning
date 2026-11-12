# Overview

- **Paper ID:** 2511.09073
- **Title:** Good-for-MDP State Reduction for Stochastic LTL Planning
- **Domain:** Formal Methods / Stochastic Planning
- **TL;DR:** Small good-for-MDP automata for LTL planning goals; a direct, singly-exponential construction for recurring co-safety goals `GF phi`.

## Short Summary

Stochastic planning with LTL goals composes an MDP with an automaton, so automaton size drives planning scalability. The paper introduces a reduction pipeline for good-for-MDP automata and a specialised construction for `GF phi` with co-safety `phi`. This gym asks for small automata for `GF phi` goals that are correct and good-for-MDPs. It covers the paper's delayed-response (TDR), signal-change (LIB) and nested-conjunction (NCS) families, plus random recurring co-safety goals. Held-out instances are generated at test time.

## Key Results (reproduced)

- TDR[6..10]: 45 states in total, matching the paper's GFM-GF column (reduced Owl 1984, reduced slim 1002).
- LIB[6..9]: 64 states in total, matching the paper (reduced Owl 68).
- NCS (Appendix N, eight rows): 60 states in total, matching the paper (reduced slim 1036).
- Every reproduced automaton passes the language checks and the MDP planning-value (good-for-MDPs) checks.

---

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

---

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

---

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

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 11m | **GPU**: 0.0h

<details>
<summary>Progress Log</summary>

<!-- Write your progress here -->

</details>

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 0m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 0m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `none` | **Status**: error
- **Working time**: 30m | **GPU**: 0.0h

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 11m | **GPU**: 0.0h
- **Jobs**: 1 total (1 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:25] - none
- Started reproduction work and read the paper markdown.
- Identified the main automata-reduction contribution and the direct `GF phi` construction.

### [2026-05-31 20:31] - core_claim
- Implemented the paper's Section 6 direct GFM construction for Table 2 TDR and LIB repeated-reachability formulas.
- Reproduced the proposed state counts exactly for TDR[6-10] and LIB[6-9] in a local smoke run.
- Added scoring, semantic checks, scripts, and documentation for the reusable benchmark environment.

### [2026-05-31 20:35] - core_claim
- Audited the inherited implementation against the paper and confirmed it implements the Section 6 direct `GF phi` automaton construction.
- Verified that evaluation reads generated method artifacts, remains independent from `method/`, and scores the reproduced Table 2 state counts plus semantic constraints.
- Corrected documentation drift around runtime scoring and prepared another CPU container smoke test.

### [2026-05-31 20:37] - core_claim
- Job `1707ed70-62d` completed successfully in the compute container with exit code 0.
- The job reproduced TDR aggregate state count `45` and LIB aggregate state count `64`, both matching the paper's GFM-GF Table 2 values.
- `python validate.py --compare` passed in the container, including scoring structure, import separation, method-output evaluation, and shared-path checks.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 4m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:39] - core_claim
- Implemented the paper's Section 6 direct GFM construction for `GF phi` formulas using NFA states, unconditional reset transitions, and accepting resets when the NFA can reach a final state.
- Reproduced the Table 2 direct-construction state counts for TDR[6-10] and LIB[6-9] with semantic structure checks passing.
- Verified the packaged workflow with `python validate.py --compare`; an earlier container job also completed `scripts/reproduce.sh` successfully.

### [2026-05-31 20:41] - core_claim
- Audited the inherited workspace and confirmed the method and evaluation are real, separated, and validated.
- Added Appendix N/Table 5 NCS[4-11] direct-construction benchmarks and reproduced the paper's aggregate `GFM-GF` state count locally.
- Submitted a CPU container validation job before raising the milestone beyond `core_claim`.

### [2026-05-31 20:43] - core_claim_plus
- CPU container job `d5313962-fe4` completed successfully with exit code 0.
- The packaged workflow reproduced TDR[6-10], LIB[6-9], and NCS[4-11] aggregate `GFM-GF` state counts exactly, with semantic checks and target-match checks at `1.0`.
- Raised the milestone to `core_claim_plus` because the reproduction now covers the core direct-construction claim plus an additional appendix benchmark family.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 1m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 7m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

### [2026-05-31 21:16] - core_claim
- Final verification cleaned method-agnostic scoring names, the reusable artifact path, and benchmark data separation.
- Re-ran `scripts/method.sh`, train/test evaluators, `python validate.py --compare`, Python compilation, and JSON validation successfully.
- Kept the milestone at `core_claim`; the environment is usable as a gym for the packaged recurring co-safety benchmark claim.

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 6m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

### [2026-05-31 21:16] - core_claim
- Final verification cleaned method-agnostic scoring names, the reusable artifact path, and benchmark data separation.
- Re-ran `scripts/method.sh`, train/test evaluators, `python validate.py --compare`, Python compilation, and JSON validation successfully.
- Kept the milestone at `core_claim`; the environment is usable as a gym for the packaged recurring co-safety benchmark claim.

### [2026-05-31 21:19] - core_claim
- Made the submitted `scripts/run.sh` path self-contained by regenerating method artifacts before evaluation.
- Re-ran the full lightweight flow locally: method generation, full/train/test evaluation, `python validate.py --compare`, and Python bytecode compilation.
- Submitting a CPU test job to verify the same end-to-end path in the packaged scheduler environment.

### [2026-05-31 21:22] - core_claim
- CPU test job `dc7532ce-d83` completed successfully with exit code 0, regenerating method artifacts, running full/train/test evaluation, and validating the packaged scores.
- Final verification confirmed that scoring, method/problem separation, train/test artifacts, and documentation are consistent for the packaged recurring co-safety benchmark gym.
- Kept the milestone at `core_claim`; the documented limitation remains that this is the direct `GF phi` construction reproduction rather than the full general Redux pipeline.

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

### [2026-05-31 21:16] - core_claim
- Final verification cleaned method-agnostic scoring names, the reusable artifact path, and benchmark data separation.
- Re-ran `scripts/method.sh`, train/test evaluators, `python validate.py --compare`, Python compilation, and JSON validation successfully.
- Kept the milestone at `core_claim`; the environment is usable as a gym for the packaged recurring co-safety benchmark claim.

### [2026-05-31 21:19] - core_claim
- Made the submitted `scripts/run.sh` path self-contained by regenerating method artifacts before evaluation.
- Re-ran the full lightweight flow locally: method generation, full/train/test evaluation, `python validate.py --compare`, and Python bytecode compilation.
- Submitting a CPU test job to verify the same end-to-end path in the packaged scheduler environment.

### [2026-05-31 21:22] - core_claim
- CPU test job `dc7532ce-d83` completed successfully with exit code 0, regenerating method artifacts, running full/train/test evaluation, and validating the packaged scores.
- Final verification confirmed that scoring, method/problem separation, train/test artifacts, and documentation are consistent for the packaged recurring co-safety benchmark gym.
- Kept the milestone at `core_claim`; the documented limitation remains that this is the direct `GF phi` construction reproduction rather than the full general Redux pipeline.

</details>

### Iteration 11: claude-opus-5-5 (hardener)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 1.0h | **GPU**: 0.0h
- **Jobs**: 1 total (1 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-31 20:47] - core_claim
- Implemented and validated the paper's Section 6 direct GFM construction for `GF phi` co-safety formulas on TDR, LIB, and NCS benchmark families.
- Reproduced the proposed GFM-GF state counts for Table 2 TDR/LIB and Appendix N NCS, with structural and ultimately-periodic trace semantic checks passing.
- Scope note: this environment reproduces the direct `GF phi` construction claim, not the full Section 5 Redux pipeline over arbitrary GFM automata.

### [2026-05-31 20:51] - core_claim
- Audited the continued workspace and found no surrogate implementation or evaluator leakage: `method/` generates automata artifacts and `eval/` scores those artifacts independently.
- Re-ran `scripts/reproduce.sh`, `python validate.py --compare`, shell syntax checks, and Python bytecode compilation successfully.
- Kept the milestone at `core_claim`; restoring `core_claim_plus` would overstate the current scope because the full Redux pipeline and external automata baselines are still not implemented.

### [2026-05-31 21:16] - core_claim
- Final verification cleaned method-agnostic scoring names, the reusable artifact path, and benchmark data separation.
- Re-ran `scripts/method.sh`, train/test evaluators, `python validate.py --compare`, Python compilation, and JSON validation successfully.
- Kept the milestone at `core_claim`; the environment is usable as a gym for the packaged recurring co-safety benchmark claim.

### [2026-05-31 21:19] - core_claim
- Made the submitted `scripts/run.sh` path self-contained by regenerating method artifacts before evaluation.
- Re-ran the full lightweight flow locally: method generation, full/train/test evaluation, `python validate.py --compare`, and Python bytecode compilation.
- Submitting a CPU test job to verify the same end-to-end path in the packaged scheduler environment.

### [2026-05-31 21:22] - core_claim
- CPU test job `dc7532ce-d83` completed successfully with exit code 0, regenerating method artifacts, running full/train/test evaluation, and validating the packaged scores.
- Final verification confirmed that scoring, method/problem separation, train/test artifacts, and documentation are consistent for the packaged recurring co-safety benchmark gym.
- Kept the milestone at `core_claim`; the documented limitation remains that this is the direct `GF phi` construction reproduction rather than the full general Redux pipeline.

### [2026-11-12] - core_claim
- Hardening iteration 11 answered the red-team audit:
  - methods are now constructor commands, and the evaluator owns the specs (hidden test with unseen sizes, renamed atoms and random formulas);
  - counts are recomputed from the automata;
  - planning-value agreement on generated MDPs closes the non-GFM shortcut;
  - dense lasso probes close the sparse-guard shortcut;
  - any failure gets worst values.
- CPU job `273cd0cc-ead` (exit 0): no shortcut beats the reference, a better variant shows real headroom (+1.95 Δpair), brute-force and weaker baselines score below the reference, and `python validate.py --compare` passes. Details in `HARDENING.md`.
- The milestone stays at `core_claim`: the scope is still the Section 6 direct construction, not the general Redux pipeline.

</details>


---

# Reproduction Milestones

**Current: core_claim**

## Stop Justification
- Completed at milestone `core_claim`.
