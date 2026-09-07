# D3.1 Search-Strategy Drift Execution Plan

## Objective

Build an ALFWorld-pattern search-strategy drift benchmark where the semantic
object-retrieval goal is stable, but the optimal search policy changes after a
physical drift. The benchmark is D3-only: there is no changelog and no
demonstration; adaptation evidence is available only through metered,
current-regime probes.

The constructed benchmark must be self-contained under:

```text
alfworld/data/D3.1/
```

with the semantic package:

```text
alfworld/data/D3.1/search_strategy/
```

## Package Layout

The family root contains this execution plan and the constructed package:

```text
alfworld/data/D3.1/
├── D3_1_search_strategy_execution_plan.md
└── search_strategy/
    ├── README.md
    ├── compile_d3_1.py
    ├── drift_spec.json
    ├── source_task.json
    ├── siblings.json
    ├── sibling_summary.json
    ├── possible_answer_r_minus.json
    ├── possible_answer_r_plus.json
    ├── regime_r_minus.json
    ├── regime_r_plus.json
    ├── regime_null.json
    ├── layout_r_minus.json
    ├── layout_r_plus.json
    ├── search_prior_r_minus.json
    ├── search_prior_r_plus.json
    ├── searchworld_simulator.py
    ├── skill_r_minus.md
    ├── skill_r_plus_oracle.md
    ├── evidence/
    │   ├── d3_probe_log.jsonl
    │   └── evidence_allocation.json
    └── validation/
        ├── check_d3_1_architecture.sh
        ├── construction_report.json
        └── replay_checks.py
```

`siblings.json` is the canonical task source. `possible_answer_r_minus.json`
and `possible_answer_r_plus.json` are the package-level compiled answer files.

## Drift Definition

Build a deterministic SearchWorld substrate with locations:

```text
foyer
hall
kitchen
dining
pantry
bedroom
bathroom
storage
```

Actions and costs:

```text
move(location) = 1
inspect(receptacle) = 1
take(object) = 1
stop() = 0
invalid move = 1
```

Use a cost-sensitive hard cap on every sibling.

Two atomic drift obligations define the r+ regime:

```text
S1 redistribution:
  r_minus: drinkware is high-probability in kitchen_cabinet
  r_plus:  drinkware is high-probability in pantry_shelf

S2 path_block:
  r_minus: hall -> kitchen is valid
  r_plus:  hall -> kitchen is blocked
  alternate route: hall -> dining -> kitchen
```

The object-retrieval success semantics do not change. A sibling is affected
only when executable support shows that its gold or optimal trace intersects a
changed obligation, its graded final output differs, or its current optimal
cost target changes.

## Evidence Allocation

The evidence allocation is:

```text
D1 = 0%
D2 = 0%
D3 = 100%
```

Learner-visible evidence lives only under `evidence/` and must use lowercase
D-level filename prefixes. For D3.1, the only learner-visible evidence file is:

```text
evidence/d3_probe_log.jsonl
```

`skill_r_minus.md` represents the stale prior skill the learner may enter with.
It is not placed under `evidence/` and is not counted as D1 or D2 evidence.
`skill_r_plus_oracle.md` is hidden evaluation-only oracle guidance and must not
be exposed through the learner evidence API.

D3 probes must be safe, metered, current-regime, evidence-only, and disjoint
from evaluation siblings. Each probe record contains:

```text
probe_id
rule_id
state_before
action
arguments
response
state_after
cost
```

The D3 probes provide one stale/negative observation and one confirming
current-regime observation for each changed obligation when both are needed.

## Sibling Construction

Build exactly 19 evaluation siblings with normalized family-prefixed IDs:

```text
8 affected:             D3.1_aff_001 ... D3.1_aff_008
4 unchanged-retention:  D3.1_ret_001 ... D3.1_ret_004
4 boundary/open-set:    D3.1_bnd_001 ... D3.1_bnd_004
3 matched-null:         D3.1_null_001 ... D3.1_null_003
```

Affected siblings:

```text
3 redistribution-only
3 blocked-route-only
2 interaction cases using both S1 and S2
```

At least two affected siblings must remain eventually solvable by exhaustive
stale search while exceeding or approaching the cost cap, so efficiency drift is
measurable even when the final semantic state is unchanged.

Unchanged-retention siblings must avoid the changed drinkware placement and the
blocked hall->kitchen edge.

Boundary/open-set siblings must cover:

```text
target absent from all searchable locations
target already in inventory
start state on opposite side of blocked edge
two locations with equal expected search value
```

Use explicit stopping or abstention behavior for absent targets.

Matched-null siblings must cover:

```text
room naming paraphrase
irrelevant object relocation
equivalent graph presentation / neighbor ordering
```

and have identical optimal policy under r- and r+.

## Compilation

The package compile script is:

```text
alfworld/data/D3.1/search_strategy/compile_d3_1.py
```

It must:

1. Load `siblings.json`.
2. Compile each task's r- trace into `possible_answer_r_minus.json`.
3. Compile each task's r+ trace into `possible_answer_r_plus.json`.
4. Preserve `regime_null.json` for matched-null controls.
5. Avoid upstream BFCL or external benchmark imports.

Recommended command:

```bash
python alfworld/data/D3.1/search_strategy/compile_d3_1.py --write
```

## Validation

Validation must be self-contained and local to the package:

```text
alfworld/data/D3.1/search_strategy/validation/replay_checks.py
alfworld/data/D3.1/search_strategy/validation/check_d3_1_architecture.sh
```

The replay validator executes compiled answer traces against local
`searchworld_simulator.py` backends for r- and r+, verifies final state,
validates trace cost, and checks slice counts.

The bash architecture test checks:

1. Required family/package layout exists.
2. JSON sidecars are syntactically valid.
3. `siblings.json` is a manifest with exactly 19 tasks.
4. Slice counts are 8 affected, 4 retention, 4 boundary/open-set, and 3
   matched-null.
5. Evidence allocation is D1=0, D2=0, D3=100.
6. Learner-visible evidence files use D-level prefixes.
7. Skills exist and oracle skill is outside `evidence/`.
8. Package-level `possible_answer_r_minus.json` and
   `possible_answer_r_plus.json` exist and cover all tasks.
9. Local replay validation passes.

Recommended command:

```bash
bash alfworld/data/D3.1/search_strategy/validation/check_d3_1_architecture.sh
```

## Limitations

This is a deterministic pilot, not an empirical ALFWorld calibration. The
construction report must leave unmeasured empirical metrics as `null`. The
pilot intentionally uses 19 siblings before any larger sweep. The local
SearchWorld simulator mirrors ALFWorld-style object retrieval and search-order
drift, but it is not a THOR physics benchmark.
