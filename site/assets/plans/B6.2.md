# B6.2 — Discount-Calculation Drift: D2-Only Agent Execution Plan
## Architecture Alignment Amendment

This plan is normalized to the reusable benchmark contract in
`data/Drift_benchmark_architecture_guide.md`.

Build B6.2 under:

```text
data/B_drift_benchmark/B6.2/
├── B6_2_discount_calculation_D2_execution_plan.md
└── discount_calculation/
    ├── README.md
    ├── generate_b6_2.py
    ├── compile_b6_2.py
    ├── formula_v1.json
    ├── formula_v2.json
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
        └── test_b6_2_architecture.sh
```

The package root is `discount_calculation/`, and `siblings.json` is the
canonical loader-facing task source. Package-level regime answers must use
`possible_answer_r_minus.json` and `possible_answer_r_plus.json`. Private/source
audit aliases `gold_v1.jsonl` and `gold_v2.jsonl` may also be emitted.

Use architecture-style task IDs:

```text
B6.2_aff_001
B6.2_ret_001
B6.2_open_001
B6.2_null_001
```

The family should be registered in `data/dataloader.py` as:

```python
"B6.2": Path("B6.2/discount_calculation/siblings.json")
```

When loading via the shared dataloader, use:

```bash
python data/dataloader.py --root data/B_drift_benchmark --benchmark-ids B6.2 --regime r+
```

### Extracted Source Truth

The executable source in `data/skilllearnbench_drift/gen/build_arbitrary_families.py`
defines:

```python
MULT_V1 = {"A": 1.2, "B": 1.5, "C": 2.0}
MULT_V2 = {"A": 1.1, "B": 1.4, "C": 1.8}
# v1: anchor = second-lowest price; fee = 5 * floor(raw / 5)
# v2: anchor = second-highest price; fee = 10 * ceil(raw / 10)
```

No cap, tax, or additional operation-order term exists in the executable source.
B6.2 therefore records `F05 operation_order` as retained multiply-then-round
semantics and does not create `F06 cap`.


## 0. Objective

Build **B6.2** as a drift benchmark derived from the existing `discount-calculation` arbitrary-rule family.

The source family already contains the hidden pricing formula and its `v1 -> v2` transition. **Do not invent a new formula, coefficient table, cap, or ordering rule.** Extract the exact rule from the existing family implementation and use it as benchmark truth.

B6.2 is the **D2-only** condition from the Roster:

```text
Family: discount-calculation
Setting: B6.2

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

The solver starts with the stale `v1` pricing skill and receives only successful post-drift invoice trajectories. It must infer the current semantic formula and transfer it to unseen invoices.

The desired competence is:

```text
not:
memorize demonstrated invoice -> fee pairs

but:
recover the v2 anchor selection,
tier-dependent numeric parameters,
and rounding/operation semantics
```

---

## 1. Use the existing `discount-calculation` family as source truth

Start from:

```text
data/skilllearnbench_drift/tasks/discount-calculation/
```

The source instances follow the shared layout:

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

The arbitrary-rule stream is:

```text
01-05  -> v1
06-11  -> v2
12-16  -> interleaved v1/v2
```

Use the original 16 instances as source/regression tests, not as the final B6.2 evaluation pool.

---

## 2. Extract the exact v1 and v2 pricing rules

Locate the source family generator, seed skill, solution code, test oracle, or constants.

Create:

```text
formula_v1.json
formula_v2.json
```

The task-family description establishes these core semantics:

### v1

```text
anchor item:
    second-lowest price

tier:
    apply the v1 tier multiplier

rounding:
    round DOWN to a multiple of 5
    after tier multiplication
```

### v2

```text
anchor item:
    second-highest price

tier:
    apply the v2 tier multiplier table

rounding:
    round UP to a multiple of 10
