#!/usr/bin/env python3
"""Held-out test evaluator for automata constructed for GF(co-safety) LTL goals.

The benchmark instances below are generated here at test time and are never
shown to the method before it is run on them.

Method interface
----------------
A method is any command registered in ``outputs/<name>.method.json``::

    {"method": "<name>", "command": ["python", "path/to/constructor.py"]}

For every registered method the evaluator writes a benchmark-spec file and runs

    <command...> <specs.json> <output.json>

from the workspace root.  ``specs.json`` is ``{"benchmarks": [{"name", "formula",
"atoms"}, ...]}``; the method must write ``{"results": [{"name", "gfm": {"states",
"initial", "transitions": [{"src", "dst", "condition", "accepting"}]}}]}``.

Everything scored is recomputed here from the automata themselves: state and
transition counts, agreement with the LTL semantics on ultimately periodic words,
and agreement of the optimal satisfaction probability obtained through the
automaton product (agent resolves the automaton's nondeterminism) with the true
optimal satisfaction probability on evaluator-generated MDPs.  Benchmark
identity (formula, atoms, size) comes only from this file.  Any missing,
malformed, oversized, or incorrect output marks the method as failed, and a
failed method receives the worst value of every metric in every experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SLICE = "test"
ROOT = Path(__file__).resolve().parents[2]

PROBE_SEED = "test-lasso-probes-v2-8675309"
MDP_SEED = "test-planning-mdps-v2-8675309"
SALT_SEED = "test-salted-checks-v2-5150"
RANDOM_FORMULA_SEED = "test-random-cosafety-v2-9091"

BALANCED_PROBES = 32          # balanced positive/negative lasso words per formula
GENERATED_PROBES = 16         # unconstrained dense random lasso words per formula
SALTED_PROBES = 16            # extra probes seeded by a hash of the method output

RANDOM_FORMULAS = 16
RANDOM_MIN_DEPTH = 4
RANDOM_DEPTH_SPAN = 3
RANDOM_MIN_SIZE = 9
RANDOM_MAX_SIZE = 22
RANDOM_MAX_MONITOR = 300      # cap on the deterministic monitor used for ground truth

CAP_STATES = 2048             # per-formula validity cap and worst value
CAP_EDGES = 16384             # per-formula cap on declared edges; worst transition value
CAP_GUARD_CHARS = 4096
CONSTRUCTOR_TIMEOUT_SEC = 1800
VALUE_TOLERANCE = 1e-6

EXPERIMENTS = [
    "tdr_delayed_response",
    "lib_signal_change",
    "ncs_ordered_sequence",
    "random_cosafety_gf",
]

# NCS[k1..kn] = GF(a & X^{k1} b & X^{k1+k2} c ...), offsets reconstructed from the
# paper's Appendix N / Table 5 (GFM-GF sizes 4..11 = span + 1).
NCS_OFFSETS = [
    (0, 1, 3),
    (0, 1, 3, 4),
    (0, 1, 3, 5),
    (0, 1, 3, 6),
    (0, 1, 3, 5, 7),
    (0, 1, 3, 5, 8),
    (0, 1, 3, 5, 9),
    (0, 1, 3, 6, 10),
]


# --------------------------------------------------------------------------
# Deterministic RNG (independent of Python's hash seed and random module)
# --------------------------------------------------------------------------

class Rng:
    MASK = (1 << 64) - 1

    def __init__(self, *parts):
        digest = hashlib.sha256(repr(parts).encode()).digest()
        self.state = int.from_bytes(digest[:8], "little")

    def next64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & self.MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & self.MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & self.MASK
        return z ^ (z >> 31)

    def randrange(self, n: int) -> int:
        return self.next64() % n

    def random(self) -> float:
        return (self.next64() >> 11) / float(1 << 53)

    def choice(self, seq):
        return seq[self.randrange(len(seq))]


# --------------------------------------------------------------------------
# LTL (co-safety fragment under GF) — AST, parser, printer, progression
# --------------------------------------------------------------------------

TRUE = ("t",)
FALSE = ("f",)


def lit(name: str, positive: bool = True):
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
    if f in (TRUE, FALSE):
        return f
    return ("X", f)


def mk_f(f):
    if f in (TRUE, FALSE) or f[0] == "F":
        return f
    return ("F", f)


def mk_u(f, g):
    if g in (TRUE, FALSE):
        return g
    if f == FALSE or f == g:
        return g
    if f == TRUE:
        return mk_f(g)
    return ("U", f, g)


class LtlParser:
    TOKEN = re.compile(r"\s*(?:(?P<id>[a-z_][a-z0-9_]*)|(?P<op>[XFGU]|[()!&|]))")

    def __init__(self, text: str):
        self.tokens = []
        pos = 0
        text = text.strip()
        while pos < len(text):
            m = self.TOKEN.match(text, pos)
            if not m or m.end() == pos:
                raise ValueError(f"bad LTL token at {text[pos:pos + 20]!r}")
            self.tokens.append(m.group("id") or m.group("op"))
            pos = m.end()
            while pos < len(text) and text[pos].isspace():
                pos += 1
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self, tok=None):
        cur = self.peek()
        if cur is None or (tok is not None and cur != tok):
            raise ValueError(f"expected {tok!r}, got {cur!r}")
        self.i += 1
        return cur

    def parse(self):
        f = self.parse_or()
        if self.peek() is not None:
            raise ValueError(f"trailing LTL token {self.peek()!r}")
        return f

    def parse_or(self):
        items = [self.parse_and()]
        while self.peek() == "|":
            self.take("|")
            items.append(self.parse_and())
        return mk_or(items) if len(items) > 1 else items[0]

    def parse_and(self):
        items = [self.parse_until()]
        while self.peek() == "&":
            self.take("&")
            items.append(self.parse_until())
        return mk_and(items) if len(items) > 1 else items[0]

    def parse_until(self):
        left = self.parse_unary()
        if self.peek() == "U":
            self.take("U")
            return mk_u(left, self.parse_until())
        return left

    def parse_unary(self):
        tok = self.peek()
        if tok == "!":
            self.take("!")
            inner = self.parse_unary()
            if inner == TRUE:
                return FALSE
            if inner == FALSE:
                return TRUE
            if inner[0] != "lit":
                raise ValueError("negation is only allowed on atoms in co-safety formulas")
            return ("lit", inner[1], not inner[2])
        if tok == "X":
            self.take("X")
            return mk_x(self.parse_unary())
        if tok == "F":
            self.take("F")
            return mk_f(self.parse_unary())
        if tok == "G":
            self.take("G")
            return ("G", self.parse_unary())
        if tok == "(":
            self.take("(")
            f = self.parse_or()
            self.take(")")
            return f
        if tok is None:
            raise ValueError("unexpected end of LTL formula")
        self.take()
        if tok == "true":
            return TRUE
        if tok == "false":
            return FALSE
        if tok in ("X", "F", "G", "U", ")", "&", "|"):
            raise ValueError(f"unexpected token {tok!r}")
        return lit(tok)


def contains_g(f) -> bool:
    if f[0] == "G":
        return True
    if f[0] in ("and", "or"):
        return any(contains_g(g) for g in f[1])
    if f[0] in ("X", "F"):
        return contains_g(f[1])
    if f[0] == "U":
        return contains_g(f[1]) or contains_g(f[2])
    return False


def parse_gf(formula: str):
    """Parse 'GF(phi)' and return the co-safety body phi."""
    f = LtlParser(formula).parse()
    if f[0] != "G" or f[1][0] != "F":
        raise ValueError("benchmark formula must have the form GF(phi)")
    body = f[1][1]
    if contains_g(body):
        raise ValueError("phi must be co-safety (no G)")
    return body


def fmt(f) -> str:
    kind = f[0]
    if kind == "t":
        return "true"
    if kind == "f":
        return "false"
    if kind == "lit":
        return f[1] if f[2] else "!" + f[1]
    if kind in ("and", "or"):
        sep = " & " if kind == "and" else " | "
        parts = sorted(_paren(g) for g in f[1])
        return sep.join(parts)
    if kind == "X":
        return "X(" + fmt(f[1]) + ")"
    if kind == "F":
        return "F(" + fmt(f[1]) + ")"
    if kind == "U":
        return _paren(f[1]) + " U " + _paren(f[2])
    if kind == "G":
        return "G(" + fmt(f[1]) + ")"
    raise ValueError(kind)


def _paren(f) -> str:
    s = fmt(f)
    return "(" + s + ")" if f[0] in ("and", "or", "U") else s


def node_count(f) -> int:
    kind = f[0]
    if kind in ("t", "f", "lit"):
        return 1
    if kind in ("and", "or"):
        return 1 + sum(node_count(g) for g in f[1])
    if kind in ("X", "F", "G"):
        return 1 + node_count(f[1])
    return 1 + node_count(f[1]) + node_count(f[2])


def temporal_depth(f) -> int:
    kind = f[0]
    if kind in ("t", "f", "lit"):
        return 0
    if kind in ("and", "or"):
        return max(temporal_depth(g) for g in f[1])
    if kind in ("X", "F", "G"):
        return 1 + temporal_depth(f[1])
    return 1 + max(temporal_depth(f[1]), temporal_depth(f[2]))


# Progression on a canonical DNF representation: a residual obligation is a
# frozenset of clauses, a clause a frozenset of literal/X/F/U terms; subsumed
# clauses are absorbed, which keeps the set of reachable residuals finite.

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


class Progression:
    """Deterministic progression of GF(phi) obligations over letter bitmasks."""

    def __init__(self, phi, atoms):
        self.atoms = list(atoms)
        self.index = {a: i for i, a in enumerate(self.atoms)}
        self.dnf_memo: dict = {}
        self.term_memo: dict = {}
        self.prog_memo: dict = {}
        self.phi = self.dnf(phi)

    def dnf(self, f):
        hit = self.dnf_memo.get(f)
        if hit is not None:
            return hit
        kind = f[0]
        if kind == "t":
            res = DTRUE
        elif kind == "f":
            res = DFALSE
        elif kind in ("lit", "X", "F", "U"):
            res = frozenset([frozenset([f])])
        elif kind == "and":
            res = DTRUE
            for g in f[1]:
                res = d_and(res, self.dnf(g))
        elif kind == "or":
            res = d_or(*[self.dnf(g) for g in f[1]])
        else:
            raise ValueError(f"cannot progress {kind}")
        self.dnf_memo[f] = res
        return res

    def term(self, t, mask):
        key = (t, mask)
        hit = self.term_memo.get(key)
        if hit is not None:
            return hit
        kind = t[0]
        if kind == "lit":
            bit = self.index.get(t[1])
            holds = bit is not None and bool((mask >> bit) & 1)
            res = DTRUE if holds == t[2] else DFALSE
        elif kind == "X":
            res = self.dnf(t[1])
        elif kind == "F":
            res = d_or(self.prog(self.dnf(t[1]), mask), frozenset([frozenset([t])]))
        elif kind == "U":
            res = d_or(self.prog(self.dnf(t[2]), mask),
                       d_and(self.prog(self.dnf(t[1]), mask), frozenset([frozenset([t])])))
        else:
            raise ValueError(kind)
        self.term_memo[key] = res
        return res

    def prog(self, d, mask):
        key = (d, mask)
        hit = self.prog_memo.get(key)
        if hit is not None:
            return hit
        out = []
        for clause in d:
            acc = DTRUE
            for t in clause:
                acc = d_and(acc, self.term(t, mask))
                if not acc:
                    break
            out.extend(acc)
        res = _absorb(out)
        self.prog_memo[key] = res
        return res

    def step(self, pending, mask):
        """DBA for GF(phi): state = disjunction of pending attempts."""
        nxt = self.prog(d_or(pending, self.phi), mask)
        if frozenset() in nxt:
            return DFALSE, True
        return nxt, False


def dba_size(phi, atoms, limit: int) -> int:
    prog = Progression(phi, atoms)
    seen = {DFALSE}
    stack = [DFALSE]
    while stack:
        d = stack.pop()
        for mask in range(1 << len(atoms)):
            nxt, _ = prog.step(d, mask)
            if nxt not in seen:
                seen.add(nxt)
                if len(seen) > limit:
                    return len(seen)
                stack.append(nxt)
    return len(seen)


# --------------------------------------------------------------------------
# Semantics on ultimately periodic (lasso) words
# --------------------------------------------------------------------------

def lasso_truth(phi, word, loop_start):
    """Return truth of phi at every position of the lasso word."""
    n = len(word)
    nxt = [i + 1 if i + 1 < n else loop_start for i in range(n)]
    memo: dict = {}

    def ev(f):
        hit = memo.get(f)
        if hit is not None:
            return hit
        kind = f[0]
        if kind == "t":
            val = [True] * n
        elif kind == "f":
            val = [False] * n
        elif kind == "lit":
            val = [((f[1] in word[i]) == f[2]) for i in range(n)]
        elif kind == "and":
            parts = [ev(g) for g in f[1]]
            val = [all(p[i] for p in parts) for i in range(n)]
        elif kind == "or":
            parts = [ev(g) for g in f[1]]
            val = [any(p[i] for p in parts) for i in range(n)]
        elif kind == "X":
            inner = ev(f[1])
            val = [inner[nxt[i]] for i in range(n)]
        elif kind in ("F", "U"):
            goal = ev(f[1] if kind == "F" else f[2])
            stay = None if kind == "F" else ev(f[1])
            val = [False] * n
            changed = True
            while changed:
                changed = False
                for i in reversed(range(n)):
                    new = goal[i] or ((stay is None or stay[i]) and val[nxt[i]])
                    if new and not val[i]:
                        val[i] = True
                        changed = True
        else:
            raise ValueError(kind)
        memo[f] = val
        return val

    return ev(phi)


def oracle_gf(phi, word, loop_start) -> bool:
    truth = lasso_truth(phi, word, loop_start)
    return any(truth[i] for i in range(loop_start, len(word)))


# --------------------------------------------------------------------------
# Graph utilities
# --------------------------------------------------------------------------

def tarjan(nodes, succ):
    index: dict = {}
    low: dict = {}
    on_stack = set()
    stack = []
    comps = []
    counter = 0
    for root in nodes:
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(succ(root)))]
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on_stack.add(w)
                    work.append((w, iter(succ(w))))
                    advanced = True
                    break
                if w in on_stack and index[w] < low[v]:
                    low[v] = index[w]
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                if low[v] < low[parent]:
                    low[parent] = low[v]
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                comps.append(comp)
    return comps


# --------------------------------------------------------------------------
# Automaton loading and validation
# --------------------------------------------------------------------------

class RowError(Exception):
    pass


class GuardParser:
    TOKEN = re.compile(r"\s*(?:(?P<id>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>[()!&|]))")

    def __init__(self, text: str, atom_index: dict):
        self.atom_index = atom_index
        self.tokens = []
        pos = 0
        while pos < len(text):
            if text[pos].isspace():
                pos += 1
                continue
            m = self.TOKEN.match(text, pos)
            if not m or m.end() == pos:
                raise RowError(f"bad guard token at {text[pos:pos + 20]!r}")
            self.tokens.append(m.group("id") or m.group("op"))
            pos = m.end()
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self, tok=None):
        cur = self.peek()
        if cur is None or (tok is not None and cur != tok):
            raise RowError(f"guard: expected {tok!r}, got {cur!r}")
        self.i += 1
        return cur

    def compile(self):
        if not self.tokens:
            raise RowError("empty guard")
        fn = self.parse_or()
        if self.peek() is not None:
            raise RowError(f"guard: trailing token {self.peek()!r}")
        return fn

    def parse_or(self):
        items = [self.parse_and()]
        while self.peek() == "|":
            self.take("|")
            items.append(self.parse_and())
        if len(items) == 1:
            return items[0]
        return lambda m, items=tuple(items): any(f(m) for f in items)

    def parse_and(self):
        items = [self.parse_not()]
        while self.peek() == "&":
            self.take("&")
            items.append(self.parse_not())
        if len(items) == 1:
            return items[0]
        return lambda m, items=tuple(items): all(f(m) for f in items)

    def parse_not(self):
        if self.peek() == "!":
            self.take("!")
            inner = self.parse_not()
            return lambda m, inner=inner: not inner(m)
        return self.parse_atom()

    def parse_atom(self):
        tok = self.peek()
        if tok == "(":
            self.take("(")
            f = self.parse_or()
            self.take(")")
            return f
        if tok is None or tok in (")", "&", "|", "!"):
            raise RowError(f"guard: unexpected token {tok!r}")
        self.take()
        if tok == "true":
            return lambda m: True
        if tok == "false":
            return lambda m: False
        if tok not in self.atom_index:
            # atoms outside the benchmark's alphabet are never true
            return lambda m: False
        bit = 1 << self.atom_index[tok]
        return lambda m, bit=bit: bool(m & bit)


class Automaton:
    def __init__(self, gfm, atoms):
        if not isinstance(gfm, dict):
            raise RowError("missing 'gfm' object")
        states = gfm.get("states")
        transitions = gfm.get("transitions")
        initial = gfm.get("initial")
        if not isinstance(states, list) or not states:
            raise RowError("'states' must be a non-empty list")
        if not all(isinstance(s, str) for s in states):
            raise RowError("state names must be strings")
        if len(set(states)) != len(states):
            raise RowError("duplicate state names")
        if len(states) > CAP_STATES:
            raise RowError(f"{len(states)} states exceeds the cap {CAP_STATES}")
        if not isinstance(transitions, list):
            raise RowError("'transitions' must be a list")
        if len(transitions) > CAP_EDGES:
            raise RowError(f"{len(transitions)} edges exceeds the cap {CAP_EDGES}")
        if not isinstance(initial, str) or initial not in states:
            raise RowError("'initial' must name a declared state")
        self.atoms = list(atoms)
        self.n_letters = 1 << len(self.atoms)
        atom_index = {a: i for i, a in enumerate(self.atoms)}
        sid = {s: i for i, s in enumerate(states)}
        self.n = len(states)
        self.initial = sid[initial]
        self.out = [[] for _ in range(self.n)]
        triples = {}
        for edge in transitions:
            if not isinstance(edge, dict):
                raise RowError("transition must be an object")
            src, dst, cond, acc = edge.get("src"), edge.get("dst"), edge.get("condition"), edge.get("accepting")
            if src not in sid or dst not in sid:
                raise RowError("transition references an undeclared state")
            if not isinstance(acc, bool):
                raise RowError("'accepting' must be a JSON boolean")
            if not isinstance(cond, str) or len(cond) > CAP_GUARD_CHARS:
                raise RowError("guard must be a string of bounded length")
            fn = GuardParser(cond, atom_index).compile()
            self.out[sid[src]].append((sid[dst], fn, acc))
            key = (sid[src], sid[dst], acc)
            triples.setdefault(key, []).append(fn)
        self.state_count = self.n
        self.transition_count = sum(
            1 for fns in triples.values() if any(self._satisfiable(fn) for fn in fns)
        )
        self.cache: dict = {}

    def _satisfiable(self, fn) -> bool:
        for m in range(self.n_letters):
            if fn(m):
                return True
        return False

    def succ(self, q: int, mask: int):
        key = (q, mask)
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        res: dict = {}
        for dst, fn, acc in self.out[q]:
            if fn(mask):
                res[dst] = res.get(dst, False) or acc
        out = tuple(sorted(res.items()))
        self.cache[key] = out
        return out

    def accepts_lasso(self, masks, loop_start) -> bool:
        n = len(masks)
        nxt = [i + 1 if i + 1 < n else loop_start for i in range(n)]
        start = (self.initial, 0)
        seen = {start}
        order = [start]
        stack = [start]
        while stack:
            q, i = stack.pop()
            for dst, _ in self.succ(q, masks[i]):
                node = (dst, nxt[i])
                if node not in seen:
                    seen.add(node)
                    stack.append(node)
                    order.append(node)

        def succ_nodes(node):
            q, i = node
            return [(dst, nxt[i]) for dst, _ in self.succ(q, masks[i])]

        for comp in tarjan(order, succ_nodes):
            members = set(comp)
            for q, i in comp:
                for dst, acc in self.succ(q, masks[i]):
                    if acc and (dst, nxt[i]) in members:
                        return True
        return False


# --------------------------------------------------------------------------
# Probe generation
# --------------------------------------------------------------------------

DENSITIES = [0.1, 0.25, 0.5, 0.75, 0.9]


def random_lasso(rng, n_atoms, max_loop, density):
    prefix = rng.randrange(4)
    loop = 1 + rng.randrange(max_loop)
    word = []
    for _ in range(prefix + loop):
        mask = 0
        for b in range(n_atoms):
            if rng.random() < density:
                mask |= 1 << b
        word.append(mask)
    return word, prefix


def mask_to_set(mask, atoms):
    return frozenset(a for i, a in enumerate(atoms) if (mask >> i) & 1)


def lasso_label(phi, atoms, word, prefix):
    return oracle_gf(phi, [mask_to_set(m, atoms) for m in word], prefix)


def balanced_probes(rng, phi, atoms, count):
    max_loop = 2 * temporal_depth(phi) + 4
    want = {True: count // 2, False: count - count // 2}
    got = {True: [], False: []}
    seen = set()
    for attempt in range(60 * count):
        if not want[True] and not want[False]:
            break
        density = DENSITIES[attempt % len(DENSITIES)]
        word, prefix = random_lasso(rng, len(atoms), max_loop, density)
        label = lasso_label(phi, atoms, word, prefix)
        candidates = [(word, prefix, label)]
        if not want[label] and want[not label]:
            # near-miss search: flip single atoms until the label changes
            for _ in range(24):
                pos = rng.randrange(len(word))
                bit = rng.randrange(len(atoms))
                mutated = list(word)
                mutated[pos] ^= 1 << bit
                mlabel = lasso_label(phi, atoms, mutated, prefix)
                if mlabel != label:
                    candidates.append((mutated, prefix, mlabel))
                    break
        for w, p, lab in candidates:
            key = (tuple(w), p)
            if want[lab] and key not in seen:
                seen.add(key)
                got[lab].append((w, p, lab))
                want[lab] -= 1
    return got[True] + got[False]


def generated_probes(rng, phi, atoms, count):
    max_loop = 2 * temporal_depth(phi) + 4
    probes = []
    for k in range(count):
        density = DENSITIES[k % len(DENSITIES)]
        word, prefix = random_lasso(rng, len(atoms), max_loop, density)
        probes.append((word, prefix, lasso_label(phi, atoms, word, prefix)))
    return probes


# --------------------------------------------------------------------------
# Planning check: MDP x automaton products, MECs, max reachability
# --------------------------------------------------------------------------

def random_letter(rng, n_atoms, density):
    mask = 0
    for b in range(n_atoms):
        if rng.random() < density:
            mask |= 1 << b
    return mask


MDP_KINDS = ["iid", "mixture", "random", "random", "mixture", "random"]
SALTED_MDP_KINDS = ["iid", "mixture"]


def gen_mdp(rng, n_atoms, kind: str):
    """MDP as list over states of actions; action = (letter_mask, [(succ, prob)]).

    iid:     a recurrent chain emitting random letters i.i.d. (tests that accepting
             behaviour is reached almost surely without knowing future letters)
    mixture: transient choice states that branch probabilistically into a
             recurrent i.i.d. block or an absorbing trap (fractional optimal values)
    random:  random states, actions, labels and successor distributions
    """
    density = rng.choice([0.2, 0.35, 0.5, 0.65, 0.8])
    if kind == "iid":
        m = 2 + rng.randrange(4)
        return [[(random_letter(rng, n_atoms, density), [(t, 1.0 / m) for t in range(m)])] for _ in range(m)]
    if kind == "mixture":
        k = 2 + rng.randrange(2)
        states = [[(random_letter(rng, n_atoms, density), [(t, 1.0 / k) for t in range(k)])] for _ in range(k)]
        trap = k
        states.append([(random_letter(rng, n_atoms, density), [(trap, 1.0)])])
        for _ in range(1 + rng.randrange(2)):
            actions = []
            for _ in range(2):
                w_good, w_bad = 1 + rng.randrange(4), 1 + rng.randrange(4)
                total = float(w_good + w_bad)
                actions.append((random_letter(rng, n_atoms, density),
                                [(rng.randrange(k), w_good / total), (trap, w_bad / total)]))
            states.append(actions)
        return states
    m = 2 + rng.randrange(4)
    states = []
    for s in range(m):
        if rng.random() < 0.2:
            states.append([(random_letter(rng, n_atoms, density), [(s, 1.0)])])
            continue
        actions = []
        for _ in range(1 + rng.randrange(2)):
            label = random_letter(rng, n_atoms, density)
            k = 1 + rng.randrange(min(3, m))
            pool = list(range(m))
            succs = []
            for _ in range(k):
                succs.append(pool.pop(rng.randrange(len(pool))))
            weights = [1 + rng.randrange(3) for _ in succs]
            total = float(sum(weights))
            actions.append((label, [(t, w / total) for t, w in zip(sorted(succs), weights)]))
        states.append(actions)
    return states


class ProductLimit(Exception):
    pass


def explore(roots, expand, limit=400000):
    ids: dict = {}
    keys = []
    acts = []
    stack = []
    for r in roots:
        if r not in ids:
            ids[r] = len(keys)
            keys.append(r)
            acts.append(None)
            stack.append(r)
    while stack:
        key = stack.pop()
        expanded = []
        for acc, succ in expand(key):
            sids = []
            probs = []
            for t, p in succ:
                if t not in ids:
                    ids[t] = len(keys)
                    keys.append(t)
                    acts.append(None)
                    stack.append(t)
                    if len(keys) > limit:
                        raise ProductLimit("product too large")
                sids.append(ids[t])
                probs.append(p)
            expanded.append((acc, tuple(sids), tuple(probs)))
        acts[ids[key]] = expanded
    return ids, acts


def maximal_end_components(n, acts):
    result = []
    work = [list(range(n))]
    while work:
        comp = set(work.pop())
        alive = {}
        rev: dict = {}
        queue = []
        for v in comp:
            ok = [ai for ai, (_, succ, _) in enumerate(acts[v]) if all(t in comp for t in succ)]
            alive[v] = set(ok)
            for ai in ok:
                for t in acts[v][ai][1]:
                    rev.setdefault(t, []).append((v, ai))
            if not ok:
                queue.append(v)
        removed = set()
        while queue:
            v = queue.pop()
            if v in removed:
                continue
            removed.add(v)
            for u, ai in rev.get(v, ()):
                if u not in removed and ai in alive[u]:
                    alive[u].discard(ai)
                    if not alive[u]:
                        queue.append(u)
        comp -= removed
        if not comp:
            continue
        ordered = sorted(comp)

        def succ(v):
            return [t for ai in alive[v] for t in acts[v][ai][1]]

        sccs = tarjan(ordered, succ)
        if len(sccs) == 1:
            result.append((comp, {v: alive[v] for v in comp}))
        else:
            work.extend(sccs)
    return result


def buchi_max_values(n, acts):
    target = set()
    for comp, alive in maximal_end_components(n, acts):
        if any(acts[v][ai][0] for v in comp for ai in alive[v]):
            target |= comp
    preds = [[] for _ in range(n)]
    for v in range(n):
        for _, succ, _ in acts[v]:
            for t in succ:
                preds[t].append(v)
    can = set(target)
    stack = list(target)
    while stack:
        t = stack.pop()
        for v in preds[t]:
            if v not in can:
                can.add(v)
                stack.append(v)
    universe = set(can)
    while True:
        reach = set(target)
        stack = list(target)
        while stack:
            t = stack.pop()
            for v in preds[t]:
                if v in universe and v not in reach:
                    for _, succ, _ in acts[v]:
                        if all(s in universe for s in succ) and any(s in reach for s in succ):
                            reach.add(v)
                            stack.append(v)
                            break
        if reach == universe:
            break
        universe = reach
    x = [0.0] * n
    for v in universe:
        x[v] = 1.0
    rest = sorted(can - universe)
    for _ in range(20000):
        delta = 0.0
        for v in rest:
            best = 0.0
            for _, succ, probs in acts[v]:
                val = 0.0
                for t, p in zip(succ, probs):
                    val += p * x[t]
                if val > best:
                    best = val
            if best - x[v] > delta:
                delta = best - x[v]
            x[v] = best
        if delta < 1e-15:
            break
    return x


def semantic_values(prog: Progression, mdp):
    """Optimal probability of GF(phi) from every MDP state (deterministic monitor)."""

    def expand(node):
        s, pending = node
        out = []
        for mask, succ in mdp[s]:
            nxt, acc = prog.step(pending, mask)
            out.append((acc, [((t, nxt), p) for t, p in succ]))
        return out

    roots = [(s, DFALSE) for s in range(len(mdp))]
    ids, acts = explore(roots, expand)
    x = buchi_max_values(len(acts), acts)
    return [x[ids[r]] for r in roots]


def syntactic_values(aut: Automaton, mdp):
    """Optimal probability of reaching an accepting MEC of the MDP x automaton product
    when the agent resolves the automaton's nondeterminism (it sees the current letter)."""
    sink = ("sink",)

    def expand(node):
        if node == sink:
            return [(False, [(sink, 1.0)])]
        s, q = node
        out = []
        for mask, succ in mdp[s]:
            options = aut.succ(q, mask)
            if not options:
                out.append((False, [(sink, 1.0)]))
                continue
            for dst, acc in options:
                out.append((acc, [((t, dst), p) for t, p in succ]))
        return out

    roots = [(s, aut.initial) for s in range(len(mdp))]
    ids, acts = explore(roots, expand)
    x = buchi_max_values(len(acts), acts)
    return [x[ids[r]] for r in roots]


