# Phase 3 — Knowledge Graph Construction

## Purpose

Phase 1 produces a list of concept pairs (`A ↔ B`) as seeds. Phase 3 expands these into a **structured knowledge graph** — not just a visualization, but a queryable, version-able, cross-session-mergeable representation of the subject's mental architecture.

| Phase | Output | Question it answers |
|-------|--------|---------------------|
| 1 | System of Values | *What* matters and how much? |
| 2 | Cognitive Patterns | *How* does the subject think? |
| **3** | **Knowledge Graph** | **How are the subject's concepts connected?** |
| 4 | Behavioral Model | What will the subject *do* in situation X? |

Phase 3 consumes Phase 1 seeds. It is **not audited by `meta-critic`** — the graph is the most directly inspectable of the four products (rendered as a graph view in any markdown PKM), and the subject's audit is the validation step.

### Why a graph

1. **Relations between nodes are themselves data.** A tension `A ↔ B` tells us A and B are structurally linked, not separately stored.
2. **Supports incremental updates.** Each new session can merge into the same graph rather than producing isolated reports.
3. **Surfaces second-order structure.** With enough nodes, hub concepts (linked to many others) emerge — these are the load-bearing structures of the subject's mind.
4. **Facilitates user verification.** A graph is more inspectable than narrative, making it easier for the subject to point at "this part is wrong."

## Inputs

| Item | Description |
|------|-------------|
| Phase 1 synthesis | `personalized/saves/session/<session_id>/analyses/synthesis.md` — provides the `Phase 3 seeds` list and the four analyst reports it cites. |
| Phase 1 analyst reports | `personalized/saves/session/<session_id>/analyses/{affect,social,values,narrative}.md` — used to ground edge typing and quote citation. |
| Existing graph (cross-session) | If present, `personalized/results/profile/knowledge_graph/` — new nodes merge in rather than overwrite. |

## Process: knowledge-graph-builder

```
       ┌────────────────────────────────────┐
       │ Phase 1 synthesis + analyst reports │
       └──────────────┬─────────────────────┘
                      │
                      ▼
         knowledge-graph-builder
              │       │       │       │
              ▼       ▼       ▼       ▼
        seed nodes  draft   typed    edge
        from seeds  files   edges    audit
              │       │       │       │
              └───────┴───┬───┴───────┘
                          ▼
              personalized/results/profile/
                  knowledge_graph/
                  ├── concepts/
                  ├── emotions/
                  ├── people/
                  └── events/
```

### Workflow

**Step 1 — Seed nodes from Phase 1.** Read the `Phase 3 seeds` list from synthesis.md. List every concept, emotion, person, and event mentioned recurrently in the analyst reports. Expect 30–50 seed nodes for a single rich session.

**Step 2 — Generate node files.** Use the node template (below). This step is largely templating: read each seed's supporting evidence in the analyst reports, draft the definition, populate frontmatter.

**Step 3 — Populate edges.** The most judgment-intensive step. The builder:
- Mechanically scans node bodies for `[[link]]` references — these become edge candidates
- Types each edge (`tension` / `cause` / `derives` / `contradicts` / `reinforces` / `weakens` / `stands_for`)
- Cross-references the analyst reports to verify each edge has at least one quotation supporting it

**Step 4 — Sweep for orphans.** Nodes with zero incoming or outgoing edges are flagged. Either evidence is missing, or the node is mis-categorized.

The builder produces a draft directory ready for subject inspection in a graph-view PKM (Obsidian, etc.). Subject corrections then feed the next iteration.

## Outputs

The Phase 3 product is a directory of typed markdown nodes:

```
personalized/results/profile/knowledge_graph/
├── concepts/
├── emotions/
├── people/
└── events/
```

### Node types

| Type | Description |
|------|-------------|
| `Concept` | Abstract concepts the subject uses to define themselves or organize experience |
| `Emotion` | Persistent emotional states the subject names |
| `Person` | Recurring relational figures (use role-based or anonymized identifiers, not real names — see neutrality invariant) |
| `Event` | High-affect or pattern-defining moments |

The actual content of each category is subject-specific and is constructed from Phase 1 outputs.

### Node frontmatter schema

```yaml
---
type: Concept | Emotion | Person | Event
first_appeared: <turn id, session id>
mentions: <integer>
centrality: 1-5  # estimated structural importance
stability: stable | context-dependent | evolving
valence: positive | negative | neutral | mixed
confidence: high | medium | low
sessions: [list of session IDs where this surfaces]
cross_framework_consensus: 0-4  # how many Phase 1 analysts touched it
---
```