```

The source description intentionally does not enumerate every numeric multiplier.

Therefore:

```text
extract exact multiplier values from the implementation
```

rather than inventing them.

If the existing source family truly contains additional parameters such as:

```text
cap
tax/discount ordering
other coefficients
```

include them in the normalized formula objects.

If those fields do not exist in the executable source, do not add them merely because the Roster uses a generic formula-family description.

---

## 3. Normalize the formula into auditable obligations

Create:

```text
drift_spec.json
```

Recommended obligation decomposition:

```text
F01 anchor_selector
F02 tier_multiplier_table
F03 rounding_direction
F04 rounding_quantum
F05 operation_order
F06 cap
```

Only mark `F05`/`F06` present if the source implementation contains them.

For the catalog-guaranteed drift:

```text
F01:
    second-lowest -> second-highest
    changed

F02:
    v1 multipliers -> v2 multipliers
    changed

F03:
    floor -> ceiling
    changed

F04:
    multiple of 5 -> multiple of 10
    changed
```

Any source-defined unchanged formula components should be recorded as retained obligations.

---

## 4. Preserve the semantic task and output contract

The source task asks the agent to compute a service fee from:

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
  "fee": 0,
  "anchor_id": "P00i"
}
```

Keep this interface stable.

The instruction must not reveal:

```text
second-highest
current multiplier table
ceil-to-10
changed cap/order
```

The task-level records alone should not be sufficient to recover the private formula.

---

## 5. Build stale and oracle skills

Create:

```text
skill_v1.md
skill_v2_oracle.md
```

`skill_v1.md` contains the complete source `v1` formula.

`skill_v2_oracle.md` contains the complete source `v2` formula.

Adaptive methods receive the stale skill only.

Never expose:

```text
formula_v2.json
skill_v2_oracle.md
private obligation annotations
```

to the learner.

---

## 6. B6.2 evidence contract

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
    "D2": "Successful post-drift discount-calculation trajectories are supplied once during adaptation. Each trajectory explicitly states one correct v2 formula rule and demonstrates it on one successful invoice.",
    "D3": null
  }
}
```

For B6.2, make D2 deliberately **maximally revealing**.

Each trajectory should contain:

```text
invoice / records
+
accepted answer
+
one explicit statement of exactly one correct current formula rule
```

Use one trajectory per atomic post-drift formula rule or parameter.

Do not provide a separate all-rules-at-once D1 changelog. Do not provide D3 probes. The explicit rule statement belongs inside the successful trajectory.

## 7. Inspect and reuse existing worked examples carefully

Inspect `worked_examples.json` from the early `v2` source instances.

For each example:

1. verify its accepted answer under the actual v2 grader;
2. determine which one atomic formula rule it can cleanly demonstrate;
3. attach an explicit statement of that rule;
4. avoid using the same trajectory to state several rules;
5. reject any example overlapping the evaluation pool.

If the existing worked examples do not cover every current v2 formula rule, generate additional evidence-only invoices.

The final D2 set should favor **clarity and full rule coverage** over minimality.

## 8. Generate an evidence-only invoice pool

Create:

```text
evidence/evidence_candidates.jsonl
```

Generate many valid source-schema invoices with controlled variation over:

```text
number of items
item prices
price ordering
price ties
tier
fields used by any source-defined cap/order terms
```

For every candidate, privately compute:

```text
answer_v1
answer_v2
obligation_support
hypotheses eliminated by observing answer_v2
```

Evidence candidate IDs must use a namespace disjoint from evaluation:

```text
B6.2-evidence-001
...
```

---

## 9. Build a minimal discriminating D2 invoice set

Do not optimize for the smallest implicit evidence set.

Instead, enumerate the exact current v2 formula into atomic rules and create one maximally revealing successful trajectory for each.

At minimum, the catalog guarantees these rule groups:

```text
D2-anchor:
    current anchor-selection rule

D2-round-direction:
    current rounding direction

D2-round-quantum:
    current rounding quantum

D2-tier-*:
    one trajectory per current tier multiplier or multiplier rule
