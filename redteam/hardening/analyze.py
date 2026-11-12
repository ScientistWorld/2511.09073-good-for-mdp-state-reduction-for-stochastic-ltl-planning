#!/usr/bin/env python3
"""Summarise the hardening audit: raw metrics, pairwise and common-population ranks."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H = ROOT / "redteam" / "hardening"
REF = "gfm_gf_reference"
HONEST = ["gfm_gf_reference", "better_gf_rewrite", "weaker_dfa", "brute_force_tdr_dba",
          "brute_force_dba", "weaker_no_acceptance"]


def load(p):
    return json.loads(Path(p).read_text())


def vectors(scores):
    out = {}
    for exp, data in scores["experiments"].items():
        for method, metrics in data["results"].items():
            out.setdefault(method, {})[exp] = metrics
    return out


def rank(ref_def, vecs, cand, population):
    total = 0.0
    for exp, edef in ref_def["experiments"].items():
        w = edef["weight"]
        for m, mdef in edef["metrics"].items():
            vals = [vecs[p][exp][m] for p in population if exp in vecs[p] and m in vecs[p][exp]]
            if len(vals) < 2:
                continue
            mean = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
            if sd == 0:
                continue
            sign = 1.0 if mdef["higher_is_better"] else -1.0
            diff = vecs[cand][exp][m] - vecs[REF][exp][m]
            total += w * abs(mdef["coefficient"]) * sign * diff / sd
    return total


def main():
    ref_def = load(ROOT / "scoring" / "reference.json")
    test = load(H / "scores_test_audit.json")
    diag = load(H / "scores_test_audit_diagnostics.json")
    vecs = vectors(test)
    cases = sorted(vecs)
    summary = {"cases": {}, "reference": vecs[REF]}
    lines = ["| case | failed | TDR S/E | LIB S/E | NCS S/E | RND S/E | Δpair | rank (all cases) | rank (honest cohort) | first error |",
             "|---|---|---|---|---|---|---:|---:|---:|---|"]
    honest = [c for c in HONEST if c in vecs]
    for c in cases:
        pair = rank(ref_def, vecs, c, [REF, c]) if c != REF else 0.0
        common = rank(ref_def, vecs, c, cases)
        hon = rank(ref_def, vecs, c, honest) if c in honest else None
        d = diag["methods"].get(c, {})
        summary["cases"][c] = {"metrics": vecs[c], "failed": d.get("failed"), "errors": d.get("errors", [])[:3],
                               "delta_pair": pair, "rank_all_cases": common, "rank_honest_cohort": hon}
        cells = []
        for exp in ["tdr_delayed_response", "lib_signal_change", "ncs_ordered_sequence", "random_cosafety_gf"]:
            m = vecs[c][exp]
            cells.append(f"{m['state_count_sum']}/{m['transition_count_sum']}")
        err = (d.get("errors") or [""])[0][:70].replace("|", "/")
        lines.append(f"| {c} | {d.get('failed')} | " + " | ".join(cells) +
                     f" | {pair:+.3f} | {common:+.3f} | " + (f"{hon:+.3f}" if hon is not None else "—") + f" | {err} |")
    # default-path and determinism checks
    default = load(H / "default_path_scores_test.json")
    dvec = vectors(default)
    summary["default_path"] = {
        "methods_scored": sorted(dvec),
        "forged_values_present": any(v.get("state_count_sum") == -1000000
                                     for m in dvec.values() for v in m.values()),
        "every_metric_present": all(len(v) == 7 for m in dvec.values() for v in m.values()),
    }
    seeds = {}
    for s in (11, 22):
        sv = vectors(load(H / f"reference_seed{s}.json"))
        r = sv[REF]
        seeds[s] = max(abs(r[e][m] - vecs[REF][e][m]) for e in r for m in r[e])
    summary["reference_seed_max_abs_diff"] = seeds
    train = load(H / "scores_train_audit.json")
    tv = vectors(train)
    summary["train_vs_test_rank_all_cases"] = {c: rank(ref_def, tv, c, sorted(tv)) for c in sorted(tv)}
    (H / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("\n".join(lines))
    print()
    print("default path:", json.dumps(summary["default_path"]))
    print("reference max |diff| across hash seeds:", seeds)


if __name__ == "__main__":
    main()
