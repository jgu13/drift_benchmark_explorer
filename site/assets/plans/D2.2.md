# D2.2 — Updated Design-Level Execution Plan (19 Siblings)

## Goal

Extend D2.2 into the **same 19-task pilot sibling family** used by D2.1.

D2.2 keeps:

- source: OSWorld-V2 `task_052`
- skill family: navigation / menu-tree strategy
- drift: `path_permute + shortcut_add`
- topology: replacement + improvement
- schedule: abrupt
- semantic goals and graders unchanged

Evidence is the only intended difference:

```text
D1 = 0%
D2 = 0%
D3 = 100%
```

The learner must recover the current graph from environment interaction alone.

---

## 1. Reuse the D2.1 family definition

The following should be shared or generated from the same source:

```text
state_catalog.json
regime_r_minus.json
regime_r_plus.json
regime_null.json
siblings.jsonl
sibling_summary.json
grader_spec.json
skill_r_minus.md
skill_r_plus_oracle.md
```

Do not create a different task pool for D2.2.

---

## 2. Directory

```text
drift_benchmark/D2.2/task_052_family/
├── README.md
├── state_catalog.json
├── regime_r_minus.json
├── regime_r_plus.json
├── regime_null.json
├── skill_r_minus.md
├── skill_r_plus_oracle.md
├── d3_evidence.jsonl
├── evidence_allocation.json
├── siblings.jsonl
├── sibling_summary.json
├── grader_spec.json
└── validation/
    ├── validate_siblings.py
    ├── validate_graph_coupling.py
    └── construction_report.json
```

There must be no learner-visible D1 notice or D2 demonstration file.

---

## 3. Shared state catalog

```text
S0    = entry, ad visible
S1    = main page
SH    = Hotels hub
S2    = Le Meurice details
S2A   = amenities
S2R   = room list
S3D   = Deluxe selected
S3P   = Prestige selected
S4    = checkout/personal information
SFAV  = saved hotel
SHELP = help
SACCT = account/preferences
```

---

## 4. Shared `r-` graph

```text
S0  --close_ad---------------> S1
S1  --open_Le_Meurice--------> S2
S1  --open_help--------------> SHELP
S1  --open_account-----------> SACCT
S2  --view_amenities---------> S2A
S2  --open_rooms-------------> S2R
S2  --save_hotel-------------> SFAV
S2R --select_Deluxe_Suite----> S3D
S2R --select_Prestige_Room---> S3P
S3D --continue_checkout------> S4
S3P --continue_checkout------> S4
```

---

## 5. Shared `r+` drift

Remove:

```text
S1 --open_Le_Meurice--> S2
```

Add:

```text
S1 --open_Hotels--> SH
SH --open_Le_Meurice--> S2
```

Add shortcut:

```text
S1 --featured_Deluxe_Suite--> S3D
```

Everything downstream stays unchanged.

---

## 6. Same 19 sibling tasks

Use the exact same logical IDs:

```text
8 affected
D2-aff-001 ... D2-aff-008

5 unchanged-retention
D2-ret-001 ... D2-ret-005

4 boundary/open-set
D2-open-001 ... D2-open-004

2 matched-null
D2-null-001 ... D2-null-002
```

---

## 7. Affected siblings

### D2-aff-001
- initial `S0`
- reserve Le Meurice Deluxe
- goal `S4`
- tests replacement + shortcut

### D2-aff-002
- initial `S1`
- reserve Le Meurice Deluxe
- goal `S4`
- directly tests shortcut

### D2-aff-003
- initial `S1`
- open Le Meurice details
- goal `S2`

### D2-aff-004
- initial `S1`
- view Le Meurice amenities
- goal `S2A`

### D2-aff-005
- initial `S1`
- open Le Meurice room list
- goal `S2R`

### D2-aff-006
- initial `S1`
- reserve Prestige Room
- goal `S4`
- no shortcut applies
- correct route `S1 → SH → S2 → S2R → S3P → S4`

### D2-aff-007
- initial `S1`
- save Le Meurice
- goal `SFAV`

### D2-aff-008
- initial `S1`
- reserve Deluxe
- goal `S4`
- step cap `2`
- only shortcut route fits

---

## 8. Unchanged-retention siblings

```text
D2-ret-001: S2 → amenities → S2A
D2-ret-002: S2 → rooms → S2R
D2-ret-003: S2R → Deluxe → checkout → S4
D2-ret-004: S2R → Prestige → checkout → S4
D2-ret-005: S1 → help → SHELP
```

These measure collateral damage and unnecessary exploration.

---

## 9. Boundary/open-set siblings

### D2-open-001
Unknown hotel (`Hotel Imaginaire Paris`) → not found / abstain.

### D2-open-002
Unavailable room (`Presidential Penthouse`) → unavailable / abstain.

### D2-open-003
Ambiguous `Reserve a Deluxe Suite` → clarify hotel / abstain.

### D2-open-004
Request to jump through hidden checkout route → do not use prohibited hidden/direct navigation.

---

## 10. Matched-null siblings