# --------------------------------------------------------------------------
# Benchmark suites
# --------------------------------------------------------------------------

def tdr_formula(n, a="a", b="b"):
    inner = b
    for _ in range(n):
        inner = f"X({inner})"
    return f"GF({a} & {inner})"


def lib_formula(n, prefix="a"):
    terms = []
    for i in range(1, n + 1):
        x = f"{prefix}{i}"
        terms.append(f"({x} & X(!{x}))")
        terms.append(f"(!{x} & X({x}))")
    return "GF(" + " | ".join(terms) + ")"


def ncs_formula(offsets, atoms):
    terms = []
    for atom, off in zip(atoms, offsets):
        inner = atom
        for _ in range(off):
            inner = f"X({inner})"
        terms.append(inner)
    return "GF(" + " & ".join(terms) + ")"


def gen_random_body(rng, atoms, depth):
    if depth <= 0 or (depth <= 2 and rng.random() < 0.3):
        return lit(rng.choice(atoms), rng.random() < 0.75)
    r = rng.random()
    if r < 0.28:
        return mk_and([gen_random_body(rng, atoms, depth - 1), gen_random_body(rng, atoms, depth - 1)])
    if r < 0.42:
        return mk_or([gen_random_body(rng, atoms, depth - 1), gen_random_body(rng, atoms, depth - 1)])
    if r < 0.70:
        return mk_x(gen_random_body(rng, atoms, depth - 1))
    if r < 0.86:
        return mk_f(gen_random_body(rng, atoms, depth - 1))
    return mk_u(gen_random_body(rng, atoms, depth - 1), gen_random_body(rng, atoms, depth - 1))


