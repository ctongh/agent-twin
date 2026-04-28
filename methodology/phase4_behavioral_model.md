# Phase 4 — Behavioral Model Construction

## Purpose

Phase 1 tells us *what the subject treats as important* (values), Phase 3 tells us *how their concepts connect* (knowledge graph), Phase 4 answers **"in situation X, what will the subject do?"**

| Phase | Output | Question it answers |
|-------|--------|---------------------|
| 1 | System of Values | *What* matters and how much? |
| 2 | Cognitive Patterns | *How* does the subject think? |
| 3 | Knowledge Graph | How are the subject's concepts connected? |
| **4** | **Behavioral Model** | **What will the subject *do* in situation X?** |

Phase 4 is the most application-relevant phase. A well-constructed Behavioral Model lets a downstream system anticipate the subject's responses, reducing the communication overhead between subject and system.

Phase 4 consumes Phase 1 seeds (the `Phase 4 seeds` list in synthesis.md) and is **not audited by `meta-critic`**. The validation strategy is subject self-review (which patterns ring true, which feel "not me") plus, over time, hold-out sessions and counterfactual probes.

## Inputs

| Item | Description |
|------|-------------|
| Phase 1 synthesis | `personalized/saves/session/<session_id>/analyses/synthesis.md` — provides the `Phase 4 seeds` list. |
| Phase 1 analyst reports | `personalized/saves/session/<session_id>/analyses/{affect,social,values,narrative}.md` — used to ground intensity thresholds, modulators, and recovery. |
| Phase 3 knowledge graph | `personalized/results/profile/knowledge_graph/` (if available) — used to link Behavior Patterns to relevant graph nodes. |
| Existing behavioral model (cross-session) | If present, `personalized/results/profile/behavioral_model/` — new patterns merge in rather than overwrite. |

## Process: behavioral-model-builder

```
       ┌────────────────────────────────────┐
       │ Phase 1 synthesis + analyst reports │
       │ + Phase 3 graph (if available)      │
       └──────────────┬─────────────────────┘
                      │
                      ▼
         behavioral-model-builder
              │       │       │       │
              ▼       ▼       ▼       ▼
        promote   build     ground    chain
        seeds     intensity modulators related
        to BPs    levels    in evidence patterns
              │       │       │       │
              └───────┴───┬───┴───────┘
                          ▼
              personalized/results/profile/
                  behavioral_model/
                  ├── BP-001_<short-name>.md
                  ├── BP-002_<short-name>.md
                  └── ...
```

### Workflow

**Step 1 — Promote seeds to Behavior Patterns.** Read the `Phase 4 seeds` list. Each seed has the form `Situation → Response (confidence)`. Promote a seed to a full Behavior Pattern when:
- The situation can be characterized at three intensity levels
- The response varies meaningfully across those levels (not just "more of the same")
- The modulators are observable in the source data

Seeds that don't meet these conditions stay as seeds — note them in the directory README rather than forcing a thin pattern.

**Step 2 — Build intensity-stratified responses.** For each promoted pattern, characterize low / medium / high intensity. Each level has observable behavior, internal experience, and typical duration.

**Step 3 — Ground modulators in evidence.** Identify amplifiers (factors that intensify the response) and dampeners (factors that reduce it). Each modulator should be traceable to specific turns in the source.

**Step 4 — Chain related patterns.** Some patterns are sub-routines of larger cycles (e.g., a recovery pattern follows a crisis pattern). Record `related_patterns` cross-references.

**Step 5 — Link to graph nodes.** Where a pattern touches a Knowledge Graph concept, add `[[concept-name]]` references.

## Outputs

The Phase 4 product is a directory of pattern files:

```
personalized/results/profile/behavioral_model/
├── BP-001_<short-name>.md
├── BP-002_<short-name>.md
└── ...
```

Each file contains:
- YAML frontmatter (the schema below)
- Detailed prose explanation
- Representative quotes with turn IDs (and session IDs if cross-session)
- Links to relevant Knowledge Graph nodes (`[[concept-name]]`)
- Counterexamples or known exceptions

### Behavior Pattern schema

```yaml
Behavior_Pattern:
  id: BP-<id>
  name: <descriptive name>

  trigger:
    situation: <description of the triggering situation>
    threshold:
      low:    <when this is a mild instance>
      medium: <when this is a moderate instance>
      high:   <when this is a severe instance>

  response:
    low_intensity:
      observable: [<external behaviors>]
      internal:   [<inner experience>]
      duration:   <typical duration>
    medium_intensity:
      observable: [...]
      internal:   [...]
      duration:   <...>
    high_intensity:
      observable: [...]
      internal:   [...]
      duration:   <...>

  recovery:
    low:    <what restores baseline at low intensity>
    medium: <...>
    high:   <...>

  modulators:
    amplifiers:  [<factors that intensify the response>]
    dampeners:   [<factors that reduce the response>]

  evidence:
    sessions: [<session IDs>]
    turns:    [<turn IDs within those sessions>]
    confidence: high | medium | low

  related_patterns:
    - BP-<id>  # patterns this one chains to or is nested in
```