### D2-null-001
Visible `Hotels` label changes to `Stays`, transition graph unchanged.

Expected: no structural graph rewrite.

### D2-null-002
Featured card is visually reordered, transition/cost unchanged.

Expected: no graph or policy rewrite.

---

## 11. Shared obligations

```text
O1 = old S1 → Le Meurice edge invalid
O2 = S1 → Hotels valid
O3 = Hotels → Le Meurice valid
O4 = Featured Deluxe → S3D valid
O5 = shortcut is target-specific
O6 = shortcut is cheaper
```

Support:

```text
aff-001: O1,O2,O3,O4,O6
aff-002: O4,O6
aff-003: O1,O2,O3
aff-004: O1,O2,O3
aff-005: O1,O2,O3
aff-006: O1,O2,O3,O5
aff-007: O1,O2,O3
aff-008: O4,O6
```

---

## 12. D2.2 evidence constraints

Do **not** provide:

```text
D1 changelog
D1 localization notice
D2 successful demonstrations
solved post-drift trajectories
```

All new-regime information must come from D3 interaction.

---

## 13. D3 interaction interface

Expose observations of:

```text
state
action
next_state or failure
cost
```

Examples:

```json
{"state":"S1","action":"open_Le_Meurice","next_state":null,"cost":1,"outcome":"action_unavailable"}
```

```json
{"state":"S1","action":"open_Hotels","next_state":"SH","cost":1,"outcome":"valid_transition"}
```

```json
{"state":"SH","action":"open_Le_Meurice","next_state":"S2","cost":1,"outcome":"valid_transition"}
```

```json
{"state":"S1","action":"featured_Deluxe_Suite","next_state":"S3D","cost":1,"outcome":"valid_transition"}
```

Every interaction is safe, bounded, and metered.

---

## 14. Do not leak the full graph via static D3

Preferred setup:

```text
probe/environment interface
+
adaptation budget
```

If early baseline code requires static evidence, expose sequential evidence atoms and count each as one discovery unit.

Do not hand the learner the full `r+` graph as one file.

---

## 15. Evidence/evaluation separation

The 19 evaluation siblings must never be given as solved interaction traces.

Evidence scenarios may share obligations but should use different wording or downstream goals.

Example:

```text
evidence: discover Hotels → Le Meurice while attempting a detail lookup
evaluation: later solve amenities or save-hotel sibling
```

This tests transfer of the learned graph.

---

## 16. Grading

Use the same semantic/state graders as D2.1.

Primary score: semantic task success.

Diagnostic scores:

```text
invalid actions
task execution cost
adaptation cost
step-cap failure
spurious update
```

Exact path match is not the primary metric.

---

## 17. Stale failure expectations

Affected tasks may show:

```text
removed-edge failure
extra recovery actions
missed shortcut
step-cap failure
```

Retention tasks should remain valid.

Open-set tasks should expose shortcut overgeneralization.

Null tasks should expose spurious structural updates.

---

## 18. Result schema

```json
{
  "family": "D2.2",
  "task_id": "D2-aff-008",
  "method": "SkillEvolver",
  "slice": "affected",
  "success": true,
  "semantic_score": 1.0,
  "actions": [],
  "task_cost": 2,
  "invalid_actions": 0,
  "adaptation_cost": 5,
  "updated_skill": null
}
```

Use the same schema for D2.1.

---

## 19. Acceptance checks

Before expensive baseline runs:

- all 19 task definitions match D2.1;
- all graders match D2.1;
- `r-`/`r+` graphs match D2.1;
- no D1 reaches the learner;
- no D2 demonstrations reach the learner;
- all changed obligations are discoverable through D3;
- D3 is bounded and metered;
- at least one stale correctness failure exists;
- at least one stale correct-but-costly case exists;
- D2-aff-008 distinguishes shortcut discovery under a cap;
- boundary tasks detect shortcut overgeneralization;
- null tasks detect spurious graph rewriting.

---

## 20. Paired D2.1 vs D2.2 analysis

Because the task pool is identical, compute paired differences such as:

```text
Q(D2.1) - Q(D2.2)
adaptation_cost(D2.1) - adaptation_cost(D2.2)
invalid_actions(D2.1) - invalid_actions(D2.2)
```

Scientific question:

```text
Does partial declaration/localization reduce the interaction
needed to recover the same underlying navigation drift?
```

---

## 21. Scaling rule

After the 19-task pilot works, expand both D2.1 and D2.2 together to:

```text
48 total
19 affected
14 unchanged-retention
10 boundary/open-set
5 matched-null
```

Vary:

```text
initial state
downstream goal
room target
shortcut applicability
step cap
surface wording
null perturbation
```

Keep physical drift fixed.

---

## 22. Conceptual summary

```text
same 19 tasks
    |
    +-- 8 affected
    +-- 5 retention
    +-- 4 open-set
    +-- 2 matched-null
    |
same r- → r+
path_permute + shortcut_add
    |
D2.2:
D1 0
D2 0
D3 100%
    |
interaction-only graph reconstruction
    |
update navigation graph + preferred route
    |
held-out sibling evaluation
```