def random_cosafety_specs(seed, prefix, count, atoms=("p", "q", "r")):
    rng = Rng(seed)
    atoms = list(atoms)
    specs = []
    seen = set()
    tries = 0
    while len(specs) < count and tries < 20000:
        tries += 1
        phi = gen_random_body(rng, atoms, RANDOM_MIN_DEPTH + rng.randrange(RANDOM_DEPTH_SPAN))
        if phi in (TRUE, FALSE):
            continue
        size = node_count(phi)
        if size < RANDOM_MIN_SIZE or size > RANDOM_MAX_SIZE or temporal_depth(phi) < 2:
            continue
        text = fmt(phi)
        if text in seen:
            continue
        if dba_size(phi, atoms, RANDOM_MAX_MONITOR) > RANDOM_MAX_MONITOR:
            continue
        check = Rng(seed, "triviality", text)
        labels = set()
        for k in range(120):
            word, pre = random_lasso(check, len(atoms), 2 * temporal_depth(phi) + 4, DENSITIES[k % 5])
            labels.add(lasso_label(phi, atoms, word, pre))
            if len(labels) == 2:
                break
        if len(labels) < 2:
            continue
        seen.add(text)
        specs.append({
            "name": f"{prefix}_{len(specs):02d}",
            "experiment": "random_cosafety_gf",
            "formula": f"GF({text})",
            "atoms": atoms,
            "size": size,
        })
    return specs


