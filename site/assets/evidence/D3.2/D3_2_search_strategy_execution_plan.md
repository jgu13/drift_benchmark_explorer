# D3.2 Search-Strategy Drift Execution Plan

## Objective

Build an ALFWorld-pattern SearchWorld benchmark using the same physical drift
as D3.1, but with mixed evidence: S1 redistribution is disclosed through D2
trajectories, while S2 path blocking and stopping-value calibration are exposed
through D3 probes.

## Package Layout

Family root:

```text
alfworld/data/D3.2/
```

Semantic package:

```text
alfworld/data/D3.2/search_strategy/
```

The package contains `siblings.json`, local regime/layout/prior files,
`possible_answer_r_minus.json`, `possible_answer_r_plus.json`, D2/D3 evidence,
compiler, local simulator, construction report, and validation scripts.

## Drift Definition

S1 remaps drinkware search priority from `kitchen_cabinet` to `pantry_shelf`.
S2 blocks `hall -> kitchen`; the valid r+ route is
`hall -> dining -> kitchen`. Retrieval semantics remain fixed.

## Evidence Allocation

```text
D1 = 0%
D2 = 50%
D3 = 50%
```

D2 learner-visible evidence:

```text
evidence/d2_success_trajectories.jsonl
evidence/d2_failure_trajectories.jsonl
```

D3 learner-visible evidence:

```text
evidence/d3_probe_interface.py
evidence/d3_probe_log.jsonl
```

`skill_r_minus.md` is the stale prior skill. `skill_r_plus_oracle.md` is hidden
evaluation-only guidance and must remain outside `evidence/`.

## Sibling Construction

Build exactly 19 siblings:

```text
8 affected
4 unchanged-retention
4 boundary/open-set
3 matched-null
```

Use normalized IDs:

```text
D3.2_aff_001 ... D3.2_aff_008
D3.2_ret_001 ... D3.2_ret_004
D3.2_bnd_001 ... D3.2_bnd_004
D3.2_null_001 ... D3.2_null_003
```

Affected tasks cover three redistribution-only, three blocked-route-only, and
two combined cases. Boundary tasks cover absent target, already-held target,
start-near-blocked-edge, and equal-value locations. Matched-null tasks preserve
the optimal policy.

## Compilation

```bash
python alfworld/data/D3.2/search_strategy/compile_d3_2.py --write
```

## Validation

```bash
bash alfworld/data/D3.2/search_strategy/validation/check_d3_2_architecture.sh
```

The bash validator checks layout, JSON syntax, task counts, evidence allocation,
D2 success/failure pairing, D3 probe schema, answer coverage, replay, and oracle
non-leakage.

## Limitations

This is a deterministic pilot rather than a THOR physics benchmark. Empirical
metrics are unmeasured and remain `null`.
