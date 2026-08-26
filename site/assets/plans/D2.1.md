# D2.1 — Updated Design-Level Execution Plan (19 Siblings)

## Goal

Extend the existing OSWorld-V2 `task_052` prototype into a **19-task pilot family** while preserving the original D2.1 construction:

- skill family: navigation / menu-tree strategy
- physical drift: `path_permute + shortcut_add`
- topology: replacement + improvement
- schedule: abrupt
- evidence: **D1 = 30%, D2 = 0%, D3 = 70%**
- substrate: TravelHub / OSWorld-V2 `task_052`
- semantic invariant: same hotel/room goal and same terminal task meaning

D2.1 and D2.2 must share the same task pool, `r-` graph, `r+` graph, graders, and cost model. Only evidence exposure differs.

### Strict D1/D3 boundary

D1 is **coarse declaration/localization only**. It may tell the learner that the hotel-detail navigation portion of its stored skill may be stale, but it must reveal **no executable graph structure**.

```text
D1 may answer:    Which broad skill region may be stale?
D1 may NOT answer: Which edge changed? Which node was added?
                   What route replaces the old one?
                   What shortcut exists? What route is optimal?
```

All exact structural recovery belongs to D3. Thus:

```text
D2.1: D1 tells WHERE to investigate; D3 tells WHAT changed.
D2.2: D3 must reveal both WHERE and WHAT changed.
```

---

## 1. Create the family directory

```text
drift_benchmark/D2.1/task_052_family/
├── README.md
├── state_catalog.json
├── regime_r_minus.json
├── regime_r_plus.json
├── regime_null.json
├── skill_r_minus.md
├── skill_r_plus_oracle.md
├── d1_notice.md
├── d3_evidence.jsonl
├── evidence_allocation.json
├── siblings.jsonl
├── sibling_summary.json
├── grader_spec.json
└── validation/
    ├── validate_siblings.py
    ├── validate_graph_coupling.py
    ├── validate_d1_nonleakage.py
    └── construction_report.json
```

---

## 2. Define the abstract state catalog

Use design-level states:

```text
S0    = TravelHub entry, ad visible
S1    = main page, ad closed
SH    = Hotels hub
S2    = Le Meurice detail page
S2A   = amenities view
S2R   = room-selection view
S3D   = Deluxe Suite selected
S3P   = Prestige Room selected
S4    = checkout / personal-information page
SFAV  = hotel saved/favorited
SHELP = TravelHub help
SACCT = account/preferences
```

These are benchmark abstractions, not claims about execution-observed OSWorld screens.

---

## 3. Define `r-`

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

Unit proxy cost: `1` per visible UI transition.

---

## 4. Define the shared `r+` drift

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

Everything downstream from `S2` stays unchanged.

This gives:

```text
replacement: direct hotel route is replaced
improvement: Deluxe shortcut lowers route cost
```

---

## 5. Define stale and oracle skills

### `skill_r_minus.md`

```text
Main → Le Meurice → Rooms → requested room → Checkout
```

### `skill_r_plus_oracle.md`

For Deluxe:

```text
Main → Featured Deluxe → Checkout
```

Fallback / non-Deluxe:

```text
Main → Hotels → Le Meurice → Rooms → requested room → Checkout
```

Keep the stale skill unchanged at the start of `r+`.

---

## 6. Build a 19-task pilot pool

Use:

```text
8 affected
5 unchanged-retention
4 boundary/open-set
2 matched-null
= 19 total
```

Later scale to:

```text
48 total
19 affected
14 unchanged-retention
10 boundary/open-set
5 matched-null
```

---

## 7. Shared sibling schema

Each task in `siblings.jsonl` should include:

```json
{
  "id": "D2-aff-001",
  "slice": "affected",
  "source_task": "OSWorld-V2 task_052",
  "initial_state": "S0",
  "instruction": "...",
  "semantic_goal": {"target_state": "S4"},
  "obligation_support": ["O1", "O4"],
  "grader": {"type": "semantic_state"}
}
```

Use the same logical IDs in D2.1 and D2.2.

---

## 8. Affected siblings (8)

### D2-aff-001 — original full reservation

- initial: `S0`
- instruction: reserve the Deluxe Suite at Le Meurice and stop at personal information
- goal: `S4`
- tests: replacement + shortcut

### D2-aff-002 — Deluxe reservation from main page

- initial: `S1`
- same semantic reservation goal
- goal: `S4`
- tests shortcut directly

### D2-aff-003 — open hotel details

- initial: `S1`
- instruction: open Le Meurice details
- goal: `S2`
- tests replacement only

### D2-aff-004 — view amenities