def suite_specs(suite: str = "test"):
    """Hidden test instances: unseen parameters and renamed atoms for the paper's
    families, and fresh random GF(co-safety) formulas."""
    specs = []

    def add(name, exp, formula, atoms, size):
        specs.append({"name": name, "experiment": exp, "formula": formula, "atoms": list(atoms), "size": size})

    for n in [7, 9, 11]:
        add(f"tdr_{n}", "tdr_delayed_response", tdr_formula(n, "trig", "resp"), ["trig", "resp"], n)
    for n in [7, 9, 10]:
        add(f"lib_{n}", "lib_signal_change", lib_formula(n, "s"), [f"s{i}" for i in range(1, n + 1)], n)
    for row in [1, 3, 5, 7]:
        offsets = NCS_OFFSETS[row]
        atoms = ["v", "w", "x", "y", "z"][: len(offsets)]
        add(f"ncs_{row + 1}", "ncs_ordered_sequence", ncs_formula(offsets, atoms), atoms, offsets[-1])
    specs.extend(random_cosafety_specs(RANDOM_FORMULA_SEED, "rnd", RANDOM_FORMULAS))
    return specs


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

def canonical_hash(gfm) -> str:
    return hashlib.sha256(json.dumps(gfm, sort_keys=True, default=str).encode()).hexdigest()


