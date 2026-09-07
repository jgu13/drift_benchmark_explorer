# B2.3 — Priority-Selection Drift: D2-Only Agent Execution Plan
## Architecture Alignment Amendment

This plan is normalized to the reusable benchmark contract in
`data/Drift_benchmark_architecture_guide.md`.

Build B2.3 under:

```text
data/B_drift_benchmark/B2.3/
├── B2_3_priority_selection_D2_execution_plan.md
└── priority_selection/
    ├── README.md
    ├── generate_b2_3.py
    ├── compile_b2_3.py
    ├── rule_v1.json
    ├── rule_v2.json
    ├── drift_spec.json
    ├── source_task.json
    ├── source_task.md
    ├── siblings.json
    ├── sibling_summary.json
    ├── possible_answer_r_minus.json
    ├── possible_answer_r_plus.json
    ├── regime_r_minus.json
    ├── regime_r_plus.json
    ├── regime_null.json
    ├── skill_r_minus.md
    ├── skill_r_plus_oracle.md
    ├── evidence/
    │   ├── evidence_allocation.json
    │   ├── evidence_candidates.jsonl
    │   ├── d2_success_trajectories.jsonl
    │   └── d2_manifest_private.json
    └── validation/
        ├── construction_report.json
        ├── replay_checks.py
        └── test_b2_3_architecture.sh
```

The package root is `priority_selection/`, and `siblings.json` is the canonical
loader-facing task source. Package-level regime answers must use
`possible_answer_r_minus.json` and `possible_answer_r_plus.json`. Legacy/private
`gold_v1.jsonl` and `gold_v2.jsonl` may be emitted as aliases for source-rule
auditing, but they are not the loader contract.

Use architecture-style task IDs:

```text
B2.3_aff_001
B2.3_ret_001
B2.3_open_001
B2.3_null_001
```

The family should be registered in `data/dataloader.py` as:

```python
"B2.3": Path("B2.3/priority_selection/siblings.json")
```

When loading via the shared dataloader, use:

```bash
python data/dataloader.py --root data/B_drift_benchmark --benchmark-ids B2.3 --regime r+
```

### Source-Truth Correction

The executable source in `data/skilllearnbench_drift/gen/build_family_A.py`
defines:

```python
winner = min(pool, key=lambda r: (r["score"], -r["age_days"]))  # v1
winner = max(pool, key=lambda r: (r["score"], -r["age_days"]))  # v2
```

Therefore `v1` score ties choose the oldest record, but `v2` score ties choose
the youngest record. Although the source prose describes the tie-break as
retained, B2.3 follows the executable rule objects as required by this plan.
`P04 tie_break` is therefore changed in the normalized B2.3 drift spec.


## 0. Objective

Build **B2.3** as a drift benchmark derived from the existing `priority-selection` arbitrary-rule family.

The existing family already contains the hidden policy and its `v1 -> v2` change. **Do not invent a new ranking rule.** Reuse the family’s actual rule implementation, seed skill, generator, and tests as the source of truth.

B2.3 is the **D2-only** condition from the Roster:

```text
Family: priority-selection
Setting: B2.3

D1 = 0%
D2 = 100%
D3 = 0%

Initial pilot:
19 evaluation siblings
  8 affected
  4 unchanged-retention
  4 boundary/open-set
  3 matched-null
```

The solver starts from the stale `v1` skill and receives **successful post-drift sibling trajectories** generated under `v2`. It must infer and store the revised semantic adjudication rule, then apply it to fresh evaluation candidate sets.

The intended competence is:

```text
not:
memorize demonstrated candidate IDs and answers

but:
recover the v2 priority-selection policy
and transfer it to unseen candidate sets
```

---

## 1. Use the existing `priority-selection` family as the source substrate

Start from:

```text
data/skilllearnbench_drift/tasks/priority-selection/
```

The existing family uses the shared layout:

```text
<instance>/
├── instruction.md
├── task.toml
├── environment/
│   └── records.json
├── tests/
└── ...
```

Early beta instances may also contain:

```text
worked_examples.json
```

The source family already has 16 instances with:

```text
01-05  -> v1
06-11  -> v2
12-16  -> interleaved v1/v2
```

Do not treat the existing 16 instances as the final B2.3 evaluation pool. They are source material and sanity checks for the new generator.

---

## 2. Extract the actual hidden rule objects before building anything

Locate the family code, seed skill, generator, solution logic, tests, or constants that define `priority-selection`.

Create normalized private truth files:

```text
rule_v1.json
rule_v2.json
```

The task-family description establishes the following intended policy:

### v1

```text
eligibility:
    age_days <= 90

dominant category:
    if eligible Q records are present, Q dominates

score direction:
    lowest score wins

tie break:
    oldest record wins
```

### v2

```text
eligibility:
    age_days <= 30

dominant category:
    if eligible Z records are present, Z dominates

score direction:
    highest score wins

tie break:
    oldest record wins
```

Before writing the B2.3 generator, verify these against the executable source/tests.

If the implementation contains additional details not captured above, copy them into `rule_v1.json` and `rule_v2.json`.

**The executable source is authoritative.**

Do not introduce a new private weight, new tie-breaker, or new ranking field merely to match a generic Roster phrase.

---

## 3. Define the physical drift as an obligation delta

Create:

```text
drift_spec.json
```

Represent the existing change as independently auditable obligations.

Recommended obligation IDs:

```text
P01 eligibility_cutoff
P02 dominant_category
P03 score_direction
P04 tie_break_oldest
```

For the known family:

```text
P01:
    v1 <= 90 days
    v2 <= 30 days
    changed = true

P02:
    v1 dominant category = Q
    v2 dominant category = Z
    changed = true

P03:
    v1 score direction = minimum
    v2 score direction = maximum
    changed = true

P04:
    v1 tie break = oldest
    v2 tie break = oldest
    changed = false
```

Example normalized structure:

```json
{
  "family": "priority-selection",
  "setting": "B2.3",
  "schedule": "abrupt",
  "changed_obligations": ["P01", "P02", "P03"],
  "retained_obligations": ["P04"],
  "evidence": {
    "D1": 0,
    "D2": 100,
    "D3": 0
  }
}
```

The natural-language task goal remains unchanged:

```text
select one priority record
+
report all eligible record IDs
```

---

## 4. Build stale and oracle skills from the same rule objects

Create:

```text
skill_v1.md
skill_v2_oracle.md
```

`skill_v1.md` must encode the complete pre-drift policy.

`skill_v2_oracle.md` must encode the complete post-drift policy.

The adaptive solver receives:

```text
skill_v1.md
```

before the drift.

It must never receive:

```text
skill_v2_oracle.md
rule_v2.json
drift_spec.json
private obligation labels
```

Those are benchmark-side truth only.

---

## 5. Keep the task instruction rule-free

Reuse the source family’s semantic task framing.

The instruction should tell the agent to read:

```text
/root/records.json
```

and write:

```text
/root/answer.json
```

with:

```json
{
  "winner": "<record id>",
  "eligible_ids": ["<id>", "..."]
}
```

The instruction may state that the policy is private or non-obvious.

It must not state:

```text
30-day cutoff
Z dominates
highest score wins
oldest tie-break
```

Those are the post-drift skill contents to be inferred from D2.

---

## 6. B2.3 evidence contract

Create:

```text
evidence/evidence_allocation.json
```

with:

```json
{
  "D1": 0,
  "D2": 100,
  "D3": 0,
  "delivery": {
    "D1": null,
    "D2": "Successful post-drift trajectories are supplied once during adaptation. Each trajectory explicitly states one correct v2 rule and demonstrates it on one successful sibling.",
    "D3": null
  }
}
```

For this family, D2 should be deliberately **maximally revealing**.

A learner-visible trajectory contains:

```text
records
+
accepted answer
+
one explicit statement of exactly one correct post-drift rule
```

Use one trajectory per atomic rule. The target evidence decomposition is:

```text
trajectory 1 -> eligibility cutoff
trajectory 2 -> dominant category
trajectory 3 -> score direction
trajectory 4 -> tie-break rule
```

Do not merge several rule declarations into one trajectory unless the executable source makes them inseparable.

Do not provide a separate D1 changelog or policy memo. Do not provide D3 probes. The explicit rule statement is part of the successful D2 trajectory itself.

## 7. Reuse existing `worked_examples.json` as seed evidence, not automatically as the final evidence set

Inspect the `worked_examples.json` files in early beta source instances.

For each example:

1. identify which one atomic v2 rule it can cleanly demonstrate;
2. verify its accepted answer under the actual v2 grader;
3. attach an explicit natural-language statement of that one rule;
4. reject or redesign it if the trajectory would need to state several rules at once;
5. reject it if it overlaps any evaluation sibling.

If the existing worked examples do not provide one clean successful demonstration per rule, generate new evidence-only siblings.