```

If executable source truth contains additional formula components such as a cap or operation-order rule, create one trajectory for each of those too.

### Anchor-selection trajectory

Construct an invoice with sufficiently distinct prices that the anchor is unambiguous.

Explicitly state the verified current rule, expected from the catalog to be:

```text
Current rule: the anchor item is the second-highest-priced item.
```

### Tier-multiplier trajectories

For every tier-specific multiplier or multiplier rule stored in the v2 skill, construct a successful invoice that uses it and explicitly state:

```text
Current rule: for tier <TIER>, use multiplier <VALUE>.
```

Do not invent `<VALUE>`; extract it from source truth.

### Rounding-direction trajectory

Use an invoice whose pre-rounding fee makes the direction observable.

Explicitly state:

```text
Current rule: round the computed fee upward.
```

### Rounding-quantum trajectory

Use an invoice near a rounding boundary.

Explicitly state:

```text
Current rule: round the fee to the next multiple of 10.
```

### Additional source-defined rules

For every other atomic formula component present in executable truth:

```text
one successful trajectory
+
one explicit rule statement
```

The solver should be able to reconstruct the complete v2 formula directly from the D2 trajectory set.

## 10. D2 success trajectory format

Create:

```text
evidence/d2_success_trajectories.jsonl
```

Each learner-visible record explicitly reveals one formula rule.

Recommended schema:

```json
{
  "evidence_id": "B6.2-D2-anchor",
  "regime": "v2",
  "rule_id": "anchor_selector",
  "revealed_rule": "The anchor item is the second-highest-priced item.",
  "instruction": "Compute the service fee and report the anchor item.",
  "records": [
    {"id": "P001", "price": 10, "tier": "example"},
    {"id": "P002", "price": 20, "tier": "example"},
    {"id": "P003", "price": 30, "tier": "example"},
    {"id": "P004", "price": 40, "tier": "example"}
  ],
  "accepted_answer": {
    "fee": 0,
    "anchor_id": "P003"
  },
  "verification": {
    "passed": true
  }
}
```

The numeric fee above is schematic. The generator must replace it with the true v2 result from executable source truth and the real grader.

The contract is:

```text
one trajectory
=
one explicit formula rule
+
one successful concrete invoice
```

For B6.2, `rule_id` and `revealed_rule` are intentionally learner-visible. Private generation metadata and oracle intermediates remain in:

```text
evidence/d2_manifest_private.json
```

## 11. Generate trajectories from the actual v2 grader

Pipeline:

```text
evidence-only invoice
        +
formula_v2 oracle
        |
        v
produce fee + anchor_id
        |
        v
write /root/answer.json
        |
        v
run source tests
        |
        v
pass
        |
        v
