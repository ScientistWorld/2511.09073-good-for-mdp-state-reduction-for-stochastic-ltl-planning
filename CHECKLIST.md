# Reproduction Checklist

## Briefing
- [x] `briefing/problem.md` (method-agnostic)
- [x] `briefing/evaluation.md` (method-agnostic)
- [x] `briefing/method.md`
- [x] `briefing/overview.md`

## Scoring
- [x] `scoring/reference.json` - paper's reported numbers
- [x] `scoring/scores.json` - reproduced numbers
- [x] `scoring/EXPERIMENTS.md`
- [x] `scoring/TARGETS.md`
- [x] `scoring/CONSTRAINTS.md`
- [x] `scoring/DIRECTION.md`
- [x] Workspace validated via `python validate.py --compare`
- [x] Container job validated via `scripts/reproduce.sh`

## Code
- [x] Evaluation code in `eval/`
- [x] Method implementation in `method/`
- [x] Baseline implementation in `baseline/` (`brute_force_dba`, `weaker_dfa`; Owl/Slim are paper-reported only)

## Scripts
- [x] `scripts/evaluate.sh`
- [x] `scripts/reproduce.sh`
- [x] `scripts/download.sh`
- [x] `scripts/method.sh`

## Environment
- [x] `environment/container.def` + `environment/setup.sh`

## Data
- [x] Benchmark specifications tracked in `data/`
- [x] No pretrained models needed

## Milestones
- [x] `method_runs`
- [x] `core_claim`
- [ ] `core_claim_plus`
- [ ] `secondary_claims`
- [ ] `majority`
- [ ] `near_complete`
- [ ] `full`
