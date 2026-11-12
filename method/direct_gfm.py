#!/usr/bin/env python3
"""Direct GFM construction for GF(phi), phi co-safety (Section 6 of
"Good-for-MDP State Reduction for Stochastic LTL Planning").

Pipeline, as in the paper:
  1. Build an NFA N_phi for the co-safety body phi with L_*(N_phi).tt^omega = [phi].
     The NFA is obtained from phi by partial derivatives (linear forms): every
     state is a residual obligation (a conjunction of subformulas of phi), the
     transitions are labelled by cubes over the atomic propositions, and the single
     final state is the discharged obligation `true`.
  2. Build the Buchi automaton A for GF(phi):
       Q_A    = non-final NFA states reachable from q0 (plus q0),
       delta  = NFA progress transitions that stay non-final, plus a reset to q0
                on every letter from every state,
       alpha  = reset transitions (q, sigma, q0) for which some NFA successor of q
                on sigma is final.
     A recognises GF(phi) and is good-for-MDPs (Theorem 5).

Usage (gym interface):
  python method/direct_gfm.py <specs.json> <output.json>
where specs.json is {"benchmarks": [{"name", "formula": "GF(...)", "atoms"}]}.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# LTL co-safety AST (hash-consed tuples; and/or are flattened frozensets)
# ---------------------------------------------------------------------------

TRUE = ("t",)
FALSE = ("f",)


def lit(name, positive=True):
    return ("lit", name, positive)


def mk_and(items):
    flat = set()
    stack = list(items)
    while stack:
        f = stack.pop()
        if f == TRUE:
            continue
        if f == FALSE:
            return FALSE
        if f[0] == "and":
            stack.extend(f[1])
        else:
            flat.add(f)
    for f in flat:
        if f[0] == "lit" and ("lit", f[1], not f[2]) in flat:
            return FALSE
    if not flat:
        return TRUE
    if len(flat) == 1:
        return next(iter(flat))
    return ("and", frozenset(flat))


def mk_or(items):
    flat = set()
    stack = list(items)
    while stack:
        f = stack.pop()
        if f == FALSE:
            continue
        if f == TRUE:
            return TRUE
        if f[0] == "or":
            stack.extend(f[1])
        else:
            flat.add(f)
    for f in flat:
        if f[0] == "lit" and ("lit", f[1], not f[2]) in flat:
            return TRUE
    if not flat:
        return FALSE
    if len(flat) == 1:
        return next(iter(flat))
    return ("or", frozenset(flat))


def mk_x(f):
    return f if f in (TRUE, FALSE) else ("X", f)


def mk_f(f):
    return f if f in (TRUE, FALSE) or f[0] == "F" else ("F", f)


def mk_u(f, g):
    if g in (TRUE, FALSE) or f == FALSE or f == g:
        return g
    if f == TRUE:
        return mk_f(g)
    return ("U", f, g)


def fmt(f):
    kind = f[0]
    if kind == "t":
        return "true"
    if kind == "f":
        return "false"
    if kind == "lit":
        return f[1] if f[2] else "!" + f[1]
    if kind in ("and", "or"):
        sep = " & " if kind == "and" else " | "
        return sep.join(sorted(_paren(g) for g in f[1]))
    if kind == "X":
        return "X(" + fmt(f[1]) + ")"
    if kind == "F":
        return "F(" + fmt(f[1]) + ")"
    if kind == "U":
        return _paren(f[1]) + " U " + _paren(f[2])
    if kind == "G":
        return "G(" + fmt(f[1]) + ")"
    raise ValueError(kind)


def _paren(f):
    s = fmt(f)
    return "(" + s + ")" if f[0] in ("and", "or", "U") else s


def children_sorted(f):
    return sorted(f[1], key=fmt)


class Parser:
    TOKEN = re.compile(r"\s*(?:(?P<id>[a-z_][a-z0-9_]*)|(?P<op>[XFGU]|[()!&|]))")

    def __init__(self, text):
        self.toks = []
        pos = 0
        text = text.strip()
        while pos < len(text):
            m = self.TOKEN.match(text, pos)
            if not m or m.end() == pos:
                raise ValueError(f"bad token near {text[pos:pos + 20]!r}")
            self.toks.append(m.group("id") or m.group("op"))
            pos = m.end()
            while pos < len(text) and text[pos].isspace():
                pos += 1
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self, tok=None):
        cur = self.peek()
        if cur is None or (tok is not None and cur != tok):
            raise ValueError(f"expected {tok!r}, got {cur!r}")
        self.i += 1
        return cur

    def parse(self):
        f = self.p_or()
        if self.peek() is not None:
            raise ValueError("trailing tokens")
        return f

    def p_or(self):
        items = [self.p_and()]
        while self.peek() == "|":
            self.take()
            items.append(self.p_and())
        return mk_or(items) if len(items) > 1 else items[0]

    def p_and(self):
        items = [self.p_until()]
        while self.peek() == "&":
            self.take()
            items.append(self.p_until())
        return mk_and(items) if len(items) > 1 else items[0]

    def p_until(self):
        left = self.p_unary()
        if self.peek() == "U":
            self.take()
            return mk_u(left, self.p_until())
        return left

    def p_unary(self):
        tok = self.peek()
        if tok == "!":
            self.take()
            inner = self.p_unary()
            if inner in (TRUE, FALSE):
                return FALSE if inner == TRUE else TRUE
            if inner[0] != "lit":
                raise ValueError("negation only on atoms (co-safety syntax)")
            return ("lit", inner[1], not inner[2])
        if tok == "X":
            self.take()
            return mk_x(self.p_unary())
        if tok == "F":
            self.take()
            return mk_f(self.p_unary())
        if tok == "G":
            self.take()
            return ("G", self.p_unary())
        if tok == "(":
            self.take()
            f = self.p_or()
            self.take(")")
            return f
        if tok is None:
            raise ValueError("unexpected end of formula")
        self.take()
        if tok == "true":
            return TRUE
        if tok == "false":
            return FALSE
        return lit(tok)


def parse_gf_body(formula):
    f = Parser(formula).parse()
    if f[0] != "G" or f[1][0] != "F":
        raise ValueError(f"expected GF(phi), got {formula!r}")
    return f[1][1]


# ---------------------------------------------------------------------------
# Step 1: NFA for the co-safety body via partial derivatives (linear forms)
# ---------------------------------------------------------------------------
# A cube is a frozenset of (atom, polarity) literals; the empty cube is `true`.

def conjoin_cubes(c1, c2):
    merged = set(c1) | set(c2)
    for atom, pol in merged:
        if (atom, not pol) in merged:
            return None
    return frozenset(merged)


def split_or(f):
    if f[0] == "or":
        return children_sorted(f)
    return [f]


class LinearForms:
    """LF(phi) = set of (cube, residual): reading a letter satisfying `cube` leaves
    the obligation `residual` for the rest of the word (TRUE = discharged)."""

    def __init__(self):
        self.memo = {}

    def __call__(self, f):
        hit = self.memo.get(f)
        if hit is not None:
            return hit
        kind = f[0]
        if kind == "t":
            res = [(frozenset(), TRUE)]
        elif kind == "f":
            res = []
        elif kind == "lit":
            res = [(frozenset([(f[1], f[2])]), TRUE)]
        elif kind == "X":
            res = [(frozenset(), f[1])]
        elif kind == "or":
            res = [pair for g in children_sorted(f) for pair in self(g)]
        elif kind == "and":
            res = [(frozenset(), TRUE)]
            for g in children_sorted(f):
                nxt = []
                for c1, r1 in res:
                    for c2, r2 in self(g):
                        c = conjoin_cubes(c1, c2)
                        if c is None:
                            continue
                        r = mk_and([r1, r2])
                        if r != FALSE:
                            nxt.append((c, r))
                res = nxt
        elif kind == "F":
            res = list(self(f[1])) + [(frozenset(), f)]
        elif kind == "U":
            res = list(self(f[2])) + [
                (c, mk_and([r, f])) for c, r in self(f[1]) if mk_and([r, f]) != FALSE
            ]
        else:
            raise ValueError(f"not a co-safety operator: {kind}")
        # partial derivatives: split disjunctive residuals into separate targets
        out = []
        seen = set()
        for c, r in res:
            for target in split_or(r):
                key = (c, target)
                if target != FALSE and key not in seen:
                    seen.add(key)
                    out.append(key)
        self.memo[f] = out
        return out


def build_nfa(phi):
    """Return (states, initial, transitions, final) with transitions (src, cube, dst)."""
    lf = LinearForms()
    initial = phi
    states = [initial]
    index = {initial: 0}
    transitions = []
    queue = [initial]
    while queue:
        q = queue.pop(0)
        if q == TRUE:
            continue
        for cube, r in lf(q):
            if r not in index:
                index[r] = len(states)
                states.append(r)
                queue.append(r)
            transitions.append((q, cube, r))
    return states, initial, transitions, TRUE


# ---------------------------------------------------------------------------
# Language-preserving NFA reductions (standard automata-tool post-processing;
# the paper builds its NFAs with an optimising tool chain).  Residual languages
# are compared exactly with formula progression.
# ---------------------------------------------------------------------------

def atoms_of(f, acc=None):
    acc = set() if acc is None else acc
    if f[0] == "lit":
        acc.add(f[1])
    elif f[0] in ("and", "or"):
        for g in f[1]:
            atoms_of(g, acc)
    elif f[0] in ("X", "F", "G"):
        atoms_of(f[1], acc)
    elif f[0] == "U":
        atoms_of(f[1], acc)
        atoms_of(f[2], acc)
    return acc


DTRUE = frozenset([frozenset()])
DFALSE = frozenset()


def _absorb(clauses):
    kept = []
    for c in sorted(set(clauses), key=len):
        if not any(k <= c for k in kept):
            kept.append(c)
    return frozenset(kept)


def _clause_and(c1, c2):
    u = c1 | c2
    for t in u:
        if t[0] == "lit" and ("lit", t[1], not t[2]) in u:
            return None
    return u


def d_or(*ds):
    return _absorb([c for d in ds for c in d])


def d_and(d1, d2):
    out = []
    for c1 in d1:
        for c2 in d2:
            c = _clause_and(c1, c2)
            if c is not None:
                out.append(c)
    return _absorb(out)


class Semantics:
    """Exact language checks for co-safety residuals over a small alphabet.

    Residuals are progressed in a canonical DNF (frozenset of clauses, a clause a
    frozenset of literal/X/F/U terms) with absorption, so progression is finite.
    """

    LIMIT = 20000

    def __init__(self, atoms):
        self.atoms = sorted(atoms)
        self.letters = [frozenset(a for a, v in zip(self.atoms, vals) if v)
                        for vals in itertools.product([False, True], repeat=len(self.atoms))]
        self.dmemo = {}
        self.tmemo = {}
        self.pmemo = {}
        self.vmemo = {}
        self.imemo = {}

    def norm(self, f):
        if isinstance(f, frozenset):
            return f
        hit = self.dmemo.get(f)
        if hit is not None:
            return hit
        k = f[0]
        if k == "t":
            r = DTRUE
        elif k == "f":
            r = DFALSE
        elif k in ("lit", "X", "F", "U"):
            r = frozenset([frozenset([f])])
        elif k == "and":
            r = DTRUE
            for g in f[1]:
                r = d_and(r, self.norm(g))
        elif k == "or":
            r = d_or(*[self.norm(g) for g in f[1]])
        else:
            raise ValueError(k)
        self.dmemo[f] = r
        return r

    def term(self, t, sigma):
        key = (t, sigma)
        hit = self.tmemo.get(key)
        if hit is not None:
            return hit
        k = t[0]
        if k == "lit":
            r = DTRUE if ((t[1] in sigma) == t[2]) else DFALSE
        elif k == "X":
            r = self.norm(t[1])
        elif k == "F":
            r = d_or(self.prog(t[1], sigma), frozenset([frozenset([t])]))
        else:
            r = d_or(self.prog(t[2], sigma), d_and(self.prog(t[1], sigma), frozenset([frozenset([t])])))
        self.tmemo[key] = r
        return r

    def prog(self, f, sigma):
        d = self.norm(f)
        key = (d, sigma)
        hit = self.pmemo.get(key)
        if hit is not None:
            return hit
        out = []
        for clause in d:
            acc = DTRUE
            for t in clause:
                acc = d_and(acc, self.term(t, sigma))
                if not acc:
                    break
            out.extend(acc)
        r = _absorb(out)
        self.pmemo[key] = r
        return r

    def valid(self, f):
        """True iff every word satisfies f (no infinite path avoiding TRUE)."""
        f = self.norm(f)
        if f in self.vmemo:
            return self.vmemo[f]
        if f == DTRUE:
            return True
        color = {f: 1}
        ok = True
        stack = [(f, iter(self.letters))]
        count = 0
        while stack and ok:
            node, it = stack[-1]
            advanced = False
            for sigma in it:
                g = self.prog(node, sigma)
                if g == DTRUE:
                    continue
                if g == DFALSE or color.get(g) == 1:
                    ok = False
                    break
                if g not in color:
                    count += 1
                    if count > self.LIMIT:
                        ok = False
                        break
                    color[g] = 1
                    stack.append((g, iter(self.letters)))
                    advanced = True
                    break
            if not ok or advanced:
                continue
            color[node] = 2
            stack.pop()
        self.vmemo[f] = ok
        return ok

    def unsat(self, f):
        f = self.norm(f)
        seen = {f}
        stack = [f]
        while stack:
            g = stack.pop()
            if g == DTRUE:
                return False
            for sigma in self.letters:
                h = self.prog(g, sigma)
                if h == DTRUE:
                    return False
                if h != DFALSE and h not in seen:
                    seen.add(h)
                    if len(seen) > self.LIMIT:
                        return False
                    stack.append(h)
        return True

    def included(self, f1, f2):
        """True iff L(f1) is a subset of L(f2) (conservative False when too large)."""
        key = (self.norm(f1), self.norm(f2))
        if key in self.imemo:
            return self.imemo[key]
        result = True
        seen = {key}
        stack = [key]
        while stack and result:
            p1, p2 = stack.pop()
            if p1 == DFALSE or p2 == DTRUE:
                continue
            if p1 == DTRUE:
                if not self.valid(p2):
                    result = False
                continue
            if p2 == DFALSE:
                if not self.unsat(p1):
                    result = False
                continue
            for sigma in self.letters:
                nxt = (self.prog(p1, sigma), self.prog(p2, sigma))
                if nxt not in seen:
                    seen.add(nxt)
                    if len(seen) > self.LIMIT:
                        result = False
                        break
                    stack.append(nxt)
        self.imemo[key] = result
        return result

    def equivalent(self, f1, f2):
        return self.norm(f1) == self.norm(f2) or (self.included(f1, f2) and self.included(f2, f1))


def cube_implies(c1, c2):
    """Every letter satisfying cube c1 satisfies cube c2."""
    return c2 <= c1


def reduce_nfa(nfa, sem):
    states, q0, transitions, final = nfa
    out = {}
    for src, cube, dst in transitions:
        out.setdefault(src, []).append((cube, dst))
    for _ in range(3):
        # (a) merge language-equivalent residual states; valid residuals are final
        live = _reachable(q0, out, final)
        reps = []
        rep_of = {}
        for q in live:
            if q != q0 and sem.valid(q):
                rep_of[q] = final
                continue
            for r in reps:
                if sem.equivalent(q, r):
                    rep_of[q] = r
                    break
            else:
                reps.append(q)
                rep_of[q] = q
        rep_of[final] = final
        new_out = {}
        for q in reps:
            pairs = []
            seen = set()
            for cube, dst in out.get(q, []):
                key = (cube, rep_of.get(dst, dst))
                if key not in seen:
                    seen.add(key)
                    pairs.append(key)
            # (b) drop a target whose language is covered by another target on a weaker guard
            kept = []
            for i, (c1, t1) in enumerate(pairs):
                dominated = False
                for j, (c2, t2) in enumerate(pairs):
                    if i == j or not cube_implies(c1, c2):
                        continue
                    if t2 == final or sem.included(t1, t2):
                        mutual = cube_implies(c2, c1) and (t1 == final or sem.included(t2, t1))
                        if not mutual or j < i:
                            dominated = True
                            break
                if not dominated:
                    kept.append((c1, t1))
            new_out[q] = kept
        changed = new_out != {q: out.get(q, []) for q in reps}
        out = new_out
        if not changed:
            break
    live = _reachable(q0, out, final)
    trans = [(q, c, d) for q in live for c, d in out.get(q, [])]
    return live + [final], q0, trans, final


def _reachable(q0, out, final):
    order = [q0]
    seen = {q0}
    for q in order:
        for _, dst in out.get(q, []):
            if dst != final and dst not in seen:
                seen.add(dst)
                order.append(dst)
    return order


def build_dfa(phi, sem, limit=4096):
    """Deterministic automaton for phi by progression, states merged up to language
    equivalence (an NFA in particular); None when too large."""
    start = sem.norm(phi)
    reps = [start]
    trans = []
    for q in reps:
        by_target = {}
        for sigma in sem.letters:
            r = sem.prog(q, sigma)
            if r == DFALSE:
                continue
            if r != DTRUE:
                if sem.valid(r):
                    r = DTRUE
                else:
                    match = next((s for s in reps if sem.equivalent(r, s)), None)
                    if match is None:
                        reps.append(r)
                        if len(reps) > limit:
                            return None
                        match = r
                    r = match
            by_target.setdefault(r, []).append(sigma)
        for r, sigmas in by_target.items():
            for cube in letters_to_cubes(sigmas, sem.atoms):
                trans.append((q, cube, r))
    return reps + [DTRUE], start, trans, DTRUE


def letters_to_cubes(sigmas, atoms):
    """Cover a set of letters by cubes (prime implicants, greedy cover)."""
    terms = {tuple(1 if a in s else 0 for a in atoms) for s in sigmas}
    primes = set()
    current = set(terms)
    while current:
        merged = set()
        used = set()
        cur = sorted(current)
        for i, t1 in enumerate(cur):
            for t2 in cur[i + 1:]:
                diff = [k for k in range(len(atoms)) if t1[k] != t2[k]]
                if len(diff) == 1 and 2 not in (t1[diff[0]], t2[diff[0]]):
                    m = list(t1)
                    m[diff[0]] = 2
                    merged.add(tuple(m))
                    used.add(t1)
                    used.add(t2)
        primes |= current - used
        current = merged
    uncovered = set(terms)
    cover = []

    def covers(p, t):
        return all(pv == 2 or pv == tv for pv, tv in zip(p, t))

    for p in sorted(primes, key=lambda p: (-sum(v == 2 for v in p), p)):
        if any(covers(p, t) for t in uncovered):
            cover.append(p)
            uncovered = {t for t in uncovered if not covers(p, t)}
        if not uncovered:
            break
    return [frozenset((a, bool(v)) for a, v in zip(atoms, p) if v != 2) for p in cover]


def best_nfa(phi):
    """NFA for phi used by the direct construction: the partial-derivative NFA with
    language-preserving reductions, or the merged deterministic automaton when that
    yields a smaller GFM automaton."""
    raw = build_nfa(phi)
    atoms = atoms_of(phi)
    if len(atoms) > 6:
        return raw
    sem = Semantics(atoms)
    candidates = [reduce_nfa(raw, sem)]
    dfa = build_dfa(phi, sem)
    if dfa is not None:
        candidates.append(reduce_nfa(dfa, sem))

    def cost(nfa):
        g = direct_gfm(nfa)
        return (len(g["states"]), len(g["transitions"]))

    return min(candidates, key=cost)


# ---------------------------------------------------------------------------
# Step 2: direct GFM construction for GF(phi) from the NFA (Section 6)
# ---------------------------------------------------------------------------

def cube_str(cube):
    if not cube:
        return "true"
    return " & ".join(a if pol else "!" + a for a, pol in sorted(cube))


def disjunction_str(cubes):
    cubes = sorted(set(cubes), key=cube_str)
    if any(not c for c in cubes):
        return "true"
    if len(cubes) == 1:
        return cube_str(cubes[0])
    return " | ".join("(" + cube_str(c) + ")" for c in cubes)


def disjunction_valid(cubes):
    """Whether the disjunction of cubes covers every letter."""
    if any(not c for c in cubes):
        return True
    atoms = sorted({a for c in cubes for a, _ in c})
    for values in itertools.product([False, True], repeat=len(atoms)):
        assignment = dict(zip(atoms, values))
        if not any(all(assignment[a] == pol for a, pol in c) for c in cubes):
            return False
    return True


def direct_gfm(nfa):
    states, q0, transitions, final = nfa
    out = {}
    for src, cube, dst in transitions:
        out.setdefault(src, []).append((cube, dst))
    # Q_A: non-final states reachable from q0 through non-final progress
    reach = [q0]
    seen = {q0}
    for q in reach:
        for cube, dst in out.get(q, []):
            if dst != final and dst not in seen:
                seen.add(dst)
                reach.append(dst)
    name = {q: f"q{i}" for i, q in enumerate(reach)}
    edges = []
    for q in reach:
        progress = {}
        accepting_cubes = []
        for cube, dst in out.get(q, []):
            if dst == final:
                accepting_cubes.append(cube)
            elif dst != q0:
                progress.setdefault(dst, []).append(cube)
            # dst == q0 coincides with the reset transition below
        for dst in sorted(progress, key=lambda d: name[d]):
            edges.append({"src": name[q], "dst": name[dst],
                          "condition": disjunction_str(progress[dst]),
                          "accepting": False, "origin": "nfa_progress"})
        if accepting_cubes:
            edges.append({"src": name[q], "dst": name[q0],
                          "condition": disjunction_str(accepting_cubes),
                          "accepting": True, "origin": "final_reset"})
            if not disjunction_valid(accepting_cubes):
                guard = disjunction_str(accepting_cubes)
                edges.append({"src": name[q], "dst": name[q0],
                              "condition": f"!({guard})",
                              "accepting": False, "origin": "reset"})
        else:
            edges.append({"src": name[q], "dst": name[q0], "condition": "true",
                          "accepting": False, "origin": "reset"})
    return {"states": [name[q] for q in reach], "initial": name[q0], "transitions": edges}


def construct(spec):
    phi = parse_gf_body(spec["formula"])
    start = time.perf_counter()
    nfa = best_nfa(phi)
    gfm = direct_gfm(nfa)
    elapsed = time.perf_counter() - start
    return {
        "name": spec["name"],
        "method": "gfm_gf",
        "formula": spec["formula"],
        "nfa_state_count": len(nfa[0]),
        "construction_time_sec": elapsed,
        "gfm": gfm,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("specs", nargs="?", default="data/gf_benchmarks.json")
    parser.add_argument("output", nargs="?", default="outputs/results.json")
    args = parser.parse_args(argv)
    specs = json.loads(Path(args.specs).read_text())["benchmarks"]
    rows = [construct(spec) for spec in specs]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"results": rows}, indent=1) + "\n")
    for row in rows:
        print(f"{row['name']}: {len(row['gfm']['states'])} states, "
              f"{len(row['gfm']['transitions'])} edges", file=sys.stderr)


if __name__ == "__main__":
    main()