serialize sanitized D2 trajectory
```

Do not hand-enter an accepted fee.

If agent logs are used, do not expose chain-of-thought. Each sanitized trajectory must retain or add its single explicit `revealed_rule` statement. Do not state unrelated formula rules in the same trajectory.

---

## 12. Generate the 19 evaluation siblings

Create:

```text
siblings.json
```

with:

```text
8 affected
4 unchanged-retention
4 boundary/open-set
3 matched-null
= 19 total
```

Recommended private schema:

```json
{
  "id": "B6.2-aff-001",
  "slice": "affected",
  "regime": "v2",
  "obligation_support": ["F01", "F03"],
  "source_family": "discount-calculation"
}
```

---

## 13. Define affectedness by paired formula compilation

For each candidate invoice:

```python
answer_v1 = solve(records, formula_v1)
answer_v2 = solve(records, formula_v2)
```

Mark it affected iff either graded output changes:

```text
fee
anchor_id
```

A change in an internal intermediate value that leaves both graded fields identical does not make the sibling affected for primary correctness.

Track such cases separately if useful for diagnostics.

---

## 14. Build the 8 affected siblings

Cover changed formula obligations independently and jointly.

Recommended sub-slices:

```text
anchor-only decisive
multiplier-only decisive
rounding-only decisive
anchor + multiplier
anchor + rounding
multiplier + rounding
full interaction
cap/order decisive, if present
```

### Anchor-selection siblings

Use at least four distinct prices where possible so:

```text
second-lowest != second-highest
```

and the expected `anchor_id` changes.

### Multiplier siblings

Control anchor selection while varying tier.

Ensure the changed multiplier alters the final fee after rounding.

### Rounding siblings

Choose pre-rounding amounts near boundaries that distinguish the v1 and v2 rounding rules.

### Interaction siblings

Create cases where a solver must correctly recover:

```text
anchor
+
multiplier
+
rounding
```

to obtain the final fee.

---

## 15. Build the 4 unchanged-retention siblings

Search for valid invoices satisfying:

```text
answer_v1 == answer_v2
```

despite the formula drift.

Possible sources include:

```text
cases where second-lowest and second-highest are the same item
cases where different intermediate calculations happen to round to the same final fee
tiers whose relevant source parameters are retained
source-defined cap saturation that equalizes outputs, if such a cap exists
```

Do not rely on intuition.

Generate and compile until exact output equality is verified.

---

## 16. Build the 4 boundary/open-set siblings

Prefer source-valid numeric boundaries:

```text
price ties
near-price ties around the anchor position
minimum valid item count
exact rounding boundaries
one unit below a rounding boundary
one unit above a rounding boundary
tier boundary values
cap boundary values, if present
```

Only include malformed/missing-field tasks if the existing source family defines expected behavior for them.

The source grader remains authoritative.

---

## 17. Build the 3 matched-null siblings

Matched-null perturbations should not alter the formula or expected answer.

Examples:

```text
permute item order
rename item IDs consistently
change irrelevant metadata
reorder JSON keys
change a non-anchor item while preserving order statistics and final fee
instruction paraphrase
```

Compile before and after the null perturbation and require identical graded outputs.

These cases detect spurious skill rewrites caused by surface changes.

---

## 18. Compile all gold outputs automatically

Create:

```text
compile_b6_2.py
```

Inputs:

```text
formula_v1.json
formula_v2.json
siblings.json
```

Outputs:

```text
gold_v1.jsonl
gold_v2.jsonl
sibling_summary.json
```

For each sibling record privately:

```text
v1 anchor
v2 anchor
v1 raw fee
v2 raw fee
v1 final fee
v2 final fee
decisive obligations
affected?
```

Keep intermediate values private from the learner.

---

## 19. Deliver D2 once during adaptation

Recommended episode:

```text
stale skill_v1.md
        +
d2_success_trajectories.jsonl
        |
        v
adapt / rewrite skill
        |
        v
evaluate on held-out v2 siblings
```

Do not prepend all worked examples to each evaluation invoice.

This should measure persistent skill adaptation rather than in-context copying.

---

## 20. Construction controls

Run:

```text
zero_shot
static_v1
simple_D2_update
oracle_v2
```

Conditions:

```text
zero_shot:
    no skill, no D2

static_v1:
    stale v1 formula, no D2

simple_D2_update:
    stale v1 formula + D2 examples

oracle_v2:
    current v2 skill, no adaptation needed
