#!/usr/bin/env python3
"""Evaluate generated automata for the GF co-safety benchmarks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def condition_holds(condition: str, valuation: set[str]) -> bool:
    """Evaluate the simple symbolic guards emitted by method/direct_gfm.py."""
    condition = condition.strip()
    if condition == "true":
        return True
    if condition.startswith("!"):
        return condition[1:] not in valuation
    return condition in valuation


def accepts_periodic_word(row: dict, period: list[set[str]]) -> bool:
    """Check nondeterministic Buchi acceptance on an infinite periodic word.

    The generated automata are small.  For a purely periodic input word, Buchi
    acceptance reduces to reachability of a product SCC that contains at least
    one accepting transition.
    """
    states = row["gfm"]["states"]
    transitions = row["gfm"]["transitions"]
    initial = row["gfm"]["initial"]
    period_len = len(period)

    graph: dict[tuple[str, int], list[tuple[tuple[str, int], bool]]] = {}
    for state in states:
        for phase, valuation in enumerate(period):
            node = (state, phase)
            next_phase = (phase + 1) % period_len
            graph[node] = [
                ((edge["dst"], next_phase), bool(edge["accepting"]))
                for edge in transitions
                if edge["src"] == state and condition_holds(edge["condition"], valuation)
            ]

    start = (initial, 0)
    reachable: set[tuple[str, int]] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in reachable:
            continue
        reachable.add(node)
        stack.extend(dst for dst, _ in graph.get(node, []) if dst not in reachable)

    order: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()

    def dfs(node: tuple[str, int]) -> None:
        seen.add(node)
        for dst, _ in graph.get(node, []):
            if dst in reachable and dst not in seen:
                dfs(dst)
        order.append(node)

    for node in reachable:
        if node not in seen:
            dfs(node)

    reverse: dict[tuple[str, int], list[tuple[str, int]]] = {node: [] for node in graph}
    for src, edges in graph.items():
        for dst, _ in edges:
            reverse.setdefault(dst, []).append(src)

    assigned: set[tuple[str, int]] = set()
    for node in reversed(order):
        if node in assigned:
            continue
        component: set[tuple[str, int]] = set()
        stack = [node]
        while stack:
            cur = stack.pop()
            if cur in assigned:
                continue
            assigned.add(cur)
            component.add(cur)
            stack.extend(pred for pred in reverse.get(cur, []) if pred in reachable and pred not in assigned)

        if any(
            accepting and dst in component
            for src in component
            for dst, accepting in graph.get(src, [])
        ):
            return True

    return False


def trace_semantic_checks(row: dict) -> tuple[int, int]:
    family = row["family"]
    n = int(row["n"])

    if family == "TDR":
        positive = [set() for _ in range(n + 1)]
        positive[0].add("a")
        positive[n].add("b")
        negative = [set() for _ in range(n + 1)]
        negative[0].add("a")
        if n > 0:
            negative[n - 1].add("b")
    elif family == "LIB":
        positive = [{"a1"}, set()]
        negative = [{f"a{i}" for i in range(1, n + 1)}]
    elif family == "NCS":
        positive = [{chr(ord("a") + i)} for i in range(n)]
        negative = [{chr(ord("a") + i)} for i in range(max(n - 1, 1))]
    else:
        raise ValueError(f"unknown family: {family}")

    passed = int(accepts_periodic_word(row, positive))
    passed += int(not accepts_periodic_word(row, negative))
    return passed, 2


def semantic_checks(row: dict) -> tuple[int, int]:
    """Return passed and total lightweight checks for the family semantics."""
    family = row["family"]
    n = int(row["n"])
    states = set(row["gfm"]["states"])
    transitions = row["gfm"]["transitions"]
    total = 0
    passed = 0

    total += 1
    passed += row["gfm"]["initial"] in states

    total += 1
    passed += any(t["src"] == "q0" and t["dst"] == "q0" and t["origin"] == "reset" for t in transitions)

    if family == "TDR":
        total += 1
        passed += row["state_count"] == n + 1
        total += 1
        passed += any(
            t["src"] == f"q{n}" and t["dst"] == "q0" and t["condition"] == "b" and t["accepting"]
            for t in transitions
        )
    elif family == "LIB":
        total += 1
        passed += row["state_count"] == 2 * n + 1
        total += 1
        passed += all(
            any(
                t["src"] == f"a{i}_was_true"
                and t["dst"] == "q0"
                and t["condition"] == f"!a{i}"
                and t["accepting"]
                for t in transitions
            )
            and any(
                t["src"] == f"a{i}_was_false"
                and t["dst"] == "q0"
                and t["condition"] == f"a{i}"
                and t["accepting"]
                for t in transitions
            )
            for i in range(1, n + 1)
        )
    elif family == "NCS":
        total += 1
        passed += row["state_count"] == n
        total += 1
        passed += all(
            any(
                t["src"] == f"q{i}"
                and t["dst"] == f"q{i + 1}"
                and t["condition"] == chr(ord("a") + i)
                and not t["accepting"]
                for t in transitions
            )
            for i in range(n - 1)
        )
        total += 1
        passed += any(
            t["src"] == f"q{n - 1}"
            and t["dst"] == "q0"
            and t["condition"] == chr(ord("a") + n - 1)
            and t["accepting"]
            for t in transitions
        )
    else:
        raise ValueError(f"unknown family: {family}")

    return passed, total


def aggregate(rows: list[dict], names: list[str]) -> dict:
    selected = [row for row in rows if row["name"] in names]
    if len(selected) != len(names):
        missing = sorted(set(names) - {row["name"] for row in selected})
        raise ValueError(f"missing benchmark outputs: {missing}")

    checks = [semantic_checks(row) for row in selected]
    check_passed = sum(p for p, _ in checks)
    check_total = sum(t for _, t in checks)
    trace_checks = [trace_semantic_checks(row) for row in selected]
    trace_passed = sum(p for p, _ in trace_checks)
    trace_total = sum(t for _, t in trace_checks)
    return {
        "state_count_sum": sum(row["state_count"] for row in selected),
        "semantic_check_pass_rate": check_passed / check_total,
        "trace_semantics_pass_rate": trace_passed / trace_total,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="outputs/gfm_gf_results.json")
    parser.add_argument("--output", default="scoring/scores.json")
    args = parser.parse_args()

    rows = load_json(args.input)["results"]
    for spec in load_json("data/gf_benchmarks.json")["benchmarks"]:
        for row in rows:
            if row["name"] == spec["name"]:
                row["paper"] = spec["paper"]

    scores = {
        "experiments": {
            "tdr_direct_gf": {
                "results": {
                    "gfm_gf": aggregate(rows, ["tdr_6", "tdr_7", "tdr_8", "tdr_9", "tdr_10"])
                }
            },
            "lib_direct_gf": {
                "results": {
                    "gfm_gf": aggregate(rows, ["lib_6", "lib_7", "lib_8", "lib_9"])
                }
            },
            "ncs_direct_gf": {
                "results": {
                    "gfm_gf": aggregate(
                        rows,
                        [
                            "ncs_4",
                            "ncs_5",
                            "ncs_6",
                            "ncs_7",
                            "ncs_8",
                            "ncs_9",
                            "ncs_10",
                            "ncs_11",
                        ],
                    )
                }
            },
        }
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