class Checks:
    """Evaluator-owned probes for one benchmark (shared by every method)."""

    def __init__(self, spec):
        self.spec = spec
        self.phi = parse_gf(spec["formula"])
        self.atoms = spec["atoms"]
        rng = Rng(PROBE_SEED, spec["name"])
        self.balanced = balanced_probes(rng, self.phi, self.atoms, BALANCED_PROBES)
        self.generated = generated_probes(Rng(PROBE_SEED, "generated", spec["name"]), self.phi, self.atoms, GENERATED_PROBES)
        self.prog = Progression(self.phi, self.atoms)
        mrng = Rng(MDP_SEED, spec["name"])
        self.mdps = [gen_mdp(mrng, len(self.atoms), kind) for kind in MDP_KINDS]
        self.mdp_values = [semantic_values(self.prog, mdp) for mdp in self.mdps]


def check_row(checks: Checks, row) -> dict:
    spec = checks.spec
    aut = Automaton(row.get("gfm") if isinstance(row, dict) else None, checks.atoms)
    result = {"states": aut.state_count, "transitions": aut.transition_count}

    def agree(probes):
        ok = 0
        for word, prefix, label in probes:
            ok += int(aut.accepts_lasso(word, prefix) == label)
        return ok, len(probes)

    result["balanced"] = agree(checks.balanced)
    result["generated"] = agree(checks.generated)
    ok = total = 0
    for mdp, expected in zip(checks.mdps, checks.mdp_values):
        got = syntactic_values(aut, mdp)
        for a, b in zip(got, expected):
            ok += int(abs(a - b) <= VALUE_TOLERANCE)
            total += 1
    result["planning"] = (ok, total)

    salt = canonical_hash(row.get("gfm"))
    srng = Rng(SALT_SEED, spec["name"], salt)
    salted_probes = generated_probes(srng, checks.phi, checks.atoms, SALTED_PROBES)
    salted_ok, salted_total = agree(salted_probes)
    for kind in SALTED_MDP_KINDS:
        mdp = gen_mdp(srng, len(checks.atoms), kind)
        expected = semantic_values(checks.prog, mdp)
        got = syntactic_values(aut, mdp)
        for a, b in zip(got, expected):
            salted_ok += int(abs(a - b) <= VALUE_TOLERANCE)
            salted_total += 1
    result["salted"] = (salted_ok, salted_total)
    result["correct"] = all(r[0] == r[1] for r in (result["balanced"], result["generated"], result["planning"], result["salted"]))
    return result


