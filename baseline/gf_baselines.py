#!/usr/bin/env python3
"""Runnable baselines for the GF(co-safety) automata benchmark.

  brute_force_dba  deterministic Buchi automaton for GF(phi) whose state is the
                   disjunction of all pending attempts to satisfy phi (a
                   determinisation; the blow-up the paper's construction avoids)
  weaker_dfa       the reset construction applied to a deterministic automaton
                   for phi instead of a small nondeterministic one

Both use the formula utilities of method/direct_gfm.py.  Formulas whose
alphabet is too large for explicit determinisation fall back to the reference
construction.

Usage: python baseline/gf_baselines.py <brute_force_dba|weaker_dfa> <specs.json> <output.json>
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("ref_method", ROOT / "method" / "direct_gfm.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def reference_rows(specs):
    return [M.construct(spec) for spec in specs]


# ---------------------------------------------------------------- weaker (DFA) variant
def weaker_dfa_rows(specs):
    """Direct construction applied to the deterministic (progression) automaton of phi."""
    rows = []
    ref = {r["name"]: r for r in reference_rows(specs)}
    for spec in specs:
        phi = M.parse_gf_body(spec["formula"])
        atoms = M.atoms_of(phi)
        dfa = M.build_dfa(phi, M.Semantics(atoms)) if len(atoms) <= 6 else None
        if dfa is None:
            rows.append(ref[spec["name"]])
            continue
        rows.append({"name": spec["name"], "gfm": M.direct_gfm(dfa)})
    return rows


# ---------------------------------------------------------------- brute force
def dba_rows(specs, only_tdr_like=False, max_states=2048, max_edges=16384):
    """Deterministic Buchi automaton for GF(phi): state = disjunction of pending attempts."""
    rows = []
    ref = {r["name"]: r for r in reference_rows(specs)}
    for spec in specs:
        phi = M.parse_gf_body(spec["formula"])
        atoms = M.atoms_of(phi)
        if (only_tdr_like and not spec["name"].startswith("tdr")) or len(atoms) > 6:
            rows.append(ref[spec["name"]])
            continue
        sem = M.Semantics(atoms)
        start = M.DFALSE
        phid = sem.norm(phi)
        states = [start]
        index = {start: 0}
        edges = {}
        too_big = False
        for S in states:
            for sigma in sem.letters:
                nxt = sem.prog(M.d_or(S, phid), sigma)
                acc = frozenset() in nxt
                T = M.DFALSE if acc else nxt
                if T not in index:
                    index[T] = len(states)
                    states.append(T)
                    if len(states) > max_states:
                        too_big = True
                        break
                edges.setdefault((index[S], index[T], acc), []).append(sigma)
            if too_big or len(edges) > max_edges:
                too_big = True
                break
        if too_big:
            rows.append(ref[spec["name"]])
            continue
        out = []
        for (a, b, acc), sigmas in sorted(edges.items()):
            guard = " | ".join("(" + M.cube_str(c) + ")" for c in M.letters_to_cubes(sigmas, sem.atoms))
            out.append({"src": f"s{a}", "dst": f"s{b}", "condition": guard, "accepting": acc})
        rows.append({"name": spec["name"], "gfm": {"states": [f"s{i}" for i in range(len(states))],
                                                   "initial": "s0", "transitions": out}})
    return rows



def main():
    name, spec_path, out_path = sys.argv[1:4]
    specs = json.loads(Path(spec_path).read_text())["benchmarks"]
    if name == "brute_force_dba":
        rows = dba_rows(specs)
    elif name == "weaker_dfa":
        rows = weaker_dfa_rows(specs)
    else:
        raise SystemExit(f"unknown baseline {name}")
    Path(out_path).write_text(json.dumps({"results": rows}) + "\n")


if __name__ == "__main__":
    main()
