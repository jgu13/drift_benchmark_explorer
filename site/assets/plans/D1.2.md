# D1.2 Design-Level Drift Construction Plan

## Objective

Construct one **design-level D1.2 drift example** using **OSWorld-V2 `task_041`** as the source substrate.

D1.2 tests **repository navigation drift**:

```text
persistent skill:
semantic target
      ↓
current repository path
      +
ordered search fallback
```

The physical drift is:

```text
relocate + split_merge
```

The semantic information and answers remain unchanged, but repository locations change.

The learner receives:

```text
D1 = 0%
D2 = 0%
D3 = 100%
```

Therefore:

- Do **not** provide a refactor note.
- Do **not** provide demonstrations of the new mappings.
- New locations must be discoverable only from simulated search/file-access outcomes.
- This is a **static construction prototype only**. Do not execute OSWorld and do not claim measured `δ_C`, `CRR`, `BE`, or identification budgets.

---

## Step 1 — Inspect the source OSWorld task

Read:

```bash
sed -n '1,260p' evaluation_examples/task_class/task_041.py
```

Extract only:

1. The original instruction.
2. What repository/template is involved.
3. The semantic outcome requested.
4. Any repository/file concepts explicitly mentioned.
5. The evaluator's final semantic requirements, if available.

Do not modify `task_041.py`.

Create:

```text
drift_benchmark/D1.2/repository_navigation/
```

with:

```text
repository_navigation/
├── source_task.md
├── regime_r_minus.json
├── regime_r_plus.json
├── skill_r_minus.md
├── skill_r_plus_oracle.md
├── siblings.json
├── d3_evidence.jsonl
├── grader_spec.json
└── README.md
```

---

## Step 2 — Write `source_task.md`

Record that the sample is derived from OSWorld-V2 `task_041`.

Include the original OSWorld instruction verbatim.

Then add:

```markdown
## D1.2 abstraction

This construction does not drift the user's semantic goal.

Instead, it treats the repository underlying the task as a
versioned layout and introduces repository-path drift.

The same semantic targets exist in both regimes, but selected
targets move, split, or merge across files.
```

Do not claim that proposed paths are actual files in the original repository unless `task_041.py` explicitly establishes them.

Label synthetic paths as:

```text
design-level repository abstraction
```

---

## Step 3 — Define semantic targets first

Do **not** start by inventing paths.

First define approximately 8 semantic repository targets, `T1, ..., T8`.

For example:

```text
T1 = paper/site metadata
T2 = author information
T3 = abstract/overview content
T4 = method section content
T5 = results section content
T6 = project links/resources
T7 = site styling/theme configuration
T8 = deployment configuration
```

Adjust these names after inspecting `task_041.py`.

The important principle is:

```text
semantic target != path
```

Example:

```text
semantic target:
deployment configuration

path under r-:
deploy/pages.yml
```

The semantic target persists even if its path changes.

---

## Step 4 — Create the baseline regime `r-`

Create `regime_r_minus.json`.

Use a simple design-level repository map such as:

```json
{
  "regime": "r_minus",
  "source_task": "OSWorld-V2 task_041",
  "layout_type": "design-level abstraction",

  "semantic_targets": {
    "paper_metadata": "config/site.yml",
    "author_information": "config/site.yml",
    "overview_content": "content/overview.md",
    "method_content": "content/method.md",
    "results_content": "content/results.md",
    "project_links": "content/resources.md",
    "site_style": "assets/theme.yml",
    "deployment_config": "deploy/pages.yml"
  }
}
```

The exact names may be changed, but keep the mapping simple and explicit.

---

## Step 5 — Define the baseline persistent skill `S-`

Create `skill_r_minus.md`.

It should contain a **semantic-target-to-path map plus an ordered fallback strategy**.

Example:

```markdown
# Repository Navigation Skill — r-

## Semantic map

- Paper metadata → `config/site.yml`
- Author information → `config/site.yml`
- Overview → `content/overview.md`
- Method → `content/method.md`
- Results → `content/results.md`
- Project links → `content/resources.md`
- Site style → `assets/theme.yml`
- Deployment configuration → `deploy/pages.yml`

## Retrieval policy

For a requested semantic target:

1. Try its stored current path directly.
2. If the path is unavailable or does not contain the target:
   - perform bounded filename/path search;
   - then perform bounded semantic/content search.
3. Open the best candidate.
4. Verify that the retrieved content satisfies the requested semantic target.
5. Stop once verified.
```

This is the persistent competence being tested.

---

## Step 6 — Create `r+` using `relocate + split_merge`

For the supervisor-scale sample, use approximately **25% changed target access mass**.

With 8 semantic targets, change two substantial mappings.

### A. Relocate

Example:

```text
results_content

r-:
content/results.md

r+:
sections/experiments/results.md
```

### B. Split / merge