```

Use these to validate that:

```text
the drift matters
the D2 evidence is sufficient
the evaluation pool is solvable
```

---

## 21. D2 identifiability validation

Create:

```text
validation/validate_evidence_rule_coverage.py
```

Compare the learner-visible D2 trajectories against private `formula_v2.json`.

Require:

```text
every atomic current v2 rule is explicitly stated in at least one trajectory
each trajectory states exactly one rule
the stated rule matches executable source truth
the concrete invoice actually exercises that rule
the accepted answer passes the actual v2 grader
```

At minimum verify coverage for:

```text
anchor selector
every tier multiplier / multiplier rule
rounding direction
rounding quantum
```

Also verify any source-defined cap, operation-order rule, or other coefficient if present.

Fail benchmark construction if any current formula component remains unstated.

## 22. Anti-memorization validation

A D2-only benchmark is only useful if demonstrated invoices cannot simply be retrieved.

Require:

```text
evidence invoice hashes != evaluation invoice hashes
different item IDs
different price combinations
different item counts where possible
different tier combinations
```

Also include held-out combinations that were never demonstrated.

The skill must generalize structurally.

---

## 23. Recommended metrics

Primary:

```text
Q_after
fee correctness
anchor_id correctness
affected-slice Q
retention Q
boundary Q
matched-null Q
```

Drift metrics:

```text
G_Q^need
G_Q^stale
RR
```

Formula diagnostics:

```text
anchor-selector recovery
multiplier parameter error
rounding-rule recovery
operation-order recovery, if present
semantic transfer rate (STR)
collateral damage (CD)
```

Do not fabricate numeric results before execution.

---

## 24. Recommended package

```text
B6.2/
├── B6_2_discount_calculation_execution_plan.md
└── discount_calculation/
    ├── README.md
    ├── extract_source_formula.py
    ├── formula_v1.json
    ├── formula_v2.json
    ├── drift_spec.json
    ├── skill_v1.md
    ├── skill_v2_oracle.md
    ├── generate_b6_2.py
    ├── compile_b6_2.py
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
        ├── validate_evidence_rule_coverage.py
        ├── validate_evidence_disjointness.py
        ├── validate_sibling_slices.py
        └── construction_report.json
```

---

## 25. Suggested implementation order

1. Locate the existing `discount-calculation` source rule and grader.
2. Extract exact v1/v2 formula objects, including all multiplier values.
3. Confirm whether cap/order terms actually exist in the source.
4. Replay all original 16 instances and reproduce their gold outputs.
5. Normalize the formula into changed/retained obligations.
6. Build a large invoice sibling generator.
7. Generate evidence-only candidate invoices.
8. Search for a minimal discriminating D2 set.
9. Verify all D2 examples with the source v2 grader.
10. Write learner-visible `d2_success_trajectories.jsonl`.
11. Generate the 19 held-out evaluation siblings.
12. Enforce 8/4/4/3 slice counts.
13. Compile paired v1/v2 gold outputs.
14. Validate D2/evaluation disjointness.
15. Validate explicit D2 rule coverage.
16. Run zero-shot/static/simple-D2/oracle construction controls.
17. Only then run full adaptive-skill baselines.

---

## 26. Acceptance checklist

- [ ] no new pricing formula was invented;
- [ ] exact source v1/v2 rules were extracted;
- [ ] exact source tier multipliers were recovered from executable truth;
- [ ] any cap/order terms are included only if they exist in the source family;
- [ ] D1 = 0%;
- [ ] D2 = 100%;
- [ ] D3 = 0%;
- [ ] D2 consists of successful v2 invoice precedents;
- [ ] every D2 trajectory passes the actual v2 grader;
- [ ] each learner-visible D2 trajectory explicitly states exactly one correct current formula rule;
- [ ] every current v2 formula rule/parameter is explicitly covered;
- [ ] each concrete invoice genuinely exercises the rule stated in its trajectory;
- [ ] evidence invoices are disjoint from evaluation invoices;
- [ ] solver starts from stale v1 skill;
- [ ] exactly 19 evaluation siblings are generated;
- [ ] slice counts are 8/4/4/3;
- [ ] affectedness is computed from v1/v2 graded outputs;
- [ ] fresh invoices test structural transfer rather than memorization;
- [ ] oracle solves all valid siblings;
- [ ] empirical results remain unset until execution.

---

## 27. Minimal conceptual summary

```text
existing discount-calculation family

v1 hidden formula
       |
       | abrupt source-defined drift
       v
v2 hidden formula
       |
       +---- evidence-only v2 invoices
       |            |
       |            v
       |    successful invoice -> answer
       |            trajectories
       |
stale v1 skill + D2 100%
             |
             v
store the explicitly revealed current semantic formula
             |
             v
19 fresh held-out invoices
             |
             v
measure application of revealed formula rules
not invoice memorization
```