def worst_metrics(specs):
    sizes = [s["size"] for s in specs]
    return {
        "state_count_size_weighted_mean": float(CAP_STATES),
        "state_count_per_formula": float(CAP_STATES),
        "state_count_sum": CAP_STATES * len(specs),
        "transition_count_sum": CAP_EDGES * len(specs),
        "semantic_check_pass_rate": 0.0,
        "generated_trace_pass_rate": 0.0,
        "planning_value_agreement_rate": 0.0,
    } if sizes else {}


def aggregate(specs, per_row):
    states = [per_row[s["name"]]["states"] for s in specs]
    sizes = [s["size"] for s in specs]

    def rate(key):
        ok = sum(per_row[s["name"]][key][0] for s in specs)
        total = sum(per_row[s["name"]][key][1] for s in specs)
        return ok / total if total else 0.0

    return {
        "state_count_size_weighted_mean": sum(a * b for a, b in zip(states, sizes)) / sum(sizes),
        "state_count_per_formula": sum(states) / len(states),
        "state_count_sum": sum(states),
        "transition_count_sum": sum(per_row[s["name"]]["transitions"] for s in specs),
        "semantic_check_pass_rate": rate("balanced"),
        "generated_trace_pass_rate": rate("generated"),
        "planning_value_agreement_rate": rate("planning"),
    }