Example split:

```text
r-:

config/site.yml
    ├── paper metadata
    └── author information
```

becomes:

```text
r+:

config/site.yml
    └── paper metadata

config/authors.yml
    └── author information
```

The point is that **repository organization changes but information does not**.

---

## Step 7 — Write `regime_r_plus.json`

Example:

```json
{
  "regime": "r_plus",
  "source_task": "OSWorld-V2 task_041",
  "layout_type": "design-level abstraction",

  "semantic_targets": {
    "paper_metadata": "config/site.yml",
    "author_information": "config/authors.yml",
    "overview_content": "content/overview.md",
    "method_content": "content/method.md",
    "results_content": "sections/experiments/results.md",
    "project_links": "content/resources.md",
    "site_style": "assets/theme.yml",
    "deployment_config": "deploy/pages.yml"
  },

  "drift": {
    "operator": [
      "relocate",
      "split_merge"
    ],

    "topology": "replacement",

    "changed_targets": [
      "author_information",
      "results_content"
    ],

    "changes": [
      {
        "target": "results_content",
        "type": "relocate",
        "old_path": "content/results.md",
        "new_path": "sections/experiments/results.md"
      },
      {
        "target": "author_information",
        "type": "split",
        "old_path": "config/site.yml",
        "new_path": "config/authors.yml"
      }
    ]
  }
}
```

---

## Step 8 — Do not change semantic gold

A sibling may ask:

```text
Where is the author information for the paper stored?
```

Under `r-`:

```text
config/site.yml
```

Under `r+`:

```text
config/authors.yml
```

But for a semantic question such as:

```text
Who are the listed authors?
```

the answer must remain identical.

Think of D1.2 as:

```text
content(r-) = content(r+)
location(r-) != location(r+)
```

---

## Step 9 — Keep `skill_r_minus.md` stale

After constructing `r+`, **do not edit the learner's skill**.

For example, it still says:

```text
Results → content/results.md
```

while the new environment is:

```text
Results → sections/experiments/results.md
```

Thus:

```text
Environment = r+
Skill       = S-
```

produces:

```text
try content/results.md
        ↓
path unavailable
        ↓
fallback search
        ↓
discover sections/experiments/results.md
        ↓
correct answer
```

This is the intended D1.2 failure mode:

> Correctness may survive, but repeated rediscovery becomes expensive.

---

## Step 10 — Create the oracle `S+`

Create `skill_r_plus_oracle.md`.

Copy the same structure as `skill_r_minus.md`, but update only changed mappings:

```markdown
# Repository Navigation Skill — r+

## Semantic map

- Paper metadata → `config/site.yml`
- Author information → `config/authors.yml`
- Overview → `content/overview.md`
- Method → `content/method.md`
- Results → `sections/experiments/results.md`
- Project links → `content/resources.md`
- Site style → `assets/theme.yml`
- Deployment configuration → `deploy/pages.yml`
```

Do **not** give this file to the learner.

It represents the oracle skill for `r+`.

---

## Step 11 — Construct D3-only evidence

This is the defining feature of D1.2.

There must be:

```text
NO refactor note
NO changelog
NO demonstration saying where the target moved
```

Instead create `d3_evidence.jsonl` containing **search/access observations**.

For the relocated results file:

```json
{
  "target": "results_content",
  "observation_type": "file_access",
  "action": "open(content/results.md)",
  "outcome": "path_not_found"
}
```

Then:

```json
{
  "target": "results_content",
  "observation_type": "search",
  "action": "search(repository, "results experiments accuracy")",
  "outcome": [
    "sections/experiments/results.md"
  ]
}
```

Then:

```json
{
  "target": "results_content",
  "observation_type": "file_access",
  "action": "open(sections/experiments/results.md)",
  "outcome": "verified_target_content"
}
```

For author information:

```json
{
  "target": "author_information",
  "observation_type": "file_access",
  "action": "open(config/site.yml)",
  "outcome": "paper metadata present; author information absent"
}
```

Then:

```json
{
  "target": "author_information",
  "observation_type": "search",
  "action": "search(repository, "authors affiliation")",
  "outcome": [
    "config/authors.yml"
  ]
}
```

These are **design-level simulated evidence atoms**.

Do not claim they were observed from OSWorld.

---

## Step 12 — Specify what the learner should infer

The intended learning path is:

```text
stale path map
      ↓
direct access failure
      ↓
bounded search
      ↓
successful new access
      ↓
semantic verification
      ↓
update path map
```

For example:

```text
results_content:
content/results.md
        ↓
sections/experiments/results.md
```

The learner should update only this mapping.

It should **not rewrite unrelated mappings**.

---

## Step 13 — Create sibling tasks

Create `siblings.json`.

For a supervisor-scale prototype, use **8–10 siblings**, not the full target volume yet.

Use four categories.

