# Drift Benchmark Web — Execution Plan

## 0. Objective

Build a local, static HTTP web interface for visually browsing and inspecting the drift benchmark families that have been constructed so far.

The web interface has two primary purposes:

1. **Presentation:** provide a compact visual overview of a growing number of drift tasks.
2. **Inspection:** allow co-authors to open each family, inspect its sibling tasks, understand the evidence regime, and read the complete execution plan used to construct the family.

The implementation should be driven by the benchmark files already on disk rather than by manually duplicating benchmark content into frontend code.

The first supported families should include:

```text
C1.1
C1.2
C2.1
C2.2
C3.1

and, when the corresponding local directory is provided:

D1.2
D2.1
D2.2
```

The web app should work with:

```bash
python -m http.server 8080 --directory drift_web/site
```

and then be visible at:

```text
http://localhost:8080
```

No external web service or database is required.

---

## 1. Core design principle

Use a two-stage architecture:

```text
benchmark files on disk
        |
        v
Python normalization/build script
        |
        v
benchmark_index.json + copied plan/evidence assets
        |
        v
static HTML/CSS/JavaScript web interface
```

The frontend must **not** understand every benchmark family's raw file format.

Instead, the Python build step converts heterogeneous family directories into one normalized schema.

This keeps the website stable as the benchmark grows.

---

## 2. Recommended repository layout

Create:

```text
drift_web/
├── README.md
├── build_site.py
├── parsers.py
├── family_overrides.json
├── tests/
│   └── test_build.py
└── site/
    ├── index.html
    ├── app.js
    ├── styles.css
    ├── data/
    │   └── benchmark_index.json
    └── assets/
        ├── plans/
        └── evidence/
```

Do not modify the benchmark source files merely to satisfy the website.

---

## 3. Example invocation

The build script should support one or more benchmark roots:

```bash
python drift_web/build_site.py \
  --root /path/to/C_drift_benchmark \
  --root /path/to/D_drift_benchmark
```

Then serve:

```bash
python -m http.server 8080 --directory drift_web/site
```

---

## 4. Family discovery

Recursively inspect each supplied benchmark root for directories matching:

```regex
^[CD][0-9]+\.[0-9]+$
```

Examples:

```text
C1.1
C1.2
C2.1
C2.2
C3.1
D1.2
D2.1
D2.2
```

Do not treat:

```text
gold_answer
validation
evidence
__pycache__
```

as families.

Sort family IDs naturally.

---

## 5. Execution-plan discovery

For every family directory, search for Markdown files matching, in priority order:

```text
*_execution_plan.md
*execution*plan*.md
*plan*.md
```

Examples:

```text
C1.1/C1_1_BFCL_execution_plan.md
C1.2/C1_2_BFCL_execution_plan.md
C2.1/C2_1_BFCL_execution_plan.md
C2.2/C2_2_BFCL_execution_plan.md
C3.1/C3_1_BFCL_execution_plan.md
D1.2/D1_2_design_level_drift_plan.md
D2.1/D2_1_design_level_drift_plan.md
D2.2/D2_2_design_level_drift_plan.md
```

Copy the selected plan to:

```text
site/assets/plans/<family_id>.md
```

The family page should render the full plan and provide a raw Markdown link.

---

## 6. Task/sibling discovery

Read sibling_summary.json and locate siblings tasks in one of the following names:

```text
siblings.json
siblings.jsonl
```

The parser must support:

```text
JSON list
JSON object containing `siblings`
JSONL, one task object per line
single-task JSON object
```

Never hardcode task counts in frontend code.

Compute:

```text
task_count = len(normalized_tasks)
```

at build time.

---

## 7. Task ID extraction

For each task, look for:

```text
id
task_id
instance_id
name
```

If none exists, generate a deterministic display ID:

```text
<family_id>_task_001
<family_id>_task_002
...
```

Generated display IDs must not be written back into benchmark source files.

---

## 8. Task slice extraction

Normalize fields such as:

```text
slice
category
task_category
affectedness
group
```

Known values include:

```text
affected
affected-new-edge
propagated-affected
affected-retired-edge
unchanged-retention
boundary-open-set
matched-null
```

Show the slice as a badge.

If no slice exists, use:

```text
unspecified
```

Do not infer a scientifically meaningful slice from wording alone.

---

## 9. One-sentence task description

The task list needs a concise description answering:

> What aspect of the task is being stressed by the drift?

Use this precedence:

### Priority 1 — explicit description

Look for:

```text
ui_description
description
drift_description
summary
```

### Priority 2 — deterministic family-specific template

Use `family_overrides.json` to map known task categories/obligations to one-sentence descriptions.

Example:

```text
Affected-new-edge: engine start must recover the newly required parking-brake prerequisite.
```

### Priority 3 — instruction fallback

Look for:

```text
instruction
prompt
user_prompt
question
```

Trim to roughly 120–160 characters.

Do not call an LLM at website runtime.

---

## 10. Normalized family schema

Generate:

```text
site/data/benchmark_index.json
```

with a schema like:

```json
{
  "families": [
    {
      "id": "C2.1",
      "title": "Precondition Graph",
      "platform": "BFCL",
      "mechanism": "Executable precondition graph",
      "drift_summary": "Engine-start prerequisites change by adding one required edge and retiring one stale edge.",
      "task_count": 16,
      "source_path": ".../C2.1",
      "plan": {
        "filename": "C2_1_BFCL_execution_plan.md",
        "asset_path": "assets/plans/C2.1.md"
      },
      "evidence": {
        "D1": {
          "percentage": 0,
          "present": false,
          "delivery": null,
          "files": []
        },
        "D2": {
          "percentage": 40,
          "present": true,
          "delivery": "Successful post-drift sibling trajectories are supplied during adaptation.",
          "files": ["evidence/d2_success_traces.jsonl"]
        },
        "D3": {
          "percentage": 60,
          "present": true,
          "delivery": "The agent observes violations and counterexamples through environment interaction.",
          "files": ["evidence/d3_counterexamples.jsonl"]
        }
      },
      "tasks": [
        {
          "id": "C2.1_vehicle_001",
          "slice": "affected-new-edge",
          "description": "Engine start must recover the newly required parking-brake prerequisite.",
          "source_file": "siblings.json"
        }
      ]
    }
  ]
}
```

---

## 11. Evidence percentages: source-of-truth order

The site must show exact D1/D2/D3 composition percentages.

Use this precedence:

### First choice

Read explicit evidence weights allocation under:

```text
evidence/evidence_allocation.json
```

---

## 13. Evidence-delivery descriptions

The site should explain **how each present evidence channel is delivered to the agent**.

### C1.1

**D2 — 50%**

```text
Successful post-drift transcripts are supplied as demonstration evidence during adaptation.
```

Typical file:

```text
device_enum/evidence/d2_success_transcripts.jsonl
```

**D3 — 50%**

```text
The agent uses safe probes and observes current environment responses to complete executable enum coverage.
```

Typical files:

```text
device_enum/evidence/d3_probe_interface.py
device_enum/evidence/d3_probe_log.jsonl
```

### C1.2

**D1 — 100%**

```text
The agent receives the stale skill plus an explicit changelog before adaptation. The changelog declares that the private start-engine token changed from START to X7.
```

Typical file:

```text
device_enum/changelog.md
```

Important:

```text
zero-shot does not receive the changelog
static_r_minus does not receive the changelog
d1_update receives the changelog
oracle already contains the r+ skill
```

### C2.1

**D2 — 40%**

```text
Successful post-drift sibling trajectories are supplied during adaptation as positive evidence of valid action ordering.
```

Typical file:

```text
precondition_graph/evidence/d2_success_traces.jsonl
```

**D3 — 60%**

```text
The agent observes violations and counterexamples from the current environment, including evidence for newly required and retired prerequisites.
```

Typical file:

```text
precondition_graph/evidence/d3_counterexamples.jsonl
```

### C2.2

**D3 — 100%**

```text
The revised precondition graph is discovered from environment interaction alone; no declaration or successful demonstration channel is provided.
```

Typical files:

```text
precondition_graph/evidence/d3_interaction.py
precondition_graph/evidence/interaction_log.jsonl
```

### C3.1

**D1 — 50%**

```text
A changelog localizes which CLI actions or flags have changed, without necessarily giving the exact replacement syntax.
```

Typical file:

```text
cli_semantics/evidence/d1_changelog.md
```

**D3 — 50%**

```text
Help output and safe command probes reveal executable replacement syntax and current command cost.
```

Typical files:

```text
cli_semantics/evidence/d3_help.jsonl
cli_semantics/evidence/d3_probe_log.jsonl
```