- initial: `S1`
- instruction: show Le Meurice amenities
- goal: `S2A`
- tests repaired prefix + unchanged downstream edge

### D2-aff-005 — open room list

- initial: `S1`
- instruction: show available rooms at Le Meurice
- goal: `S2R`

### D2-aff-006 — reserve Prestige Room

- initial: `S1`
- instruction: reserve Prestige Room and stop at personal information
- goal: `S4`
- no shortcut applies
- correct `r+`: `S1 → SH → S2 → S2R → S3P → S4`

### D2-aff-007 — save Le Meurice

- initial: `S1`
- instruction: save Le Meurice to favorites
- goal: `SFAV`

### D2-aff-008 — step-capped Deluxe reservation

- initial: `S1`
- instruction: reserve Deluxe Suite
- goal: `S4`
- step cap: `2`
- only `S1 → S3D → S4` satisfies the cap
- use for capped correctness / cost recovery

---

## 9. Unchanged-retention siblings (5)

### D2-ret-001
- initial `S2`
- show amenities
- route `S2 → S2A`

### D2-ret-002
- initial `S2`
- open rooms
- route `S2 → S2R`

### D2-ret-003
- initial `S2R`
- select Deluxe and checkout
- route `S2R → S3D → S4`

### D2-ret-004
- initial `S2R`
- select Prestige and checkout
- route `S2R → S3P → S4`

### D2-ret-005
- initial `S1`
- open TravelHub help
- route `S1 → SHELP`

These tasks should remain valid without any graph repair.

---

## 10. Boundary/open-set siblings (4)

### D2-open-001 — unknown hotel
Instruction: open `Hotel Imaginaire Paris`.
Expected: not-found / abstain.

### D2-open-002 — unavailable room
Initial: `S2R`.
Instruction: select `Presidential Penthouse`.
Expected: unavailable / abstain.

### D2-open-003 — ambiguous Deluxe
Initial: `S1`.
Instruction: reserve a Deluxe Suite.
Expected: request hotel clarification / abstain.
Do not assume Le Meurice because a Featured Deluxe shortcut exists.

### D2-open-004 — prohibited hidden route
Instruction: jump directly to hidden checkout.
Expected: do not use hidden/direct navigation; preserve visible-interface restriction.

---

## 11. Matched-null siblings (2)

### D2-null-001 — cosmetic label change
Visible label changes `Hotels → Stays`, but the underlying action/transition is unchanged.

Expected: no persistent structural graph update.

### D2-null-002 — visual reorder
Featured card moves visually, but the state/action/next-state relation is unchanged.

Expected: no graph or cost-model rewrite.

---

## 12. Define drift obligations with localization separated from structure

Use:

```text
O1 = detect/localize that hotel-detail navigation may be stale
O2 = discover that the old direct hotel-detail action is invalid
O3 = discover the new intermediate navigation action/state
O4 = discover the transition from that intermediate state to Le Meurice
O5 = discover the Deluxe shortcut
O6 = determine shortcut specificity
O7 = determine shortcut cost advantage
```

Evidence responsibility is intentionally separated:

```text
D1: O1 only
D3: O2,O3,O4,O5,O6,O7
```

Suggested evaluation-sibling support:

```text
aff-001: O2,O3,O4,O5,O7
aff-002: O5,O7
aff-003: O2,O3,O4
aff-004: O2,O3,O4
aff-005: O2,O3,O4
aff-006: O2,O3,O4,O6
aff-007: O2,O3,O4
aff-008: O5,O7
```

`O1` belongs to the adaptation episode rather than to a particular held-out task path.

---

## 13. D2.1 D1 notice — strict non-leaking version

Create `d1_notice.md` with exactly this level of specificity:

```markdown
# TravelHub UI Update Notice

Hotel-detail navigation has recently been reorganized.

Existing hotel listings, room availability, and booking goals remain unchanged.

Previously stored navigation routes to hotel details may no longer be current.
```

This notice is visible to the learner **once per drift/adaptation episode**, not repeated inside every sibling prompt.

It tells the learner only:

```text
broad stale region = hotel-detail navigation
```

It must not reveal or strongly imply any changed graph structure.

### Forbidden D1 content

Do not mention:

```text
Hotels
Stays
Featured
Featured Deluxe
new section
intermediate page
shortcut
direct link removed
open Hotels
Hotels → Le Meurice
Main → Hotels
Main → Featured Deluxe
replacement route
faster route
cheaper route
```

Also avoid semantic equivalents such as:

```text
"hotel details are now under another section"
"there is a new top-level hotel menu"
"some rooms can now be accessed directly"
```

The rule is:

```text
D1 may localize.
D1 may not identify.
```

---

## 14. Add a D1 non-leakage validator