The final D2 evidence should favor **clarity and completeness** over minimality.

## 8. Construct an evidence-only sibling pool

Create a private pool separate from the 19 evaluation siblings:

```text
evidence_candidates.jsonl
```

Generate many valid `records.json` candidate sets under the original source schema.

Each candidate must be compilable under both:

```text
rule_v1
rule_v2
```

For each evidence candidate, record privately:

```text
gold_v1
gold_v2
obligation_support
which alternative hypotheses it distinguishes
```

Use a separate ID namespace:

```text
B2.3-evidence-001
B2.3-evidence-002
...
```

Do not reuse:

```text
B2.3-aff-*
B2.3-ret-*
B2.3-open-*
B2.3-null-*
```

---

## 9. Build a minimal discriminating D2 evidence set

Do **not** optimize for the smallest implicit example set.

Instead, construct one successful trajectory whose explanation explicitly states each current rule.

For the current source family, target four trajectories:

```text
D2-01 -> eligibility cutoff rule
D2-02 -> dominant-category rule
D2-03 -> score-direction rule
D2-04 -> tie-break rule
```

The rules must be verified against executable source truth before serialization.

For the catalog-described implementation, the intended v2 rules are:

```text
eligibility:
    age_days <= 30

dominant category:
    category Z dominates when eligible Z records are present

score direction:
    highest score wins within the decisive eligible candidate set

tie break:
    oldest record wins
```

If executable source truth differs in an edge case, follow executable truth.

### D2-01 — eligibility cutoff

Construct a sibling with records around the threshold, ideally including:

```text
age_days = 30
age_days = 31
```

Explicitly state:

```text
Current rule: a record is eligible only when age_days <= 30.
```

### D2-02 — dominant category

Construct a sibling with eligible candidates from multiple categories including `Z`.

Explicitly state:

```text
Current rule: if any eligible category-Z record is present, category Z is the dominant category.
```

### D2-03 — score direction

Construct a sibling where at least two candidates survive eligibility/category selection and have distinct scores.

Explicitly state:

```text
Current rule: among the decisive eligible records, the highest score wins.
```

### D2-04 — tie break

Construct a sibling with a decisive score tie.

Explicitly state:

```text
Current rule: when decisive candidates tie, the oldest record wins.
```

The tie-break is retained rather than drifted, but exposing it makes the complete post-drift policy unambiguous.

## 10. D2 trajectory format

Create:

```text
evidence/d2_success_trajectories.jsonl
```

Each line explicitly reveals **one** post-drift rule and demonstrates that rule on a successful sibling.

Recommended learner-visible schema:

```json
{
  "evidence_id": "B2.3-D2-001",
  "regime": "v2",
  "rule_id": "eligibility_cutoff",
  "revealed_rule": "A record is eligible only when age_days <= 30.",
  "instruction": "Select the priority record and report all eligible IDs.",
  "records": [
    {"id": "R001", "age_days": 30, "category": "A", "score": 10},
    {"id": "R002", "age_days": 31, "category": "A", "score": 99}
  ],
  "accepted_answer": {
    "winner": "R001",
    "eligible_ids": ["R001"]
  },
  "verification": {
    "passed": true
  }
}
```

The exact record values must be generated from the real source schema and checked by the real v2 grader.

The evidence contract is:

```text
one trajectory
=
one explicit current rule
+
one concrete successful demonstration
```

For B2.3, `rule_id` and `revealed_rule` are intentionally learner-visible. Private construction metadata such as generation seed, alternative-hypothesis coverage, and provenance goes in:

```text
evidence/d2_manifest_private.json
```

## 11. What constitutes a successful trajectory

A D2 trajectory must be produced by executing the example against the actual v2 task grader.

Generation pipeline:

```text
evidence-only sibling
        +
v2 oracle skill / rule compiler
        |
        v
write /root/answer.json
        |
        v
run source tests
        |
        v
reward = pass
        |
        v
sanitize into D2 example
```

Never hand-label a trajectory as successful without verifier confirmation.

If using a model-generated agent transcript, do not expose chain-of-thought. Preserve or add the single required `revealed_rule` statement for that trajectory. Do not state unrelated rules in the same trajectory.

The informative evidence is intentionally:

```text
explicit current rule
+
records -> accepted output
```

---

## 12. Generate the 19 evaluation siblings

Create:

```text
siblings.json
```

with exactly:

```text
8 affected
4 unchanged-retention
4 boundary/open-set
3 matched-null
= 19
```