### D1.2

**D3 — 100%**

```text
The agent recovers current repository locations and navigation structure through environment/navigation interaction rather than a declared relocation map.
```

### D2.1

**D1 — 30%**

Use the strict D1 interpretation:

```text
The agent receives one TravelHub UI Update Notice during adaptation stating only that hotel-detail navigation has been reorganized and previously stored routes may be stale.
```

The site must explicitly state:

```text
D1 does NOT reveal the added intermediate state,
the removed graph edge,
the replacement route,
or the Featured Deluxe shortcut.
```

**D3 — 70%**

```text
The agent interacts with TravelHub to discover the removed stale route, the new intermediate navigation transition, the Featured Deluxe shortcut, and their consequences.
```

### D2.2

**D3 — 100%**

```text
The same physical TravelHub drift is used as D2.1, but no update notice is provided. The agent must both localize the stale region and reconstruct the changed navigation graph through interaction alone.
```

---

## 14. Global overview page

The default page should show a responsive grid of family cards.

Each card should include:

```text
Family ID
Family title / mechanism
one-sentence physical drift summary
task count
platform
D1/D2/D3 evidence composition
```

Example:

```text
┌────────────────────────────────────────┐
│ C2.1  Precondition Graph               │
│ BFCL                                   │
│                                        │
│ Add parking-brake prerequisite and     │
│ retire full-brake prerequisite.        │
│                                        │
│ 16 tasks                               │
│                                        │
│ D1  0%                                 │
│ D2 40%  ████████                       │
│ D3 60%  ████████████                   │
│                                        │
│ [Inspect family]                       │
└────────────────────────────────────────┘
```

---

## 15. Overview summary header

Show:

```text
Drift Benchmark Explorer
```

and computed summaries:

```text
number of families
total number of tasks
number of BFCL families
number of OSWorld families
last generated timestamp
```

---

## 16. Family detail routing

Use hash routing so the site works with a static HTTP server.

Examples:

```text
http://localhost:8080/#/family/C1.1
http://localhost:8080/#/family/C2.1
http://localhost:8080/#/family/D2.1
```

---

## 17. Family detail section A — summary

Show:

```text
Family ID
Family title
platform
task count
one-sentence physical drift
build/status label if known
```

Task count must come from parsed files, not from target counts written in execution plans.

---

## 18. Family detail section B — evidence composition

Display D1/D2/D3 as a horizontal stacked bar.

Below it, render one card per evidence channel.

Absent:

```text
D1
0%
Not provided in this family.
```

Present:

```text
D3
60%

How the agent receives it:
The agent observes precondition violations and counterexamples through environment interaction.

Evidence files:
- evidence/d3_counterexamples.jsonl
```

---

## 19. Family detail section C — task list

Render a searchable table:

| Task ID | Slice | What is being drifted / stressed |
|---|---|---|
| C2.1_vehicle_001 | affected-new-edge | Engine start must recover the newly required parking-brake prerequisite. |
| C2.1_vehicle_007 | affected-retired-edge | The stale skill retains a brake-pedal prerequisite that is no longer required. |

Features:

```text
search by task ID
search by description
filter by slice
```

Do not paginate initially unless a family exceeds roughly 100 tasks.

---

## 20. Task row expansion

Clicking a task may reveal:

```text
full instruction
initial state
semantic goal
obligation support
source file
```

Only show fields that exist.

Do not expose hidden oracle data by default:

```text
gold_r_plus
skill_r_plus_oracle
hidden graph truth
possible_answer_r_plus
```

A future explicit developer/oracle view can expose these if needed.

---

## 21. Family detail section D — execution plan

Render the complete execution plan.

Preferred navigation:

```text
Overview
Tasks
Execution Plan
Files
```

If tabs complicate version 1, stacked sections are sufficient.

Preserve Markdown:

```text
headings
lists
code blocks
tables
```

Avoid internet CDNs.

Preferred options:

1. convert Markdown to sanitized HTML during `build_site.py`;
2. vendor a local renderer;
3. fallback to escaped `<pre>`.

---

## 22. Optional Files panel

For co-author inspection, show a lightweight manifest containing files such as:

```text
drift_spec.json
siblings.json
README.md
evidence/*
skill_r_minus.md
validation/construction_report.json
```

Hide implementation noise by default.

---

## 23. Search and filtering