def discover_methods(outputs: Path):
    """Every outputs/*.method.json manifest is a method; a malformed one is a failed method."""
    methods = {}
    problems = {}
    for path in sorted(outputs.glob("*.method.json")):
        stem = path.name[: -len(".method.json")]
        try:
            manifest = json.loads(path.read_text())
            name = manifest.get("method", stem)
            command = manifest.get("command")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.\-]+", name):
                raise ValueError("invalid method name")
            if not isinstance(command, list) or not command or not all(isinstance(c, str) for c in command):
                raise ValueError("'command' must be a non-empty list of strings")
        except Exception as exc:
            name, command = stem, None
            problems[name] = f"malformed manifest {path.name}: {exc}"
        if name in methods or (command is not None and name in problems):
            print(f"warning: duplicate method name {name!r} in {path.name}; ignored", file=sys.stderr)
            continue
        if command is not None:
            methods[name] = command
    return methods, problems


def run_constructor(command, public_specs, workdir: Path):
    spec_path = workdir / "specs.json"
    out_path = workdir / "constructed.json"
    spec_path.write_text(json.dumps({"benchmarks": public_specs}, indent=2) + "\n")
    proc = subprocess.run(
        command + [str(spec_path), str(out_path)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=CONSTRUCTOR_TIMEOUT_SEC,
    )
    if proc.returncode != 0:
        tail = proc.stdout.decode(errors="replace")[-600:]
        raise RuntimeError(f"constructor exited with {proc.returncode}: {tail}")
    if not out_path.is_file():
        raise RuntimeError("constructor wrote no output file")
    if out_path.stat().st_size > 200_000_000:
        raise RuntimeError("constructor output too large")
    payload = json.loads(out_path.read_text())
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("output must be an object with a 'results' list")
    by_name = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("name"), str):
            if row["name"] in by_name:
                raise RuntimeError(f"duplicate output for {row['name']}")
            by_name[row["name"]] = row
    return by_name


