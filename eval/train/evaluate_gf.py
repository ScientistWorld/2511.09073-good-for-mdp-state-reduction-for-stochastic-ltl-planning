#!/usr/bin/env python3
"""Train-slice evaluator for generated automata on GF co-safety benchmarks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


SLICE = "train"
GENERATED_TRACE_SEED = 1729
GENERATED_TRACE_COUNT = 8

EXPERIMENTS = {
    "tdr_direct_gf": ["tdr_6", "tdr_8", "tdr_10"],
    "lib_direct_gf": ["lib_6", "lib_8"],
    "ncs_direct_gf": ["ncs_4", "ncs_6", "ncs_8", "ncs_10"],
}


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def discover_artifacts(input_path: str) -> list[Path]:
    path = Path(input_path)
    if path.is_file():
        return [path]
    if path.is_dir():
        artifacts = sorted(p for p in path.glob("*.json") if p.is_file())
        if artifacts:
            return artifacts
        raise FileNotFoundError(f"no JSON method artifacts found in {path}")
    matches = sorted(Path().glob(input_path))
    if matches:
        return [p for p in matches if p.is_file()]
    raise FileNotFoundError(f"method artifact path does not exist: {input_path}")


def artifact_rows(path: Path) -> list[dict]:
    payload = load_json(path)
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise ValueError(f"{path} is not a method artifact with a results list")
    return rows


def method_name_for(row: dict, path: Path) -> str:
    method = row.get("method")
    if isinstance(method, str) and method:
        return method
    stem = path.stem
    if stem.endswith("_results"):
        stem = stem[: -len("_results")]
    return stem


def load_rows_by_method(input_path: str) -> dict[str, list[dict]]:
    by_method: dict[str, dict[str, dict]] = {}
    for path in discover_artifacts(input_path):
        for row in artifact_rows(path):
            method = method_name_for(row, path)
            name = row.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError(f"{path} contains a row without a benchmark name")
            by_method.setdefault(method, {})
            if name in by_method[method]:
                raise ValueError(f"duplicate output for method={method}, benchmark={name}")
            by_method[method][name] = row
    if not by_method:
        raise ValueError("no method rows found")
    return {method: list(rows.values()) for method, rows in sorted(by_method.items())}


class GuardParser:
    def __init__(self, text: str, valuation: set[str]):
        self.text = text.strip()
        self.valuation = valuation
        self.pos = 0

    def parse(self) -> bool:
        if not self.text:
            raise ValueError("empty transition guard")
        value = self.parse_or()
        self.skip_ws()
        if self.pos != len(self.text):
            raise ValueError(f"unexpected guard token at {self.text[self.pos:]!r}")
        return value

    def parse_or(self) -> bool:
        value = self.parse_and()
        while True:
            self.skip_ws()
            if not self.consume("|"):
                return value
            rhs = self.parse_and()
            value = value or rhs

    def parse_and(self) -> bool:
        value = self.parse_not()
        while True:
            self.skip_ws()
            if not self.consume("&"):
                return value
            rhs = self.parse_not()
            value = value and rhs

    def parse_not(self) -> bool:
        self.skip_ws()
        if self.consume("!"):
            return not self.parse_not()
        return self.parse_atom()

    def parse_atom(self) -> bool:
        self.skip_ws()
        if self.consume("("):
            value = self.parse_or()
            self.skip_ws()
            if not self.consume(")"):
                raise ValueError("unclosed guard parenthesis")
            return value
        start = self.pos
        while self.pos < len(self.text) and (
            self.text[self.pos].isalnum() or self.text[self.pos] == "_"
        ):
            self.pos += 1
        atom = self.text[start : self.pos]
        if atom == "true":
            return True
        if atom == "false":
            return False
        if atom:
            return atom in self.valuation
        raise ValueError(f"expected guard atom at {self.text[self.pos:]!r}")

    def consume(self, token: str) -> bool:
        if self.text.startswith(token, self.pos):
            self.pos += len(token)
            return True
        return False

    def skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1


def condition_holds(condition: str, valuation: set[str]) -> bool:
    return GuardParser(condition, valuation).parse()


def accepts_periodic_word(row: dict, period: list[set[str]]) -> bool:
    states = list(row["gfm"]["states"])
    transitions = list(row["gfm"]["transitions"])
    initial = row["gfm"]["initial"]
    period_len = len(period)

    graph: dict[tuple[str, int], list[tuple[tuple[str, int], bool]]] = {}
    for state in states:
        for phase, valuation in enumerate(period):
            node = (state, phase)
            next_phase = (phase + 1) % period_len
            graph[node] = [
                ((edge["dst"], next_phase), bool(edge.get("accepting", False)))
                for edge in transitions
                if edge.get("src") == state and condition_holds(edge.get("condition", "false"), valuation)
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


def wraps(period: list[set[str]], index: int) -> set[str]:
    return period[index % len(period)]


def oracle_accepts(family: str, n: int, period: list[set[str]]) -> bool:
    for phase in range(len(period)):
        if family == "TDR":
            if "a" in wraps(period, phase) and "b" in wraps(period, phase + n):
                return True
        elif family == "LIB":
            for i in range(1, n + 1):
                atom = f"a{i}"
                if (atom in wraps(period, phase)) != (atom in wraps(period, phase + 1)):
                    return True
        elif family == "NCS":
            if all(chr(ord("a") + i) in wraps(period, phase + i) for i in range(n)):
                return True
        else:
            raise ValueError(f"unknown family: {family}")
    return False


def canonical_traces(family: str, n: int) -> list[list[set[str]]]:
    if family == "TDR":
        positive = [set() for _ in range(n + 1)]
        positive[0].add("a")
        positive[n].add("b")
        negative = [set() for _ in range(n + 1)]
        negative[0].add("a")
        if n > 0:
            negative[n - 1].add("b")
        return [positive, negative]
    if family == "LIB":
        return [[{"a1"}, set()], [{f"a{i}" for i in range(1, n + 1)}]]
    if family == "NCS":
        return [[{chr(ord("a") + i)} for i in range(n)], [{chr(ord("a") + i)} for i in range(max(n - 1, 1))]]
    raise ValueError(f"unknown family: {family}")


def semantic_traces(family: str, n: int) -> list[list[set[str]]]:
    traces = list(canonical_traces(family, n))
    if family == "TDR":
        shifted = [set() for _ in range(n + 3)]
        shifted[1].add("a")
        shifted[n + 1].add("b")
        b_only = [set(), {"b"}, set()]
        traces.extend([shifted, b_only])
    elif family == "LIB":
        signal_n = f"a{n}"
        traces.extend([[set(), {signal_n}], [set()], [{f"a{i}" for i in range(1, n + 1)}, {f"a{i}" for i in range(1, n + 1)}]])
    elif family == "NCS":
        shifted = [set() for _ in range(n + 2)]
        for i in range(n):
            shifted[i + 1].add(chr(ord("a") + i))
        missing_last = [{chr(ord("a") + i)} for i in range(max(n - 1, 1))]
        reversed_atoms = [{chr(ord("a") + i)} for i in reversed(range(n))]
        traces.extend([shifted, missing_last, reversed_atoms])
    else:
        raise ValueError(f"unknown family: {family}")
    return traces


def atoms_for_family(family: str, n: int) -> list[str]:
    if family == "TDR":
        return ["a", "b"]
    if family == "LIB":
        return [f"a{i}" for i in range(1, n + 1)]
    if family == "NCS":
        return [chr(ord("a") + i) for i in range(n)]
    raise ValueError(f"unknown family: {family}")


def generated_traces(family: str, n: int) -> list[list[set[str]]]:
    atoms = atoms_for_family(family, n)
    state = (GENERATED_TRACE_SEED + 97 * n + 17 * len(atoms)) & 0x7FFFFFFF
    traces: list[list[set[str]]] = []
    for trace_index in range(GENERATED_TRACE_COUNT):
        state = (1103515245 * state + 12345 + trace_index) & 0x7FFFFFFF
        positive = trace_index % 2 == 0
        if family == "TDR":
            period_len = n + 2 + (state % 3)
            start = state % (period_len - n)
            period = [set() for _ in range(period_len)]
            period[start].add("a")
            offset = n if positive else n + 1
            period[(start + offset) % period_len].add("b")
        elif family == "LIB":
            period_len = 2 + (state % 4)
            base = {
                atom
                for atom_index, atom in enumerate(atoms)
                if ((state >> (atom_index % 16)) ^ atom_index) & 1
            }
            period = [set(base) for _ in range(period_len)]
            if positive:
                atom = atoms[state % len(atoms)]
                phase = (state >> 5) % period_len
                if atom in period[phase]:
                    period[phase].remove(atom)
                else:
                    period[phase].add(atom)
        elif family == "NCS":
            period_len = n + 2 + (state % 3)
            start = state % (period_len - n + 1)
            period = [set() for _ in range(period_len)]
            missing = (state >> 4) % n
            for atom_index, atom in enumerate(atoms):
                if positive or atom_index != missing:
                    period[(start + atom_index) % period_len].add(atom)
        else:
            raise ValueError(f"unknown family: {family}")
        traces.append(period)
    return traces


def count_trace_agreements(row: dict, traces: Iterable[list[set[str]]]) -> tuple[int, int]:
    family = row["family"]
    n = int(row["n"])
    passed = 0
    total = 0
    for trace in traces:
        expected = oracle_accepts(family, n, trace)
        observed = accepts_periodic_word(row, trace)
        passed += int(expected == observed)
        total += 1
    return passed, total


def aggregate(rows: list[dict], names: list[str]) -> dict:
    by_name = {row["name"]: row for row in rows}
    missing = sorted(set(names) - set(by_name))
    if missing:
        raise ValueError(f"missing benchmark outputs for {SLICE} slice: {missing}")
    selected = [by_name[name] for name in names]

    semantic_counts = [count_trace_agreements(row, semantic_traces(row["family"], int(row["n"]))) for row in selected]
    semantic_passed = sum(passed for passed, _ in semantic_counts)
    semantic_total = sum(total for _, total in semantic_counts)

    trace_counts = [count_trace_agreements(row, canonical_traces(row["family"], int(row["n"]))) for row in selected]
    trace_passed = sum(passed for passed, _ in trace_counts)
    trace_total = sum(total for _, total in trace_counts)

    generated_counts = [count_trace_agreements(row, generated_traces(row["family"], int(row["n"]))) for row in selected]
    generated_passed = sum(passed for passed, _ in generated_counts)
    generated_total = sum(total for _, total in generated_counts)

    state_count_sum = sum(int(row.get("state_count", len(row["gfm"]["states"]))) for row in selected)
    transition_count_sum = sum(int(row.get("transition_count", len(row["gfm"]["transitions"]))) for row in selected)
    size_weighted_denominator = sum(int(row["n"]) for row in selected)
    size_weighted_state_sum = sum(
        int(row.get("state_count", len(row["gfm"]["states"]))) * int(row["n"])
        for row in selected
    )

    return {
        "state_count_size_weighted_mean": size_weighted_state_sum / size_weighted_denominator,
        "state_count_per_formula": state_count_sum / len(selected),
        "state_count_sum": state_count_sum,
        "transition_count_sum": transition_count_sum,
        "semantic_check_pass_rate": semantic_passed / semantic_total,
        "trace_semantics_pass_rate": trace_passed / trace_total,
        "generated_trace_pass_rate": generated_passed / generated_total,
    }


def build_scores(rows_by_method: dict[str, list[dict]]) -> dict:
    return {
        "experiments": {
            exp_name: {
                "results": {
                    method: aggregate(rows, names)
                    for method, rows in rows_by_method.items()
                }
            }
            for exp_name, names in EXPERIMENTS.items()
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="outputs")
    parser.add_argument("--output", default="scoring/scores_train.json")
    args = parser.parse_args()

    scores = build_scores(load_rows_by_method(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps({"slice": SLICE, "output": str(output), "methods": sorted(next(iter(scores["experiments"].values()))["results"])}, indent=2))


if __name__ == "__main__":
    main()
