# Good-for-MDP State Reduction for Stochastic LTL Planning

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2511.09073"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2511.09073-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2511.09073](https://arxiv.org/abs/2511.09073) |
|:---|:---|
| **Domain** | Formal Methods / Stochastic Planning |
| **TL;DR** | The paper reduces automata state spaces for LTL planning and gives a compact direct construction for repeated-reachability formulas. |

## Summary

Stochastic planning with LTL goals often composes an MDP with an automaton, so automaton size directly affects planning scalability. The paper introduces a reduction pipeline for good-for-MDP automata and a specialised construction for `GF` co-safety formulas. This reproduction implements the specialised construction and evaluates it on the paper's Table 2 TDR and LIB benchmarks.

## Problem

How can one construct small automata for Linear Temporal Logic objectives used in stochastic planning, especially objectives that require finite patterns to recur infinitely often?

## The paper's method

The paper proposes state-space reduction for good-for-MDP automata used in stochastic LTL planning, and a specialised direct construction for formulas of the form `GF phi` where `phi` is co-safety.

## Key results of the paper

- Reproduced the proposed direct-construction state counts for TDR[6-10]: aggregate 45 states.
- Reproduced the proposed direct-construction state counts for LIB[6-9]: aggregate 64 states.
- Reproduced Appendix N direct-construction state counts for NCS[4-11]: aggregate 60 states.
- Semantic structure checks pass for all generated automata.

## Run it

```bash
pip install sciworld
sw research 2511.09073 --mode innovate --agent claude-code
sw evaluate 2511.09073
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

