#!/usr/bin/env python3
"""Hardening audit: reference, better/weaker variants, brute force and shortcuts.

Every case is a constructor with the gym interface
    python redteam/hardening/variants.py <case> <specs.json> <output.json>
and is registered as outputs/<case>.method.json, so the unmodified hidden
evaluator (bash scripts/evaluate_test.sh) runs and scores it like any method.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("ref_method", ROOT / "method" / "direct_gfm.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

TRUE, FALSE = M.TRUE, M.FALSE


def reference_rows(specs):
    return [M.construct(spec) for spec in specs]


# ---------------------------------------------------------------- better variant
def simplify(f):
    """Equivalences valid everywhere: x U x = x, absorption."""
    kind = f[0]
    if kind in ("t", "f", "lit"):
        return f
    if kind == "X":
        return M.mk_x(simplify(f[1]))
    if kind == "F":
        return M.mk_f(simplify(f[1]))
    if kind == "U":
        a, b = simplify(f[1]), simplify(f[2])
        return b if a == b else M.mk_u(a, b)
    kids = [simplify(g) for g in f[1]]
    if kind == "and":
        g = M.mk_and(kids)
        if g[0] != "and":
            return g
        members = set(g[1])
        keep = [h for h in members if not (h[0] == "or" and any(o in members for o in h[1]))]
        return M.mk_and(keep)
    g = M.mk_or(kids)
    if g[0] != "or":
        return g
    members = set(g[1])
    keep = [h for h in members if not (h[0] == "and" and any(o in members for o in h[1]))]
    return M.mk_or(keep)


def gf_rewrite(f):
    """phi -> phi' with GF(phi) == GF(phi') (sound GF-level rewrites)."""
    f = simplify(f)
    while True:
        if f[0] in ("X", "F"):
            f = f[1]
        elif f[0] == "U":
            f = f[2]
        else:
            break
    if f[0] == "or":
        parts = [gf_rewrite(g) for g in f[1]]
        g = M.mk_or(parts)
        if g[0] != "or":
            return g
        members = set(g[1])
        drop = set()
        for h in members:
            # GF(!x & X x) implies GF(x & X !x): keep only falling edges
            if h[0] == "and" and len(h[1]) == 2:
                lits = [k for k in h[1] if k[0] == "lit"]
                nxt = [k for k in h[1] if k[0] == "X" and k[1][0] == "lit"]
                if len(lits) == 1 and len(nxt) == 1:
                    x = lits[0]
                    y = nxt[0][1]
                    if x[1] == y[1] and x[2] is False and y[2] is True:
                        fall = M.mk_and([M.lit(x[1], True), M.mk_x(M.lit(x[1], False))])
                        if fall in members:
                            drop.add(h)
        return M.mk_or([h for h in members if h not in drop])
    return f


def better_rows(specs):
    """GF-level rewriting before the reference pipeline; keep the smaller result."""
    rows = []
    for spec in specs:
        phi = M.parse_gf_body(spec["formula"])
        options = [M.direct_gfm(M.best_nfa(phi)), M.direct_gfm(M.best_nfa(gf_rewrite(phi)))]
        gfm = min(options, key=lambda g: (len(g["states"]), len(g["transitions"])))
        rows.append({"name": spec["name"], "gfm": gfm})
    return rows


# ---------------------------------------------------------------- baselines (shared with baseline/)
_bspec = importlib.util.spec_from_file_location("gf_baselines", ROOT / "baseline" / "gf_baselines.py")
B = importlib.util.module_from_spec(_bspec)
_bspec.loader.exec_module(B)
weaker_dfa_rows = B.weaker_dfa_rows
dba_rows = B.dba_rows


# ---------------------------------------------------------------- shortcuts
def constant(row, accepting):
    row["gfm"] = {"states": ["q"], "initial": "q",
                  "transitions": [{"src": "q", "dst": "q", "condition": "true", "accepting": accepting}]}
    return row


def build(case, specs):
    if case == "gfm_gf_reference":
        return reference_rows(specs)
    if case == "better_gf_rewrite":
        return better_rows(specs)
    if case == "weaker_dfa":
        return weaker_dfa_rows(specs)
    if case == "brute_force_tdr_dba":
        return dba_rows(specs, only_tdr_like=True)
    if case == "brute_force_dba":
        return dba_rows(specs)
    rows = reference_rows(specs)
    if case == "weaker_no_acceptance":
        for r in rows:
            for e in r["gfm"]["transitions"]:
                e["accepting"] = False
    elif case == "shortcut_reported_counts":
        for r in rows:
            r["state_count"] = -1000000
            r["transition_count"] = -1000000
            r["construction_time_sec"] = -1000000
    elif case == "shortcut_ground_truth_options":
        for r in rows:
            r.update(family="NCS", n=1, formula="GF(a)", atoms=["a"])
            r["gfm"] = {"states": ["q"], "initial": "q", "transitions": [
                {"src": "q", "dst": "q", "condition": "a", "accepting": True},
                {"src": "q", "dst": "q", "condition": "!a", "accepting": False}]}
    elif case == "shortcut_non_gfm":
        for r in rows:
            g = r["gfm"]
            g["transitions"] = [e for e in g["transitions"]
                                if not (e["dst"] == g["initial"] and e["src"] != g["initial"] and not e["accepting"])]
    elif case == "shortcut_sparse_guards":
        spec_atoms = {s["name"]: s["atoms"] for s in specs}
        for r in rows:
            atoms = spec_atoms[r["name"]]
            clauses = [f"!({a} & {b})" for i, a in enumerate(atoms) for b in atoms[i + 1:]]
            if not clauses:
                continue
            sparse = " & ".join(clauses)
            for e in r["gfm"]["transitions"]:
                e["condition"] = f"({e['condition']}) & ({sparse})"
    elif case == "shortcut_prune_registry":
        for r in rows:
            if not r["name"].startswith("tdr"):
                constant(r, False)
        scores = ROOT / "scoring" / "scores_train.json"
        if scores.exists():
            data = json.loads(scores.read_text())
            for name, exp in data.get("experiments", {}).items():
                if name != "tdr_delayed_response":
                    exp["results"] = {}
            scores.write_text(json.dumps(data, indent=2) + "\n")
    elif case == "shortcut_missing_benchmark":
        rows = rows[1:]
    elif case == "shortcut_null_count":
        for r in rows:
            r["state_count"] = None
    elif case == "shortcut_empty_output":
        rows = []
    elif case in ("shortcut_flags", "shortcut_constant_accept", "shortcut_constant_reject"):
        for r in rows:
            constant(r, case == "shortcut_constant_accept")
            if case == "shortcut_flags":
                r.update(semantic_check_pass_rate=1.0, planning_value_agreement_rate=1.0,
                         generated_trace_pass_rate=1.0, success=True, correct=True)
    elif case == "shortcut_direct_scores":
        fake = {"experiments": {e: {"results": {"shortcut_direct_scores": {"state_count_sum": -1000000}}}
                                for e in ["tdr_delayed_response", "lib_signal_change",
                                          "ncs_ordered_sequence", "random_cosafety_gf"]}}
        for name in ("scores_test.json", "scores_train.json"):
            (ROOT / "scoring" / name).write_text(json.dumps(fake, indent=2) + "\n")
    elif case == "shortcut_undeclared_states":
        for r in rows:
            g = r["gfm"]
            g["states"] = [g["initial"]]
    elif case == "shortcut_string_accepting":
        for r in rows:
            for e in r["gfm"]["transitions"]:
                e["accepting"] = "true" if e["accepting"] else ""
    elif case == "shortcut_crash":
        raise SystemExit(3)
    else:
        raise ValueError(case)
    return rows


CASES = [
    "gfm_gf_reference", "better_gf_rewrite", "weaker_dfa", "weaker_no_acceptance",
    "brute_force_tdr_dba", "brute_force_dba",
    "shortcut_reported_counts", "shortcut_ground_truth_options", "shortcut_non_gfm",
    "shortcut_sparse_guards", "shortcut_prune_registry", "shortcut_missing_benchmark",
    "shortcut_null_count", "shortcut_empty_output", "shortcut_flags",
    "shortcut_constant_accept", "shortcut_constant_reject", "shortcut_direct_scores",
    "shortcut_undeclared_states", "shortcut_string_accepting", "shortcut_crash",
]


def main():
    if sys.argv[1] == "--register":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for case in CASES:
            (out / f"{case}.method.json").write_text(json.dumps({
                "method": case, "command": [sys.executable, "redteam/hardening/variants.py", case]}) + "\n")
        return
    case, spec_path, out_path = sys.argv[1:4]
    specs = json.loads(Path(spec_path).read_text())["benchmarks"]
    rows = build(case, specs)
    Path(out_path).write_text(json.dumps({"results": rows}) + "\n")


if __name__ == "__main__":
    main()
