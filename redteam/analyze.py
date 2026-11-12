#!/usr/bin/env python3
"""Audit-only ranking: directions, coefficient magnitudes, population std units."""
import json
from pathlib import Path
import statistics

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'
config = json.loads((ROOT / 'scoring/reference.json').read_text())['experiments']


def load(path):
    return json.loads(path.read_text())


def method_scores(case):
    blob = load(AUDIT / case / 'scores_test.json')['experiments']
    return {exp: entry.get('results', {}).get('gfm_gf', {}) for exp, entry in blob.items()}


def delta(candidate, reference, cohort):
    total = 0.0
    terms = []
    for exp, cfg in config.items():
        for metric, spec in cfg['metrics'].items():
            ref = reference.get(exp, {}).get(metric)
            value = candidate.get(exp, {}).get(metric)
            if ref is None or value is None:
                continue  # This is the gym's stated missing-value rule.
            observations = [s[exp][metric] for s in cohort if metric in s.get(exp, {})]
            std = statistics.pstdev(observations) if len(observations) > 1 else 0.0
            if not std:
                continue
            direction = 1 if spec['higher_is_better'] else -1
            term = cfg['weight'] * abs(spec['coefficient']) * direction * (value - ref) / std
            total += term
            terms.append({'experiment': exp, 'metric': metric, 'delta': term, 'population_std': std})
    return {'delta': total, 'terms': terms}


def main():
    outcomes = {p.parent.name: load(p) for p in AUDIT.glob('*/outcome.json')}
    successful = {case: method_scores(case) for case, out in outcomes.items()
                  if out.get('test', {}).get('returncode') == 0}
    ref = successful['reference_seed11']
    honest_names = ['reference_seed11', 'better_lib_falling', 'weaker_no_acceptance']
    honest_cohort = [successful[c] for c in honest_names]
    audit_cohort = list(successful.values())
    results = {}
    for case, outcome in sorted(outcomes.items()):
        entry = {'hidden_exit_code': outcome.get('test', {}).get('returncode')}
        if case in successful:
            scores = successful[case]
            entry.update(scores=scores, paired_normalized_delta=delta(scores, ref, [ref, scores])['delta'],
                         audit_cohort_normalized_delta=delta(scores, ref, audit_cohort)['delta'])
            if case in honest_names:
                entry['honest_cohort_normalized_delta'] = delta(scores, ref, honest_cohort)['delta']
            improvements, losses, missing = [], [], []
            for exp, cfg in config.items():
                for metric, spec in cfg['metrics'].items():
                    if metric not in scores.get(exp, {}):
                        missing.append(f'{exp}/{metric}')
                        continue
                    gain = (scores[exp][metric] - ref[exp][metric]) * (1 if spec['higher_is_better'] else -1)
                    if gain > 0:
                        improvements.append(f'{exp}/{metric}')
                    if gain < 0:
                        losses.append(f'{exp}/{metric}')
            entry.update(improved=improvements, worsened=losses, missing=missing)
            entry['relation'] = ('dominates_reference' if improvements and not losses else
                                 'ties_observed_reference' if not improvements and not losses else
                                 'worse_than_reference' if losses and not improvements else 'tradeoff')
        else:
            entry['relation'] = 'failed_hidden_test_not_ranked'
            entry['stale_score_file_unchanged'] = outcome.get('stale_score_file_unchanged')
        results[case] = entry
    seed_scores = [successful[f'reference_seed{s}'] for s in [11, 22, 33]]
    spread = {exp: {metric: max(s[exp][metric] for s in seed_scores) - min(s[exp][metric] for s in seed_scores)
                    for metric in cfg['metrics']} for exp, cfg in config.items()}
    summary = {'normalization_note': 'Exact future attempt-population stds are unknown. Paired deltas use the reference and one candidate as a two-attempt cohort. Audit-cohort deltas use all 15 successful runs, including duplicate references and the negative-count outlier. Honest-cohort deltas are reported only for reference/better/weaker, using those three attempts. Population standard deviations are used; constant metrics contribute zero. Pareto dominance and exact ties do not depend on the positive normalizers. Missing values are skipped as specified. Coefficient signs are discarded.',
               'audit_cohort': sorted(successful), 'honest_cohort': honest_names,
               'reference': ref, 'seed_metric_range': spread, 'cases': results}
    (AUDIT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for case, entry in results.items():
        print(case, entry['relation'], entry.get('paired_normalized_delta'), entry.get('audit_cohort_normalized_delta'))


if __name__ == '__main__':
    main()
