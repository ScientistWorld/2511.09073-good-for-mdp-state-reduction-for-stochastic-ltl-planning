#!/usr/bin/env python3
"""Real candidate variants and shortcuts, installed via the public artifact API."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')


def load(path):
    return json.loads(path.read_text())


def run(cmd, log, timeout=900, env=None):
    start = time.monotonic()
    try:
        with log.open('w') as out:
            result = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT,
                                    timeout=timeout, env=env)
        return {'returncode': result.returncode, 'seconds': time.monotonic() - start}
    except subprocess.TimeoutExpired:
        return {'returncode': 124, 'seconds': time.monotonic() - start, 'timeout': True}


def fresh_reference(seed, folder):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    result = run(['python', 'method/direct_gfm.py', '--output', 'outputs/results.json'],
                 folder / 'construction.log', env=env)
    if result['returncode']:
        raise RuntimeError(result)
    return load(ROOT / 'outputs/results.json')


def reference(folder):
    cached = AUDIT / 'reference_seed11' / 'artifacts' / 'results.json'
    if cached.exists():
        return load(cached)
    return fresh_reference(11, folder)


def recount(row):
    row['state_count'] = len(row['gfm']['states'])
    row['transition_count'] = len(row['gfm']['transitions'])
    row['accepting_transition_count'] = sum(bool(e.get('accepting')) for e in row['gfm']['transitions'])


def constant(row, accepts):
    row['gfm'] = {'states': ['q'], 'initial': 'q', 'transitions': [
        {'src': 'q', 'dst': 'q', 'condition': 'true', 'accepting': accepts}]}
    recount(row)


def deterministic_tdr(row):
    # Exhaustively enumerate all 2^n pending trigger histories, not a learned proxy.
    n = int(row['n'])
    size = 1 << n
    edges = []
    for mask in range(size):
        oldest = bool(mask & (1 << (n - 1)))
        for a in [False, True]:
            dst = ((mask << 1) | int(a)) & (size - 1)
            guard = 'a' if a else '!a'
            for b in ([False, True] if oldest else [None]):
                condition = guard if b is None else f'{guard} & ' + ('b' if b else '!b')
                edges.append({'src': str(mask), 'dst': str(dst), 'condition': condition,
                              'accepting': bool(oldest and b)})
    row['gfm'] = {'states': [str(m) for m in range(size)], 'initial': '0', 'transitions': edges}
    recount(row)


def build(case, folder):
    if case.startswith('reference_seed'):
        return fresh_reference(int(case.removeprefix('reference_seed')), folder)
    payload = reference(folder)
    rows = payload['results']
    if case == 'better_lib_falling':
        # GF(any signal changes) == GF(any signal has a falling edge), for finite n.
        # Apply the same direct GFM construction to the smaller equivalent NFA.
        for row in rows:
            if row['family'] != 'LIB':
                continue
            gfm = row['gfm']
            kept = {s for s in gfm['states'] if not s.endswith('_was_false')}
            gfm['states'] = [s for s in gfm['states'] if s in kept]
            gfm['transitions'] = [e for e in gfm['transitions'] if e['src'] in kept and e['dst'] in kept]
            recount(row)
    elif case == 'weaker_no_acceptance':
        for row in rows:
            for e in row['gfm']['transitions']:
                e['accepting'] = False
            recount(row)
    elif case == 'brute_force_history':
        for row in rows:
            if row['family'] == 'TDR':
                deterministic_tdr(row)
    elif case == 'shortcut_reported_counts':
        for row in rows:
            # Shortcut: a correct unchanged automaton with impossible reported sizes.
            row['state_count'] = -1000000
            row['transition_count'] = -1000000
            row['construction_time_sec'] = -1000000
    elif case == 'shortcut_ground_truth_options':
        specs = load(ROOT / 'data/gf_benchmarks.json')['benchmarks']
        rows = []
        for spec in specs:
            # Shortcut: keep required names, replace the problem by GF(a).
            row = {'name': spec['name'], 'method': 'gfm_gf', 'family': 'NCS', 'n': 1,
                   'formula': 'GF(a)', 'gfm': {'states': ['q'], 'initial': 'q', 'transitions': [
                       {'src': 'q', 'dst': 'q', 'condition': 'a', 'accepting': True},
                       {'src': 'q', 'dst': 'q', 'condition': '!a', 'accepting': False}]}}
            recount(row)
            rows.append(row)
        payload['results'] = rows
    elif case == 'shortcut_non_gfm':
        for row in rows:
            # Shortcut: keep the omega-language, discard the online/GFM guarantee.
            row['gfm']['transitions'] = [e for e in row['gfm']['transitions']
                if not (e.get('origin') == 'reset' and e['src'] != row['gfm']['initial'])]
            recount(row)
    elif case == 'shortcut_sparse_guards':
        for row in rows:
            # Shortcut: all public TDR/NCS probe templates have <=1 true atom.
            # Reject dense valuations, even when they satisfy the true formula.
            if row['family'] == 'LIB':
                continue
            atoms = ['a', 'b'] if row['family'] == 'TDR' else [chr(97 + i) for i in range(row['n'])]
            clauses = [f'!({a} & {b})' for i, a in enumerate(atoms) for b in atoms[i + 1:]]
            sparse = ' & '.join(clauses)
            for edge in row['gfm']['transitions']:
                edge['condition'] = f'({edge["condition"]}) & ({sparse})'
            recount(row)
    elif case in ['shortcut_prune_registry', 'shortcut_missing_benchmark',
                  'shortcut_null_count', 'shortcut_direct_scores', 'shortcut_flags',
                  'shortcut_empty_output', 'shortcut_constant_accept', 'shortcut_constant_reject']:
        if case == 'shortcut_prune_registry':
            for row in rows:
                if row['family'] != 'TDR':
                    constant(row, False)
        elif case == 'shortcut_missing_benchmark':
            payload['results'] = [r for r in rows if r['name'] != 'tdr_7']
        elif case == 'shortcut_null_count':
            for row in rows:
                row['state_count'] = None
        elif case in ['shortcut_flags', 'shortcut_constant_accept', 'shortcut_constant_reject']:
            for row in rows:
                constant(row, case == 'shortcut_constant_accept')
                if case == 'shortcut_flags':
                    row.update(semantic_check_pass_rate=1.0, trace_semantics_pass_rate=1.0,
                               generated_trace_pass_rate=1.0, success=True,
                               accepting_transition_count=1000000)
        elif case == 'shortcut_empty_output':
            payload['results'] = []
    else:
        raise ValueError(case)
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case')
    args = parser.parse_args()
    case = args.case
    folder = AUDIT / case
    folder.mkdir(parents=True, exist_ok=True)
    runtime = AUDIT / '.runtime' / case
    runtime.mkdir(parents=True, exist_ok=True)
    score_paths = [ROOT / 'scoring' / name for name in ['scores_train.json', 'scores_test.json']]
    originals = {p: p.read_bytes() if p.exists() else None for p in score_paths}
    output = ROOT / 'outputs'
    backup = runtime / 'original_outputs'
    if backup.exists():
        raise RuntimeError(f'unrestored previous run: {backup}')
    had_outputs = output.exists()
    if had_outputs:
        output.rename(backup)
    output.mkdir()
    outcome = {'case': case, 'hidden_command': ['bash', 'scripts/evaluate_test.sh'],
               'modified_evaluator': False}
    try:
        payload = build(case, folder)
        save(output / 'results.json', payload)
        (folder / 'artifacts').mkdir(exist_ok=True)
        shutil.copy2(output / 'results.json', folder / 'artifacts' / 'results.json')
        outcome['construction'] = {'formulas': len(payload['results']),
            'actual_states': sum(len(r['gfm']['states']) for r in payload['results']),
            'actual_transitions': sum(len(r['gfm']['transitions']) for r in payload['results'])}
        outcome['train'] = run(['bash', 'scripts/evaluate_train.sh'], folder / 'train.log')
        shutil.copy2(score_paths[0], folder / 'scores_train.json')
        if case == 'shortcut_prune_registry':
            train = load(score_paths[0])
            for name, exp in train['experiments'].items():
                if name != 'tdr_delayed_response':
                    exp['results'] = {}
            # Shortcut: scores_train.json is mutable and used as the test method registry.
            save(score_paths[0], train)
            save(folder / 'scores_train_registry_shortcut.json', train)
            extra = copy.deepcopy(payload)
            for row in extra['results']:
                row['method'] = 'shortcut_unregistered_method'
                constant(row, False)
            save(output / 'shortcut_unregistered_method.json', extra)
        if case == 'shortcut_direct_scores':
            # Shortcut attempt: forge the default final score artifact, then let
            # the genuine hidden test run. It should overwrite this file.
            fake = {'experiments': {name: {'results': {'gfm_gf': {
                'state_count_sum': -1000000, 'semantic_check_pass_rate': 1.0}}}
                for name in ['tdr_delayed_response', 'lib_signal_change', 'ncs_ordered_sequence']}}
            save(score_paths[1], fake)
            save(folder / 'forged_scores_shortcut.json', fake)
        # A separate process with no monkeypatches or surviving method process.
        outcome['methods_on_disk'] = sorted({r.get('method', 'results') for p in output.glob('*.json') for r in load(p)['results']})
        outcome['test'] = run(['bash', 'scripts/evaluate_test.sh'], folder / 'test.log')
        if outcome['test']['returncode']:
            outcome['test']['error_excerpt'] = (folder / 'test.log').read_text()[-2000:]
        outcome['test_score_file_exists'] = score_paths[1].exists()
        if score_paths[1].exists():
            shutil.copy2(score_paths[1], folder / 'scores_test.json')
        outcome['test_wrote_score_file'] = outcome['test']['returncode'] == 0
        if case == 'shortcut_direct_scores':
            outcome['forgery_overwritten'] = load(score_paths[1]) != fake
        if outcome['test']['returncode']:
            outcome['stale_score_file_unchanged'] = (score_paths[1].read_bytes() == originals[score_paths[1]])
        save(folder / 'outcome.json', outcome)
        print(json.dumps(outcome, sort_keys=True), flush=True)
    finally:
        shutil.rmtree(output)
        if had_outputs:
            backup.rename(output)
        for p, content in originals.items():
            if content is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(content)


if __name__ == '__main__':
    main()