def score_method(name, command, specs, checks):
    diag = {"failed": False, "errors": [], "rows": {}}
    per_row = {}
    if command is None:
        diag["failed"] = True
    else:
        public = [{"name": s["name"], "formula": s["formula"], "atoms": s["atoms"]} for s in specs]
        try:
            with tempfile.TemporaryDirectory(prefix=f"gf_{SLICE}_") as tmp:
                rows = run_constructor(command, public, Path(tmp))
        except Exception as exc:
            diag["failed"] = True
            diag["errors"].append(f"constructor: {exc}")
            rows = {}
        for spec in specs:
            row = rows.get(spec["name"])
            if row is None:
                diag["failed"] = True
                if rows:
                    diag["errors"].append(f"{spec['name']}: missing output")
                continue
            try:
                res = check_row(checks[spec["name"]], row)
            except Exception as exc:  # malformed or unscorable output fails the method
                diag["failed"] = True
                diag["errors"].append(f"{spec['name']}: {type(exc).__name__}: {exc}")
                continue
            per_row[spec["name"]] = res
            diag["rows"][spec["name"]] = {k: v for k, v in res.items()}
            if not res["correct"]:
                diag["failed"] = True
                diag["errors"].append(f"{spec['name']}: semantic or planning disagreement")
    experiments = {}
    for exp in EXPERIMENTS:
        exp_specs = [s for s in specs if s["experiment"] == exp]
        if not exp_specs:
            continue
        experiments[exp] = worst_metrics(exp_specs) if diag["failed"] else aggregate(exp_specs, per_row)
    return experiments, diag


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs", default=str(ROOT / "outputs"), help="directory holding *.method.json manifests")
    parser.add_argument("--output", default=str(ROOT / "scoring" / "scores_test.json"))
    parser.add_argument("--diagnostics", default=None)
    parser.add_argument("--suite", default="test", choices=["test"])
    args = parser.parse_args()
    sys.setrecursionlimit(10000)

    specs = suite_specs(args.suite)

    methods, problems = discover_methods(Path(args.outputs))
    all_names = sorted(set(methods) | set(problems))
    scores = {"experiments": {exp: {"results": {}} for exp in EXPERIMENTS}}
    diagnostics = {"slice": args.suite, "methods": {}}
    if not all_names:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(scores, indent=2) + "\n")
        print("no registered methods (outputs/*.method.json) found", file=sys.stderr)
        return 2
    checks = {s["name"]: Checks(s) for s in specs}
    for name in all_names:
        experiments, diag = score_method(name, methods.get(name), specs, checks)
        if name in problems:
            diag["errors"].insert(0, problems[name])
            diag["failed"] = True
        for exp, metrics in experiments.items():
            scores["experiments"][exp]["results"][name] = metrics
        diagnostics["methods"][name] = diag
        status = "FAILED" if diag["failed"] else "ok"
        print(f"[{args.suite}] {name}: {status}" + (f" ({diag['errors'][0]})" if diag["errors"] else ""))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2) + "\n")
    diag_path = Path(args.diagnostics) if args.diagnostics else out.with_name(out.stem + "_diagnostics.json")
    diag_path.write_text(json.dumps(diagnostics, indent=2, default=list) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
