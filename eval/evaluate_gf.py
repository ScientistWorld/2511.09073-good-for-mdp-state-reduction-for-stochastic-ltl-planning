#!/usr/bin/env python3
"""Evaluate generated automata for the GF co-safety benchmarks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


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
    paper_targets = {
        row["name"]: row["paper"]["gfm_gf_states"]
        for row in load_json("data/gf_benchmarks.json")["benchmarks"]
    }
    target_matches = sum(row["state_count"] == paper_targets[row["name"]] for row in selected)
    return {
        "state_count_sum": sum(row["state_count"] for row in selected),
        "semantic_check_pass_rate": check_passed / check_total,
        "state_count_target_match_rate": target_matches / len(selected),
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
        }
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