### A. Affected siblings

```json
{
  "id": "D1.2-aff-001",
  "semantic_target": "results_content",
  "question": "Retrieve the reported experimental results for the TypeSQL project.",
  "slice": "affected"
}
```

```json
{
  "id": "D1.2-aff-002",
  "semantic_target": "author_information",
  "question": "Retrieve the author information used by the project website.",
  "slice": "affected"
}
```

### B. Unchanged-retention siblings

```json
{
  "id": "D1.2-ret-001",
  "semantic_target": "method_content",
  "question": "Retrieve the method description.",
  "slice": "unchanged"
}
```

Its path remains:

```text
content/method.md
```

under both regimes.

### C. Boundary/open-set siblings

```json
{
  "id": "D1.2-open-001",
  "semantic_target": "supplementary_video",
  "question": "Locate the supplementary video configuration.",
  "slice": "boundary"
}
```

Expected behavior:

```text
bounded search
→ verify absence
→ abstain / report not found
```

rather than hallucinating a path.

### D. Matched null

Change surface naming or formatting without changing semantic location.

The learner should **not update its map**.

---

## Step 14 — Add an abstract cost model

Because this is not executed, do not report real latency or real action counts.

Define a simple **design cost model** in `grader_spec.json`:

```json
{
  "cost_model": {
    "type": "design_proxy",
    "direct_path_access": 1,
    "failed_path_access": 1,
    "repository_search": 1,
    "verification_read": 1
  }
}
```

Illustration:

### Oracle `S+`

```text
open(new_path)
→ verify

design cost ≈ 2
```

### Stale `S-`

```text
open(old_path)       1
search               1
open(new_path)       1
verify               1
                   ----
design cost ≈ 4
```

These are **abstract design costs, not benchmark measurements**.

Do not calculate official `CRR`.

---

## Step 15 — Define the expected update

The learner should eventually produce something conceptually equivalent to:

```diff
- Results → content/results.md
+ Results → sections/experiments/results.md

- Author information → config/site.yml
+ Author information → config/authors.yml
```

Everything else remains unchanged.

---

## Step 16 — Write `README.md`

The README should contain five sections.

### 1. Source

```text
OSWorld-V2 task_041
```

Note that the repository layout is a design abstraction.

### 2. Physical drift

```text
operator: relocate + split_merge
topology: replacement
schedule: abrupt
sample scope: ~25%
```

### 3. Evidence

```text
D1: 0%
D2: 0%
D3: 100%
```

Explain:

> The refactor note is withheld. New target locations are identifiable only through file-access failures, repository search, successful access, and semantic verification.

### 4. Before/after table

| Semantic target | `r-` | `r+` | Status |
|---|---|---|---|
| Paper metadata | `config/site.yml` | `config/site.yml` | unchanged |
| Author info | `config/site.yml` | `config/authors.yml` | split |
| Overview | `content/overview.md` | same | unchanged |
| Method | `content/method.md` | same | unchanged |
| Results | `content/results.md` | `sections/experiments/results.md` | relocated |
| Resources | `content/resources.md` | same | unchanged |
| Style | `assets/theme.yml` | same | unchanged |
| Deployment | `deploy/pages.yml` | same | unchanged |

### 5. Expected causal behavior

```text
r- + S-
    → direct retrieval

r+ + S-
    → stale path
    → search
    → recovery
    → higher cost

r+ + updated skill
    → direct retrieval

r+ + oracle S+
    → direct retrieval
```

---

## Step 17 — State limitations explicitly

Include:

> This package is a design-level prototype. The OSWorld source task supplies the repository-oriented application context, but the paired repository layouts and D3 access/search observations are counterfactual constructions and have not yet been executed. Consequently, stale-skill damage, normalized execution cost, CRR, break-even horizon, and identification budget are intentionally unset.

---

## Expected Final Output

```text
drift_benchmark/
└── D1.2/
    └── repository_navigation/
        ├── source_task.md
        ├── regime_r_minus.json
        ├── regime_r_plus.json
        ├── skill_r_minus.md
        ├── skill_r_plus_oracle.md
        ├── siblings.json
        ├── d3_evidence.jsonl
        ├── grader_spec.json
        └── README.md
```

## Conceptual Summary

```text
D1.2 — repository navigation drift

                    r-
Results ───────────────► content/results.md
Author info ───────────► config/site.yml

                 DRIFT
         relocate + split

                    r+
Results ───────────────► sections/experiments/results.md
Author info ───────────► config/authors.yml


Old skill S-
     │
     ├─ tries old path
     │       ↓
     │    failure
     │       ↓
     └─ search → new path → correct answer
                      ↑
                     D3

Updated skill
     │
     └─ direct new path → correct answer
```

This is the D1.2 design analogue of the C1.2 `START → X7` sample and the D2.2 path-permutation sample.