Global:

```text
family ID/title search
platform filter
D1/D2/D3 presence filters
```

Family tasks:

```text
task ID search
description search
slice filter
```

All filtering can be client-side.

---

## 24. Visual style

Use a restrained dark research-dashboard style based only on this approved palette:

```text
#E35336
#FFB0A1
#9E3A26
#451911
#FFD3AC
#CCBEB1
#664C36
#331C08
```

The overall appearance should use a **dark brown background with light warm text**, with burnt-sienna/coral accents for interactive and evidence-related elements.

### Recommended semantic color tokens

Define the palette once in `site/styles.css` using CSS custom properties:

```css
:root {
  --bg-page: #331C08;
  --bg-surface: #451911;
  --bg-surface-soft: #664C36;

  --text-primary: #FFD3AC;
  --text-secondary: #CCBEB1;

  --accent-primary: #E35336;
  --accent-soft: #FFB0A1;
  --accent-deep: #9E3A26;

  --border: #664C36;
}
```

Do not introduce unrelated blues, greens, purples, or default framework colors in version 1.

### Page-level styling

```text
page background          #331C08
primary card background  #451911
secondary/raised surface #664C36
primary text             #FFD3AC
secondary text           #CCBEB1
primary accent           #E35336
soft accent              #FFB0A1
deep accent              #9E3A26
```

The intended hierarchy is:

```text
darkest brown page
    ↓
dark burnt-brown cards
    ↓
medium brown borders / secondary surfaces
    ↓
warm cream / peach text
    ↓
burnt-sienna accents for emphasis
```

### Typography

Use:

```text
body text:       #CCBEB1
main headings:   #FFD3AC
family/task IDs: #FFB0A1
links/buttons:   #FFB0A1 or #E35336
muted metadata:  #CCBEB1
```

Use system fonts so there is no external font dependency. Recommended stack:

```css
font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Task IDs, family IDs, file paths, and code should use a system monospace stack.

### Family cards

```text
background:       #451911
border:           #664C36
heading:          #FFD3AC
family ID:        #FFB0A1
body text:        #CCBEB1
hover border:     #E35336
hover/background: subtle #664C36 treatment
```

Keep cards flat and restrained. Avoid large drop shadows, glossy gradients, neon effects, or high-saturation fills over large areas.

### Buttons and links

For actions such as `Inspect family`, `View execution plan`, and `View paired family`:

```text
default text/accent: #FFB0A1
hover/focus:         #E35336
active/deep state:   #9E3A26
```

For filled buttons:

```text
background: #E35336
text:       #331C08
hover:      #FFB0A1
```

Always provide a visible keyboard focus state.

### Tables

```text
table background:  #451911
header background: #664C36
header text:       #FFD3AC
body text:         #CCBEB1
row separator:     #664C36
hover row:         subtle #664C36
task ID:           #FFB0A1
```

### Slice badges

Default badge:

```text
background: transparent
border:     #664C36
text:       #FFD3AC
```

Affected slices may use `#E35336` for border/text emphasis. Unchanged-retention and matched-null should use neutral warm-brown treatment rather than introducing green. Always display the slice text label.

### Execution-plan and code blocks

```text
code background: #331C08
code border:     #664C36
code text:       #FFD3AC
inline code:     #FFB0A1
```

Long code blocks should scroll horizontally rather than overflow.

### Accessibility

Do not rely on color alone. Every evidence segment, badge, status, and control must have a text label. Check contrast for the light text colors on `#331C08` and `#451911`. If an accent color is insufficient for small text, use it for borders, bars, icons, or large labels while keeping text in `#FFD3AC` or `#CCBEB1`.

---

## 25. Evidence color convention

Use stable evidence identities from the approved palette:

```text
D1 = #E35336
D2 = #FFB0A1
D3 = #9E3A26
```

Use these consistently in family cards, stacked evidence bars, percentage labels, family-detail evidence cards, filters, and legends.

### Stacked evidence bar

```text
D1 segment: #E35336
D2 segment: #FFB0A1
D3 segment: #9E3A26
bar track:  #664C36
```

Always print labels and percentages alongside the visualization, e.g. `D1 30%`, `D2 0%`, `D3 70%`.

### Evidence cards

Keep evidence cards dark:

```text
background: #451911
border:     #664C36
```