Create:

```text
validation/validate_d1_nonleakage.py
```

At minimum, reject obvious forbidden strings:

```python
from pathlib import Path

FORBIDDEN = [
    "hotels",
    "featured",
    "shortcut",
    "open hotels",
    "new section",
    "direct link removed",
    "faster route",
    "cheaper route",
]

text = Path("d1_notice.md").read_text().lower()

for term in FORBIDDEN:
    assert term not in text, f"D1 leakage: {term}"
```

String matching is only a first check. Manually inspect semantic leakage as well.

Acceptance condition:

```text
D1 identifies the broad stale skill region
but exposes zero executable graph edges/nodes/shortcuts.
```

---

## 15. D2.1 D3 evidence

All exact executable structure must now come from D3.

Examples:

```json
{"state":"S1","action":"open_Le_Meurice","next_state":null,"cost":1,"outcome":"action_unavailable"}
```

This identifies that the stale direct edge is invalid.

Then:

```json
{"state":"S1","action":"open_Hotels","next_state":"SH","cost":1,"outcome":"valid_transition"}
```

```json
{"state":"SH","action":"open_Le_Meurice","next_state":"S2","cost":1,"outcome":"valid_transition"}
```

```json
{"state":"S1","action":"featured_Deluxe_Suite","next_state":"S3D","cost":1,"outcome":"valid_transition"}
```

D3 must also establish:

```text
shortcut specificity
route-cost advantage
```

Evidence-only scenarios must be disjoint from evaluation sibling IDs.

---

## 16. Evidence allocation

```json
{
  "D1": 30,
  "D2": 0,
  "D3": 70,
  "obligations": {
    "O1": "D1",
    "O2": "D3",
    "O3": "D3",
    "O4": "D3",
    "O5": "D3",
    "O6": "D3",
    "O7": "D3"
  }
}
```

Treat 30/70 as the construction contract, not a measured information-theoretic quantity.

The key interpretation is:

```text
D2.1: D1 tells WHERE; D3 tells WHAT.
D2.2: D3 tells both WHERE and WHAT.
```

---

## 17. Grading

Primary correctness should be semantic/state based.

Do not make exact path match the primary metric.

Examples:

- reservation tasks: correct hotel + room + checkout/personal-info state
- details: `S2`
- amenities: `S2A`
- rooms: `S2R`
- favorite: `SFAV`
- open-set: correct abstain/not-found/clarification
- matched-null: no spurious persistent update

---

## 18. Baseline result schema

Save at least:

```json
{
  "family": "D2.1",
  "task_id": "D2-aff-001",
  "method": "static_r_minus",
  "slice": "affected",
  "success": false,
  "semantic_score": 0.0,
  "actions": [],
  "task_cost": 0,
  "invalid_actions": 0,
  "adaptation_cost": 0,
  "updated_skill": null
}
```

Raw quantities:

```text
Q
task cost
invalid actions
adaptation cost
slice
```

---

## 19. Acceptance checks

Before scaling:

- all 19 siblings compile;
- affected tasks touch at least one changed obligation;
- retention tasks avoid changed prefix edges by construction;
- open-set tasks have no accidental valid shortcut;
- null variants have unchanged semantic transition graphs;
- oracle succeeds;
- stale skill has at least one correctness failure;
- stale skill has at least one correct-but-more-expensive case;
- D1 contains no changed node names;
- D1 contains no changed action names;
- D1 contains no removed-edge description;
- D1 contains no shortcut hint;
- D1 contains no route-cost hint;
- D1 only identifies hotel-detail navigation as potentially stale;
- all exact structural recovery comes from D3;
- D3 evidence IDs are disjoint from evaluation IDs.

---

## 20. Scaling rule

Scale both D2.1 and D2.2 together to:

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

Do not create 48 near-duplicate paraphrases.

---

## 21. Conceptual summary

```text
             SAME HIDDEN PHYSICAL DRIFT

r-                                      r+
old direct route                       replacement route
                                       + hidden shortcut


                    D2.1

D1 notice:
"hotel-detail navigation may be stale"
              |
              |  reveals NO graph edge
              |  reveals NO new node
              |  reveals NO shortcut
              |  reveals NO optimal route
              v
      localize investigation
              |
              v
          D3 interaction
              |
              +-- stale edge fails
              +-- discover new intermediate action
              +-- discover next transition
              +-- discover shortcut
              +-- measure route cost
              |
              v
       reconstruct current graph
              |
              v
        update persistent skill
              |
              v
      evaluate on 19 siblings


Comparison:

D2.1 = D1 tells WHERE + D3 tells WHAT
D2.2 = D3 tells WHERE + WHAT
```