### Pattern categories

Common Behavior Pattern categories (illustrative, not prescriptive):

- **Affect-driven** — patterns triggered by emotional states
- **Boundary-driven** — patterns triggered by perceived violations
- **Defense** — patterns that protect identity or self-image
- **Strategic** — patterns the subject deploys deliberately to navigate situations
- **Cyclic / systemic** — meta-patterns that contain other patterns (e.g., burnout cycles)

## Quality criteria

A Behavioral Model is acceptable when:

1. **Each pattern has all three intensity levels populated.** A pattern with only one intensity is a seed, not a pattern — keep it as a seed.
2. **Triggers are distinguishable.** Two patterns with identical triggers should be merged (or differentiated by modulator).
3. **Recovery is concrete.** "The subject returns to baseline" is not enough; what restores baseline?
4. **Evidence is traceable.** Every intensity level cites at least one supporting turn.
5. **Inter-pattern relations are noted.** A pattern that systematically follows another should be linked via `related_patterns`.

## Pitfalls

### Overfitting the past
Patterns reconstructed from history may not predict future behavior. Mitigations:

**Short-term validation** (always done):
- Subject self-review: which patterns does the subject recognize as theirs? Which feel "not me"?
- Pattern distinguishability: if two patterns always co-occur, consider merging them
- Counterfactual probe: "if the response in situation X were the opposite of pattern Y, would that be plausible?"

**Medium-term validation** (cross-session):
- Hold-out sessions: take the next session captured after Phase 4 was built; check whether new events fit existing patterns
- Cross-domain validation: do patterns identified in domain A also surface in domain B?
- Stress-level testing: patterns observed during a high-stress period — do they appear in calm periods too, or only under stress?

### Stage-state as stable trait
A subject in burnout has different patterns than the same subject at baseline. Phase 4 must distinguish stage-state from stable trait. Patterns evidenced only during one phase of the source should be tagged accordingly in the prose explanation.

### Over-stratification
Forcing a pattern into low/medium/high when only two levels are clear in the data. Better to mark one level as `not observed` than to fabricate.

### Confidence inflation
A pattern observed in a single session is not `high` confidence regardless of how clear it looks. Cross-session recurrence is the path to high confidence.

## Pipeline integration

| Concern | Where handled |
|---------|---------------|
| Builder dispatch | `orchestrator` runs `behavioral-model-builder` after Phase 1 has converged (and Phase 3 if it has built first) |
| Cross-session merge | When a new session's Phase 1 outputs arrive, the builder updates pattern frontmatter (sessions, evidence) rather than overwriting |
| Subject self-review | Subject reads the directory; flags patterns that feel off; the next pipeline iteration adjusts |
| Output-language consistency | Pattern names and prose explanations are in the source conversation's dominant language |
| Privacy / neutrality | Pattern names and observable behaviors must not name specific individuals; `validate_pipeline` checks this document contains no subject-specific content |

## Where Phase 4 fits in product flow

Phase 4 produces the `behavioral_model/` directory. The `profile-compressor` reads it (specifically: the highest-confidence patterns and their plain-language situation→response summaries) when it builds `user_profile.md`. Most of the model stays on disk for cross-session validation and detailed reference — only the most actionable patterns make it into the compressed profile, and they are translated out of YAML schema into plain "When X, they tend to Y" phrasing.

### Downstream applications

The compiled Phase 4 product can be used for:

1. **Conversation-layer adaptation** — the compressed summary in `user_profile.md` makes the assistant aware of how the subject is likely to react in different situations
2. **Scenario simulation** — given a hypothetical situation, predict the subject's likely response trajectory
3. **Intervention design** — if the subject wants to change a pattern, the modulators section identifies leverage points
4. **Communication shorthand** — the subject can choose to share specific Behavior Patterns with trusted contacts to reduce ongoing communication overhead

## See also

- `methodology/template/pipeline.md` — overall pipeline architecture
- `methodology/template/phase1_value_extraction.md` — produces the seeds Phase 4 expands
- `methodology/template/phase3_knowledge_graph.md` — sibling phase; provides graph nodes for cross-linking
- `agents/behavioral-model-builder.md` — the builder prompt
- `agents/orchestrator.md` — how Phase 4 is dispatched in the overall pipeline