Use the channel-specific color only as a restrained identifier such as a left border, short top rule, badge, or percentage marker. Do not fill the entire evidence card with the accent color.

### Zero-percent channels

Keep absent channels visible:

```text
D2
0%
Not provided in this family.
```

Use `#CCBEB1` text and `#664C36` borders rather than hiding them.

### Hover and selected states

For interactive evidence filters:

```text
default border: #664C36
hover border:   channel-specific color
selected text:  #FFD3AC
selected state: channel-specific border plus subtle surface treatment
```

### Palette constraint

Version 1 should use only:

```text
#E35336
#FFB0A1
#9E3A26
#451911
#FFD3AC
#CCBEB1
#664C36
#331C08
```

plus transparency/opacity variants if needed. Do not add arbitrary framework default colors.

---

## 26. Drift summary fallbacks

Suggested initial summaries:

```text
C1.1:
Selected private device enum values are remapped or deprecated while semantic user intent remains fixed.

C1.2:
The private ignition token for engine start changes from START to X7 while engine-start semantics remain fixed.

C2.1:
Engine-start prerequisites change by adding a parking-brake prerequisite and retiring the full-brake prerequisite.

C2.2:
The same precondition-graph change as C2.1 must be discovered through environment interaction alone.

C3.1:
CLI command grammar changes through flag replacement/deprecation and a new lower-cost shortcut.

D1.2:
Semantic repository targets move or split across paths while the requested information remains unchanged.

D2.1:
TravelHub hotel navigation changes by replacing an old route and adding a shortcut; D1 only localizes the stale navigation region.

D2.2:
The same TravelHub navigation drift as D2.1 must be localized and reconstructed through interaction alone.
```

---

## 27. Platform/status badges

Normalize:

```text
BFCL
OSWorld
```

OSWorld design-only families must visibly remain labeled:

```text
Design-level
```

until execution validation exists.

---

## 28. Build script pseudocode

```python
def main():
    roots = parse_cli_roots()
    overrides = load_overrides()
    family_dirs = discover_family_dirs(roots)

    families = []

    for family_dir in family_dirs:
        family_id = family_dir.name
        plan = find_execution_plan(family_dir)
        drift_spec = load_optional_drift_spec(family_dir)

        evidence = parse_evidence_mix(
            family_dir,
            drift_spec,
            overrides.get(family_id)
        )

        tasks = parse_tasks(family_dir)
        tasks = [
            normalize_task(family_id, task, overrides)
            for task in tasks
        ]

        families.append({
            "id": family_id,
            "title": ...,
            "platform": ...,
            "drift_summary": ...,
            "task_count": len(tasks),
            "evidence": evidence,
            "tasks": tasks,
            "plan": copy_plan_asset(plan),
        })

    validate_index(families)
    write_index(families)
```

---

## 29. Parser functions

Implement in `parsers.py`:

```python
discover_family_dirs()
find_execution_plan()
find_task_file()
load_json_or_jsonl()
extract_task_list()
extract_task_id()
extract_task_slice()
extract_instruction()
make_task_description()
find_evidence_files()
parse_evidence_mix()
extract_drift_summary()
```

Keep parser logic independent of frontend code.

---

## 30. Evidence-file discovery heuristics

D1 candidates:

```text
*d1*
*changelog*
*notice*
*policy*
*declaration*
```

D2 candidates:

```text
*d2*
*success*trace*
*success*transcript*
*demonstration*
```

D3 candidates:

```text
*d3*
*probe*
*interaction*
*counterexample*
*help*
```

Use these only for file display and validation, not percentage inference.

---

## 31. Build validation

Fail or warn if:

```text
family has zero tasks
execution plan cannot be found
task IDs are duplicated
D1+D2+D3 != 100
present evidence channel has no delivery description
declared evidence file does not exist
task_count != normalized task-list length
```

Support:

```text
--allow-incomplete
```

for families still under construction.

---

## 32. Important C1.2 presentation detail

Display:

```text
C1.2 — D1 100%

D1 is explicitly provided because this family models a declared interface migration.

During adaptation:
stale skill + changelog → updated skill

The changelog declares:
START → X7

The zero-shot and static controls do not receive this declaration.
```

This prevents D1 from being confused with environment exploration.

---

## 33. Important D2.1 presentation detail

Preserve the strict D1 boundary.

Display:

```text
D1 tells the agent only that hotel-detail navigation may be stale.
```

Separately:

```text
D3 is responsible for discovering the actual changed route, new intermediate state, and shortcut.
```

Do not display hidden changed edges inside the D1 evidence card.

If a physical drift diagram is later added, label it:

```text
Benchmark construction / oracle view
```

not D1 evidence.

---

## 34. D2.1 versus D2.2 paired view

Add a comparison note:

```text
D2.1 and D2.2 use the same TravelHub r- → r+ physical change.

D2.1:
D1 localizes the stale region; D3 reconstructs the change.

D2.2:
D3 must both localize and reconstruct the change.
```

This makes clear why the two families are intentionally similar.

---

## 35. Paired-family links

Recommended:

```text
C2.1 ↔ C2.2
D2.1 ↔ D2.2
```

Example:

```text
Paired evidence condition: View C2.2
```

---

## 36. Do not add baseline plots in version 1

Version 1 should focus on benchmark construction:

```text
tasks
family design
evidence
execution plan
task count
```

Later add a separate Results tab after baseline evaluation stabilizes.

---

## 37. README for co-authors

`drift_web/README.md` should contain:

```bash
python build_site.py \
  --root ../C_drift_benchmark \
  --root ../D_drift_benchmark

python -m http.server 8080 --directory site
```

Then:

```text
Open http://localhost:8080
```

Explain that rerunning the build script refreshes counts and metadata.

---

## 38. Tests

At minimum test:

### C1.2 single-task parsing

`task.json` normalizes to one task.

### C2.1 sibling parsing

Every sibling in `siblings.json` receives a stable ID and slice.

### Evidence composition

Verify:

```text
C1.1 = 0/50/50
C1.2 = 100/0/0
C2.1 = 0/40/60
C2.2 = 0/0/100
C3.1 = 50/0/50
D2.1 = 30/0/70
D2.2 = 0/0/100
```

### Plan discovery

The correct `*_execution_plan.md` is selected.

### Duplicate IDs

Build fails on duplicate task IDs.

---

## 39. Version-1 acceptance checklist

- [ ] every discovered family appears on the overview page;
- [ ] task counts are derived from disk;
- [ ] D1/D2/D3 percentages appear for every family;
- [ ] each present evidence channel explains how it reaches the agent;
- [ ] absent evidence channels are visibly absent;
- [ ] each family has a searchable task list;
- [ ] task slices appear when available;
- [ ] each family renders its execution plan;
- [ ] C1.2 correctly explains explicit D1 changelog delivery;
- [ ] D2.1 does not leak hidden graph edges through its D1 description;
- [ ] D2.1 and D2.2 are identified as paired physical-drift conditions;
- [ ] OSWorld families are labeled as design-level;
- [ ] the site consistently uses the approved dark palette and light warm text;
- [ ] D1/D2/D3 colors follow the documented palette mapping and remain text-labeled;
- [ ] the site works with `python -m http.server`;
- [ ] no external service is required;
- [ ] adding siblings and rebuilding automatically updates task counts.

---

## 40. Suggested implementation sequence for a coding agent

1. Inspect all supplied roots and print discovered family directories.
2. For each family, print selected execution plan, candidate task file, drift spec, and evidence files.
3. Implement JSON/JSONL task normalization.
4. Implement evidence-percentage extraction and `family_overrides.json`.
5. Generate and manually inspect `benchmark_index.json`.
6. Add validation for counts, duplicate IDs, and evidence percentages.
7. Build overview cards.
8. Add hash-based family routing.
9. Add task search and slice filters.
10. Add the evidence composition panel.
11. Add execution-plan rendering.
12. Add paired-family links labels.
13. Test against the full C benchmark.
14. Test against the D benchmark if present.
15. Manually inspect at least `C1.2`, `C2.1`, `C3.1`, `D2.1`, and `D2.2`.
16. Verify that adding one temporary sibling to a test fixture increments the displayed count after rebuild.
17. Remove the temporary fixture and finalize.

---

## 41. Expected user experience

The overview should answer:

```text
What benchmark families exist?
How many tasks are in each?
What kind of drift does each family represent?
What evidence mixture does each family use?
```

Clicking a family should answer:

```text
What are the sibling tasks?
Which slice does each belong to?
What is the one-sentence drift description?
How does D1/D2/D3 reach the agent?
How was this family constructed?
```

That is sufficient for the initial goals of visual presentation and co-author inspection.
