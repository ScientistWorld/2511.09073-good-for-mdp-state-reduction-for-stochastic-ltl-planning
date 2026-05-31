#!/usr/bin/env python3
"""Direct GFM construction for repeated reachability formulas.

This implements Section 6 of "Good-for-MDP State Reduction for Stochastic
LTL Planning" for the benchmark co-safety NFAs used in Table 2.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class NfaTransition:
    src: str
    dst: str
    condition: str


@dataclass
class NFA:
    states: list[str]
    initial: str
    finals: list[str]
    transitions: list[NfaTransition]


@dataclass(frozen=True)
class GfmTransition:
    src: str
    dst: str
    condition: str
    accepting: bool
    origin: str


@dataclass
class GFM:
    states: list[str]
    initial: str
    transitions: list[GfmTransition]

    @property
    def accepting_transition_count(self) -> int:
        return sum(1 for edge in self.transitions if edge.accepting)


def tdr_formula(n: int) -> str:
    inner = "b"
    for _ in range(n):
        inner = f"X({inner})"
    return f"GF(a & {inner})"


def lib_formula(n: int) -> str:
    terms = []
    for i in range(1, n + 1):
        terms.append(f"(a{i} & X !a{i})")
        terms.append(f"(!a{i} & X a{i})")
    return "GF(" + " | ".join(terms) + ")"


def ncs_formula(n: int) -> str:
    terms = []
    for i in range(n):
        atom = chr(ord("a") + i)
        for _ in range(i):
            atom = f"X({atom})"
        terms.append(atom)
    return "GF(" + " & ".join(terms) + ")"


def build_tdr_nfa(n: int) -> NFA:
    """NFA for the finite pattern a & X^n b."""
    states = [f"q{i}" for i in range(n + 2)]
    final = states[-1]
    transitions = [NfaTransition("q0", "q1", "a")]
    for i in range(1, n):
        transitions.append(NfaTransition(f"q{i}", f"q{i + 1}", "true"))
    transitions.append(NfaTransition(f"q{n}", final, "b"))
    return NFA(states=states, initial="q0", finals=[final], transitions=transitions)


def build_lib_nfa(n: int) -> NFA:
    """NFA for one of n Boolean signals changing value on the next letter."""
    states = ["q0"]
    transitions: list[NfaTransition] = []
    final = "qf"
    for i in range(1, n + 1):
        true_state = f"a{i}_was_true"
        false_state = f"a{i}_was_false"
        states.extend([true_state, false_state])
        transitions.append(NfaTransition("q0", true_state, f"a{i}"))
        transitions.append(NfaTransition("q0", false_state, f"!a{i}"))
        transitions.append(NfaTransition(true_state, final, f"!a{i}"))
        transitions.append(NfaTransition(false_state, final, f"a{i}"))
    states.append(final)
    return NFA(states=states, initial="q0", finals=[final], transitions=transitions)


def build_ncs_nfa(n: int) -> NFA:
    """NFA for a nested conjunction sequence over n consecutive offsets."""
    states = [f"q{i}" for i in range(n + 1)]
    final = states[-1]
    transitions: list[NfaTransition] = []
    for i in range(n):
        atom = chr(ord("a") + i)
        transitions.append(NfaTransition(f"q{i}", f"q{i + 1}", atom))
    return NFA(states=states, initial="q0", finals=[final], transitions=transitions)


def complement_simple_condition(condition: str) -> str:
    """Complement the atom/negated-atom guards used in the benchmark NFAs."""
    if condition == "true":
        raise ValueError("cannot represent complement of true with the simple guard format")
    if condition.startswith("!"):
        return condition[1:]
    return f"!{condition}"


def direct_gfm_from_nfa(nfa: NFA) -> GFM:
    """Apply the paper's reset construction from an NFA for phi to GFM for GF phi."""
    finals = set(nfa.finals)
    gfm_states = [s for s in nfa.states if s not in finals]
    gfm_state_set = set(gfm_states)
    transitions: list[GfmTransition] = []

    by_src: dict[str, list[NfaTransition]] = {s: [] for s in gfm_states}
    for edge in nfa.transitions:
        if edge.src in by_src:
            by_src[edge.src].append(edge)

    for state in gfm_states:
        final_edges: list[NfaTransition] = []
        for edge in by_src[state]:
            if edge.dst in finals:
                final_edges.append(edge)
                transitions.append(
                    GfmTransition(state, nfa.initial, edge.condition, True, "final_reset")
                )
            elif edge.dst in gfm_state_set:
                transitions.append(
                    GfmTransition(state, edge.dst, edge.condition, False, "nfa_progress")
                )
        if not final_edges:
            transitions.append(GfmTransition(state, nfa.initial, "true", False, "reset"))
        elif len(final_edges) == 1:
            reset_condition = complement_simple_condition(final_edges[0].condition)
            transitions.append(GfmTransition(state, nfa.initial, reset_condition, False, "reset"))
        else:
            raise ValueError(
                f"{state} has multiple final-reaching guards; add symbolic disjointness support"
            )

    return GFM(states=gfm_states, initial=nfa.initial, transitions=transitions)


def build_benchmark(spec: dict) -> dict:
    family = spec["family"]
    n = int(spec["n"])
    if family == "TDR":
        nfa = build_tdr_nfa(n)
        formula = tdr_formula(n)
    elif family == "LIB":
        nfa = build_lib_nfa(n)
        formula = lib_formula(n)
    elif family == "NCS":
        nfa = build_ncs_nfa(n)
        formula = ncs_formula(n)
    else:
        raise ValueError(f"Unsupported benchmark family: {family}")

    start = time.perf_counter()
    gfm = direct_gfm_from_nfa(nfa)
    duration = time.perf_counter() - start
    return {
        "name": spec["name"],
        "family": family,
        "n": n,
        "formula": formula,
        "method": "gfm_gf",
        "state_count": len(gfm.states),
        "transition_count": len(gfm.transitions),
        "accepting_transition_count": gfm.accepting_transition_count,
        "construction_time_sec": duration,
        "nfa": {
            "state_count": len(nfa.states),
            "final_state_count": len(nfa.finals),
            "transition_count": len(nfa.transitions),
        },
        "gfm": {
            "states": gfm.states,
            "initial": gfm.initial,
            "transitions": [asdict(edge) for edge in gfm.transitions],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmarks", default="data/gf_benchmarks.json")
    parser.add_argument("--output", default="outputs/gfm_gf_results.json")
    args = parser.parse_args()

    specs = json.loads(Path(args.benchmarks).read_text())["benchmarks"]
    results = [build_benchmark(spec) for spec in specs]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"results": results}, indent=2) + "\n")

    for row in results:
        print(
            f"{row['name']}: {row['state_count']} states, "
            f"{row['accepting_transition_count']} accepting transitions"
        )


if __name__ == "__main__":
    main()
