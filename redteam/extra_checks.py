#!/usr/bin/env python3
"""Scientific cross-checks; candidate creation never reads hidden code or scores."""
import importlib.util
import json
from pathlib import Path
import random

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'
spec = importlib.util.spec_from_file_location('visible_train_eval', ROOT / 'eval/train/evaluate_gf.py')
visible = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visible)


def rows(case):
    return json.loads((AUDIT / case / 'artifacts/results.json').read_text())['results']


def strongly_connected(graph, nodes):
    # Iterative Kosaraju, used only for a small independently constructed MDP.
    seen, order = set(), []
    for start in nodes:
        if start in seen:
            continue
        stack = [(start, False)]
        while stack:
            node, done = stack.pop()
            if done:
                order.append(node)
            elif node not in seen:
                seen.add(node)
                stack.append((node, True))
                stack.extend((dst, False) for dst in graph[node] if dst in nodes and dst not in seen)
    reverse = {node: [] for node in nodes}
    for node in nodes:
        for dst in graph[node]:
            if dst in nodes:
                reverse[dst].append(node)
    assigned, components = set(), []
    for start in reversed(order):
        if start in assigned:
            continue
        component, stack = set(), [start]
        while stack:
            node = stack.pop()
            if node in assigned:
                continue
            assigned.add(node)
            component.add(node)
            stack.extend(reverse[node])
        components.append(component)
    return components


def accepting_mecs(row):
    # MDP: iid uniform letters {}, {a}, {b}, {a,b}. Choices see the current
    # letter, but cannot see the next random letter. Missing actions go to sink.
    letters = [set(), {'a'}, {'b'}, {'a', 'b'}]
    states = row['gfm']['states']
    nodes = {(q, v) for q in states for v in range(4)} | {('sink', 0)}
    actions = {}
    for q, v in nodes:
        if q == 'sink':
            actions[q, v] = [(frozenset({('sink', 0)}), False)]
            continue
        opts = []
        for e in row['gfm']['transitions']:
            if e['src'] == q and visible.condition_holds(e['condition'], letters[v]):
                opts.append((frozenset((e['dst'], vp) for vp in range(4)), bool(e['accepting'])))
        actions[q, v] = opts or [(frozenset({('sink', 0)}), False)]
    pending = [nodes]
    mecs = []
    while pending:
        component = set(pending.pop())
        while component:
            bad = {node for node in component if not any(succ <= component for succ, _ in actions[node])}
            if not bad:
                break
            component -= bad
        if not component:
            continue
        graph = {node: set().union(*(set(succ) for succ, _ in actions[node] if succ <= component))
                 for node in component}
        parts = strongly_connected(graph, component)
        if len(parts) == 1:
            mecs.append(component)
        else:
            pending.extend(parts)
    accepting = [c for c in mecs if any(acc and succ <= c for node in c for succ, acc in actions[node])]
    return {'maximal_end_component_count': len(mecs), 'accepting_end_component_count': len(accepting),
            'accepting_component_sizes': sorted(map(len, accepting)),
            'optimal_buchi_probability': 0.0 if not accepting else 1.0}


def main():
    ref = rows('reference_seed11')
    better = {r['name']: r for r in rows('better_lib_falling')}
    rng = random.Random(20261112)
    checks = []
    for row in ref:
        if row['family'] != 'LIB':
            continue
        total, ref_agree, better_agree = 0, 0, 0
        atoms = [f'a{i}' for i in range(1, row['n'] + 1)]
        periods = [[set()], [set(atoms)]]
        for length in [1, 2, 3, 4, 7, 13]:
            for _ in range(16):
                periods.append([{a for a in atoms if rng.randrange(2)} for _ in range(length)])
        for period in periods:
            expected = visible.oracle_accepts('LIB', row['n'], period)
            total += 1
            ref_agree += visible.accepts_periodic_word(row, period) == expected
            better_agree += visible.accepts_periodic_word(better[row['name']], period) == expected
        checks.append({'name': row['name'], 'count': total, 'reference_correct': ref_agree,
                       'better_correct': better_agree})
    sparse = {r['name']: r for r in rows('shortcut_sparse_guards')}
    sparse_counterexamples = []
    for row in ref:
        if row['family'] == 'LIB':
            continue
        atoms = ['a', 'b'] if row['family'] == 'TDR' else [chr(97 + i) for i in range(row['n'])]
        period = [set(atoms)]
        sparse_counterexamples.append({'name': row['name'], 'period': [atoms],
            'true_answer': visible.oracle_accepts(row['family'], row['n'], period),
            'reference_answer': visible.accepts_periodic_word(row, period),
            'shortcut_answer': visible.accepts_periodic_word(sparse[row['name']], period)})
    row = next(r for r in ref if r['name'] == 'tdr_7')
    bad = next(r for r in rows('shortcut_non_gfm') if r['name'] == 'tdr_7')
    result = {'better_lib_dense_random_checks': checks,
              'shortcut_sparse_guard_counterexamples': sparse_counterexamples,
              'iid_mdp_tdr_7': {'letters': [[], ['a'], ['b'], ['a', 'b']],
                'probability_per_letter': 0.25, 'specification_satisfaction_probability': 1.0,
                'reference': accepting_mecs(row), 'shortcut_non_gfm': accepting_mecs(bad)}}
    (AUDIT / 'extra_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['iid_mdp_tdr_7'], indent=2))


if __name__ == '__main__':
    main()