Each sibling should include benchmark-side metadata such as:

```json
{
  "id": "B2.3-aff-001",
  "slice": "affected",
  "regime": "v2",
  "obligation_support": ["P01", "P03"],
  "source_family": "priority-selection"
}
```

The metadata is not necessarily copied into the learner-facing environment.

---

## 13. Define affectedness by paired compilation

For every candidate sibling:

```python
gold_v1 = solve(records, rule_v1)
gold_v2 = solve(records, rule_v2)
```

Mark:

```text
affected
```

iff the drift changes at least one graded output:

```text
winner
eligible_ids
```

This should be computed, not guessed from the wording.

Also record which changed obligations are causally decisive.

---

## 14. Build the 8 affected siblings

The affected pool should cover the changed obligations individually and jointly.

Recommended sub-slices:

```text
cutoff-only decisive
dominant-category-only decisive
score-direction-only decisive
cutoff + category
cutoff + direction
category + direction
all-three interaction
```

Construction examples:

### Eligibility-cutoff cases

Include records with:

```text
age_days = 30
age_days = 31
ages well below 30
ages between 31 and 90
```

so the cutoff change affects eligibility.

### Dominant-category cases

Include eligible:

```text
Q and Z together
Z with non-Q categories
Q without Z
```

so the v1/v2 dominant-category difference becomes decisive.

### Score-direction cases

Create candidate pools where the same eligibility/category pool contains at least two distinct scores such that:

```text
minimum-score winner != maximum-score winner
```

### Interaction cases

Combine the changed obligations so a solver that updates only one clause still fails.

---

## 15. Build the 4 unchanged-retention siblings

These are valid `v2` tasks whose graded outputs happen to be invariant under `v1` and `v2`.

Find them by paired compilation:

```text
gold_v1 == gold_v2
```

Examples may include cases where:

```text
all potentially eligible records are <= 30 days
Q/Z dominance does not alter the decisive candidate pool
min/max ranking happens to choose the same record
oldest tie-break is decisive and unchanged
```

Do not assume a case is retention merely because it avoids one changed clause.

Verify full-output equality.

---

## 16. Build the 4 boundary/open-set siblings

Keep the source schema valid unless the original family explicitly supports malformed inputs.

Prioritize semantic boundaries:

```text
age_days exactly 30
age_days exactly 31
exact score ties
near score ties
multiple Q and Z records
oldest tie among equal scores
no eligible records, if the source family defines this case
single eligible record
candidate ordering permutations
```

The expected behavior must come from the existing rule compiler and grader.

Do not invent a new output convention for unsupported cases.

---

## 17. Build the 3 matched-null siblings

Matched-null siblings should vary the task surface while leaving the policy and expected output unchanged.

Possible null perturbations:

```text
record order permutation
instruction paraphrase
irrelevant record metadata change
ID renaming with consistently regenerated gold
non-decisive score/age perturbation that preserves the same winner and eligibility set
```

Use paired compilation to verify that the perturbation does not create a real policy-effect change.

A matched-null task should not trigger a persistent rule edit.

---

## 18. Compile gold outputs automatically

Create:

```text
compile_b2_3.py
```

Inputs:

```text
rule_v1.json
rule_v2.json
siblings.json
```

Outputs:

```text
gold_v1.jsonl
gold_v2.jsonl
sibling_summary.json
```

For each sibling store privately:

```text
gold_v1
gold_v2
changed?
decisive obligations
```

Do not manually maintain independent gold files.

---

## 19. Adaptation delivery to the solver

Recommended evaluation episode:

```text
1. give stale skill_v1.md
2. give evidence/d2_success_trajectories.jsonl once
3. allow the method to update its persistent skill
4. remove direct access to the oracle
5. evaluate on held-out B2.3 siblings
```

Do not repeat the D2 evidence inside every evaluation prompt.

All adaptive methods should receive the same D2 set under the same adaptation budget.

---

## 20. Construction controls

Before evaluating full adaptive baselines, run:

```text
zero_shot
static_v1
simple_D2_update
oracle_v2
```

Interpretation:

```text
zero_shot:
    no seed skill, no D2

static_v1:
    stale skill only

simple_D2_update:
    stale skill + D2 successful trajectories

oracle_v2:
    current skill only
```

This first pass validates benchmark construction, not method superiority.

---

## 21. Validation

### Oracle correctness

```text
oracle_v2
```

must solve every valid evaluation sibling.

### Stale-skill gap

Affected siblings should produce a meaningful difference between:

```text
static_v1
oracle_v2
```

### D2 explicit-rule completeness

Using only the learner-visible D2 trajectories, every current post-drift rule should be explicitly stated at least once and demonstrated by a successful concrete sibling.

### Novel transfer

A solver that merely memorizes evidence IDs/records should fail on held-out generated candidate sets.

### Retention

Updating the rule should not reduce performance on unchanged-retention siblings.

### Boundary behavior

Check exact cutoff/tie cases.

### No evidence leakage

Evidence and evaluation sibling hashes must be disjoint.

---

## 22. Recommended metrics

Primary:

```text
Q_after
affected-slice Q
unchanged-retention Q
boundary/open-set Q
matched-null Q
```

Drift metrics:

```text
G_Q^need
G_Q^stale
RR
```

Rule-recovery diagnostics:

```text
eligibility cutoff error
dominant-category recovery
score-direction recovery
tie-break retention
semantic transfer rate (STR)
collateral damage (CD)
```

Do not fabricate empirical values before execution.

---

## 23. Recommended package

```text
B2.3/
├── B2_3_priority_selection_execution_plan.md
└── priority_selection/
    ├── README.md
    ├── extract_source_rules.py
    ├── rule_v1.json
    ├── rule_v2.json
    ├── drift_spec.json
    ├── skill_v1.md
    ├── skill_v2_oracle.md
    ├── generate_b2_3.py
    ├── compile_b2_3.py
    ├── siblings.json
    ├── sibling_summary.json
    ├── gold_v1.jsonl
    ├── gold_v2.jsonl
    ├── evidence/
    │   ├── evidence_allocation.json
    │   ├── evidence_candidates.jsonl
    │   ├── d2_success_trajectories.jsonl
    │   └── d2_manifest_private.json
    └── validation/
        ├── replay_source_grader.py
        ├── validate_evidence_identifiability.py
        ├── validate_evidence_disjointness.py
        ├── validate_sibling_slices.py
        └── construction_report.json
```

---

## 24. Suggested implementation order

1. Locate the existing `priority-selection` rule implementation and tests.
2. Extract exact `v1` and `v2` policies.
3. Reproduce all original 16 source-instance gold answers.
4. Create normalized `rule_v1.json` and `rule_v2.json`.
5. Define changed and retained obligations.
6. Build a large candidate sibling generator.
7. Generate candidate D2 evidence-only siblings.
8. Compute a minimal discriminating D2 set.
9. Verify every selected D2 trajectory under the v2 grader.
10. Write learner-visible `d2_success_trajectories.jsonl`.
11. Generate the 19 evaluation siblings.
12. Enforce the 8/4/4/3 slice counts.
13. Compile v1/v2 gold outputs.
14. Validate evidence/evaluation disjointness.
15. Run zero-shot/static/simple-D2/oracle construction controls.
16. Only after construction passes, run SkillEvolver/GRASP/SkillTTA or other adaptive methods.

---

## 25. Acceptance checklist

- [ ] no new hidden priority policy was invented;
- [ ] exact source `v1` and `v2` rules were extracted and replay-validated;
- [ ] D1 = 0%;
- [ ] D2 = 100%;
- [ ] D3 = 0%;
- [ ] D2 contains successful post-drift examples rather than a policy declaration;
- [ ] all D2 examples pass the actual v2 grader;
- [ ] each learner-visible D2 trajectory explicitly states exactly one correct post-drift rule;
- [ ] every current post-drift rule is covered by at least one trajectory;
- [ ] each concrete trajectory actually exercises the rule it states;
- [ ] evidence siblings are disjoint from evaluation siblings;
- [ ] the solver starts from the stale v1 skill;
- [ ] exactly 19 evaluation siblings are generated;
- [ ] slice counts are 8/4/4/3;
- [ ] affectedness is determined by paired v1/v2 compilation;
- [ ] oracle solves every valid sibling;
- [ ] retention/null cases detect collateral edits and spurious updating;
- [ ] empirical metrics remain unset until execution.

---

## 26. Minimal conceptual summary

```text
existing priority-selection family

v1 hidden policy
    |
    | abrupt drift already encoded by family
    v
v2 hidden policy
    |
    +---- evidence-only v2 siblings
    |          |
    |          v
    |   successful input/output trajectories
    |          |
    |          v
stale v1 skill + D2 100%
            |
            v
store the explicitly revealed revised semantic policy
            |
            v
19 fresh held-out siblings
            |
            v
test application of revealed rules rather than record memorization
```
