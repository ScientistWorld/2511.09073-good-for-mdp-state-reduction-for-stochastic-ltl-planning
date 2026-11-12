#!/usr/bin/env python3
"""Lightweight checks of saved audit evidence and restored gym source."""
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'
START = (AUDIT / 'restoration/start_commit.txt').read_text().strip()


def load(path):
    return json.loads(path.read_text())


def main():
    summary = load(AUDIT / 'summary.json')
    cases = {p.parent.name: load(p) for p in AUDIT.glob('*/outcome.json')}
    assert len(cases) == 18
    failures = {'shortcut_missing_benchmark', 'shortcut_null_count', 'shortcut_empty_output'}
    for case, outcome in cases.items():
        folder = AUDIT / case
        assert (folder / 'run.sh').is_file()
        assert outcome['hidden_command'] == ['bash', 'scripts/evaluate_test.sh']
        assert outcome['modified_evaluator'] is False
        assert outcome['test']['returncode'] == (1 if case in failures else 0)
        assert (folder / 'scores_test.json').is_file()
        assert (folder / 'scores_train.json').is_file()
        if case in failures:
            assert outcome['stale_score_file_unchanged']
            assert summary['cases'][case]['relation'] == 'failed_hidden_test_not_ranked'
    frozen = json.loads(subprocess.check_output(
        ['git', 'show', f'{START}:scoring/scores_test.json'], cwd=ROOT))
    for seed in [11, 22, 33]:
        assert load(AUDIT / f'reference_seed{seed}/scores_test.json') == frozen
    assert all(spread == 0 for metrics in summary['seed_metric_range'].values()
               for spread in metrics.values())
    assert summary['cases']['better_lib_falling']['honest_cohort_normalized_delta'] > 0
    assert summary['cases']['weaker_no_acceptance']['honest_cohort_normalized_delta'] < 0
    wins = ['shortcut_reported_counts', 'shortcut_ground_truth_options', 'shortcut_non_gfm']
    ties = ['shortcut_sparse_guards', 'shortcut_prune_registry']
    for case in wins:
        entry = summary['cases'][case]
        assert entry['improved'] and not entry['worsened']
        assert entry['audit_cohort_normalized_delta'] > 0
    for case in ties:
        assert summary['cases'][case]['paired_normalized_delta'] == 0
    assert len(summary['cases']['shortcut_prune_registry']['missing']) == 14
    for entry in load(AUDIT / 'shortcut_prune_registry/scores_test.json')['experiments'].values():
        assert 'shortcut_unregistered_method' not in entry['results']
    assert cases['shortcut_direct_scores']['forgery_overwritten']
    cross = load(AUDIT / 'extra_checks.json')
    assert sum(x['count'] for x in cross['better_lib_dense_random_checks']) == 392
    assert all(x['reference_correct'] == x['better_correct'] == x['count']
               for x in cross['better_lib_dense_random_checks'])
    assert len(cross['shortcut_sparse_guard_counterexamples']) == 13
    assert all(x['true_answer'] and x['reference_answer'] and not x['shortcut_answer']
               for x in cross['shortcut_sparse_guard_counterexamples'])
    assert cross['iid_mdp_tdr_7']['reference']['optimal_buchi_probability'] == 1
    assert cross['iid_mdp_tdr_7']['shortcut_non_gfm']['optimal_buchi_probability'] == 0
    protected = ['baseline', 'briefing', 'data', 'environment', 'eval', 'method', 'paper',
                 'scoring', 'scripts', '.gitignore', 'MILESTONES.md', 'PROGRESS.md']
    subprocess.run(['git', 'diff', '--exit-code', START, '--', *protected], cwd=ROOT,
                   check=True, capture_output=True)
    assert (ROOT / 'scripts/run.sh').read_bytes() == (AUDIT / 'restoration/run.sh').read_bytes()
    result = {'status': 'passed', 'start_commit': START, 'case_count': len(cases),
              'successful_hidden_invocations': 15, 'intentionally_failed_hidden_invocations': 3,
              'strictly_paying_shortcuts': wins, 'paying_shortcut_ties': ties,
              'protected_gym_paths_unchanged': protected,
              'temporary_launcher_restored': True,
              'seed_metric_and_rank_spread': 0,
              'note': 'Checks recorded evidence only; no model construction or inference is run.'}
    (AUDIT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