### Edge types

Edges must be typed; an untyped graph is a loose mesh.

| Edge type | Marker | Meaning |
|-----------|--------|---------|
| Tension | `↔ tension` | A and B form a structural pull within the subject |
| Cause | `→ causes` | A triggers B |
| Derives | `⇒ derives` | B is an inference or application of A |
| Contradicts | `× contradicts` | the subject holds both A and B but they are incompatible |
| Reinforces | `+ reinforces` | A's presence strengthens B |
| Weakens | `- weakens` | A's presence weakens B |
| Stands-for | `↦ stands_for` | A is a manifestation or symbol of B |

### Single-node template

```markdown
---
type: Concept
first_appeared: <turn id, session id>
mentions: 12
centrality: 5
stability: stable
valence: mixed
confidence: high
cross_framework_consensus: 4
sessions: [<session_id_1>, <session_id_2>]
---

# <node-title>

## Definition
[A short paragraph defining the concept as the subject uses it. Distinct from a dictionary definition.]

## Related (grouped by edge type)

### Tension
- [[other-concept-1]] ↔ [why this is a structural tension]
- [[other-concept-2]] ↔ [...]

### Cause
- [[trigger-event]] → this concept
- this concept → [[downstream-effect]]

### Derives
- this concept ⇒ [[derived-pattern]]

## Representative quotes
> "..." [<turn>] (<session_id>)

## Turns
[<turn>][<turn>][<turn>] (<session_id>)

## Notes
- Cross-framework consensus from Phase 1: [analysts that touched this]
- Stability over sessions: [what trend, if any]
```

## Quality criteria

A Knowledge Graph is acceptable when:

1. **Every node has at least one inbound or outbound edge.** Isolated nodes signal a categorization issue.
2. **Every edge has supporting evidence.** A `tension` edge between A and B should cite at least one quote (or a clear behavioral pattern) from the analyst reports.
3. **Hub nodes are real, not artifacts.** A node with `centrality: 5` should appear across multiple Phase 1 analyst reports, not just one.
4. **Cross-framework consensus is recorded.** The `cross_framework_consensus` field should reflect actual analyst coverage (verified against the reports).
5. **Wiki-links resolve.** `[[link]]` references must point to existing node files or be flagged as planned-but-not-yet-built.

## Pitfalls

### Granularity drift
"Anxiety" as one node vs. context-typed variants ("domain-A anxiety", "domain-B anxiety"). Default rule: split when ≥2 sessions show context-specific patterns. Don't split prematurely on a single session.

### Edge-typing as decoration
Picking an edge type because it sounds right, not because it's grounded. Each edge type carries semantic weight; misuse degrades the graph's queryability.

### Centrality inflation
Marking too many nodes as `centrality: 5`. The hub designation should be reserved for nodes that genuinely structure many others (suggested ceiling: 5–7 hubs per session-source).

### Echoing the AI's framing
Some node titles or definitions may be lifted from the AI's prior summarization rather than the subject's language. Prefer the subject's own phrasing where it exists.

## Pipeline integration

| Concern | Where handled |
|---------|---------------|
| Builder dispatch | `orchestrator` runs `knowledge-graph-builder` after Phase 1 has converged |
| Cross-session merge | When a new session's Phase 1 outputs arrive, the builder merges into the existing graph (see Cross-session integration in `pipeline.md`) |
| Graph rendering | Subject inspects via any markdown-graph PKM (Obsidian, Foam, Logseq) |
| Output-language consistency | Node titles and definitions are in the source conversation's dominant language |
| Privacy / neutrality | `Person` nodes use role-based or anonymized identifiers; `validate_pipeline` checks this document contains no subject-specific content |

## Where Phase 3 fits in product flow

Phase 3 produces the `knowledge_graph/` directory. The `profile-compressor` reads the graph (specifically: hub nodes and their definitions, plus tension edges between hubs) when it builds `user_profile.md`. Most of the graph stays on disk for cross-session integration and direct subject inspection — only the hub structure makes it into the compressed profile.

## See also

- `methodology/pipeline.md` — overall pipeline architecture
- `methodology/phase1_value_extraction.md` — produces the seeds Phase 3 expands
- `methodology/phase4_behavioral_model.md` — sibling phase; consumes Phase 1 seeds independently
- `agents/knowledge-graph-builder.md` — the builder prompt
- `agents/orchestrator.md` — how Phase 3 is dispatched in the overall pipeline
