# Digital Persona Analysis Pipeline

> **Reading guide.** This document is the **conceptual overview** of the batch-layer pipeline — written for humans (engineers, contributors, customizers) trying to understand the system. The agent files under `${CLAUDE_PLUGIN_ROOT}/agents/` are Claude Code subagent definitions (LLM system prompts plus model + tool restrictions) and are not duplicated here. Specifically:
>
> | If you want to … | Read |
> |---|---|
> | Understand the architecture and methodology | this file |
> | Understand any single phase in depth | `methodology/template/phase{1,2,3,4}_*.md` |
> | See exactly what an agent does, step by step | `${CLAUDE_PLUGIN_ROOT}/agents/<agent-name>.md` |
> | See how the runner dispatches the agents | `methodology/template/orchestration_protocol.md` |
> | Understand how output validation works | `methodology/template/output_contract_schema.md` |
>
> This file does **not** contain executable instructions for any LLM. It contains design rationale, invariants, and pointers.

## Overview

The pipeline turns conversational data (the subject's prior chats with AI assistants) into a structured persona profile that downstream systems can consume. It runs in two layers:

```
                     ┌────────────────────────────────────┐
                     │  Conversation layer (everyday use) │
                     │  load_persona reads user_profile.md│
                     │  → assistant adapts responses      │
                     └────────────────┬───────────────────┘
                                      ▲
                                      │ consumes one compressed file
                                      │
                     ┌────────────────┴───────────────────┐
                     │  Batch layer (analysis pipeline)   │
                     │  invoked by /run_pipeline,         │
                     │  dormant outside skill invocation  │
                     └────────────────────────────────────┘
```

The batch layer produces five persistent products under `personalized/results/profile/`:

| Product | Question answered | Phase | Audited |
|---------|-------------------|-------|---------|
| System of Values | *What* matters and how much? | Phase 1 | yes (meta-critic loop) |
| Cognitive Patterns | *How* does the subject think? | Phase 2 | no |
| Knowledge Graph | How are the subject's concepts connected? | Phase 3 | no |
| Behavioral Model | What will the subject *do* in situation X? | Phase 4 | no |
| **User Profile** | **The compressed brief the conversation layer reads** | **Final compression** | no |

Phase 1 is the foundation. Its synthesis emits **seeds** (concept pairs and situation→response patterns) that Phase 3 and Phase 4 expand. Phase 2 is independent — it operates directly on the source text and can run in any order relative to the others. Final compression reads all four detailed products and produces `user_profile.md`.

Only Phase 1 carries the Worker–Evaluator quality gate. Phase 2/3/4 are deterministic expansions of either the source data (Phase 2) or Phase 1 seeds (Phase 3/4); their outputs are auditable by the subject directly.

## Data sources

The pipeline accepts standardized conversation logs. Source-format conversion is handled by per-source extractors (skills under `skills/extract_<source>/`). All inputs eventually reach the analysis stage as JSON of the form:

```json
[{ "order": <int>, "user": "<text>", "model": "<text>" }, ...]
```

## Stage 1 — Capture

Two situations are supported:

- **Bulk import** of historical conversations: per-platform extractor skills (`skills/extract_gemini/`, etc.) capture a share-link or export and standardize it.
- **Forward-going capture**: `save_session` snapshots the current Claude Code conversation when invoked.

Output: `personalized/saves/session/<session_id>/conversation.json`.

## Stage 2 — Topic annotation

Add topic-cluster headers to the conversation so analysts can keep cross-topic context distinct. Annotated format:

```
### [<topic>  | turns <N>...]
[NNN] USER: <text>
      AI summary: <first 120 chars of model response>...
```

Cluster boundaries are inferred (manually or via topic-modeling LLM call). Each cluster has a turn range and a short topic label.

**Why cluster boundaries matter.** In long sessions (>50 turns), subject behavior often shifts by topic. Treating turns 1–30 (one topic) and turns 80–110 (a different topic) as a uniform stream conflates context-specific states with stable traits. The boundary is a hard discipline for analysts: high-confidence findings must show evidence from at least two clusters.

Output: `personalized/saves/session/<session_id>/annotated.txt`.

### Clustering options

| Option | Pros | Cons |
|--------|------|------|
| LLM-driven (recommended) | Strong on semantics; bilingual-friendly | Costs LLM calls |
| BERTopic / classical NLP | Deterministic; no LLM call | Weaker on semantics; per-language preprocessing |
| Manual via template | Suitable for very short sessions | Does not scale |

The recommended hybrid: LLM produces a draft, the subject reviews and corrects.

## Stage 3 — Phase 1: Four-frame analysis (audited)

Four analysts read the annotated conversation in parallel, each through a different lens:

| Agent | Frame |
|-------|-------|
| `affect-analyst` | Emotional architecture — fears, defenses, attachments |
| `social-dynamics-analyst` | Power, status, organizational positioning |
| `values-analyst` | Value hierarchy and decision principles |
| `narrative-analyst` | Self-story, identity language, causal attribution |

Each writes to `personalized/saves/session/<session_id>/analyses/<short-name>.md` (`affect`, `social`, `values`, `narrative`).

`meta-critic` then audits all four against their declared output contracts. Verdicts are `pass` / `pass_with_warnings` / `needs_revision` / `unrecoverable`. The orchestrator re-dispatches only the analysts marked `needs_revision`. The loop is bounded at `MAX_ITERATIONS` (default 3); at iteration 3, any remaining `needs_revision` becomes `escalate`.

Once the loop converges (or escalates), `synthesis-builder` is dispatched as its own stage. It reads the four analyst reports plus `meta_critic.md` and produces a cross-framework synthesis: high-consistency findings, real divergences, composite portrait, **Phase 3 seeds**, **Phase 4 seeds**, and pipeline caveats. From this synthesis, `system_of_values.md` is produced as the formal Phase 1 product.

The exact dispatch protocol — parallelism, iteration feedback, when synthesis-builder runs — lives in `methodology/template/orchestration_protocol.md`. This file describes **why** four frames are needed; the orchestration protocol describes **how** they are run.

Common methodological constraints (each agent enforces these):

1. **Evidence priority**: pre-rational signals > concrete actions > corrections of AI > cross-cluster recurrence > single self-disclosure > AI-anchored statements
2. **AI-anchoring filter**: statements mirroring the AI's prior framing are downgraded or excluded unless the subject extends the framing in their own language
3. **Cluster-boundary discipline**: high-confidence findings need evidence from ≥2 clusters
4. **Long-session memory degradation**: late-session reframings may be partial reconstructions, not stable insights — flag them

See `methodology/template/phase1_value_extraction.md` for the full Phase 1 specification.

## Stage 4 — Phase 2: Cognitive patterns build (no audit)

A `cognitive-patterns-builder` runs over the source conversation and produces `cognitive_patterns.md`: lexical fields, metaphor systems, question style, argument structure, emotional–rational oscillation, and metacognition profile. Optionally a small quantitative pre-pass (Python regex/counters) produces baseline statistics the builder interprets.

No meta-critic audit. The builder's output is short, language-level, and the subject can sanity-check it directly. See `methodology/template/phase2_cognitive_patterns.md`.

## Stage 5 — Phase 3: Knowledge graph build (no audit)

A `knowledge-graph-builder` consumes Phase 1's synthesis and seeds. It generates a directory of typed markdown nodes (concepts / emotions / people / events) with frontmatter, wiki-links, and edges typed by relation (tension / cause / derives / contradicts / reinforces / weakens / stands_for).

No meta-critic audit; the subject inspects the graph directly in a markdown PKM (Obsidian Graph View, etc.). See `methodology/template/phase3_knowledge_graph.md`.

## Stage 6 — Phase 4: Behavioral model build (no audit)

A `behavioral-model-builder` consumes Phase 1's seeds and expands each `Situation → Response` row into a full Behavior Pattern unit (trigger thresholds, intensity-stratified responses, recovery, modulators, evidence, related patterns). Output: one BP-XXX file per pattern.

No meta-critic audit; subject self-review is the validation step (per the methodology doc). See `methodology/template/phase4_behavioral_model.md`.

## Stage 7 — Final compression: user_profile.md

A `profile-compressor` reads all four detailed products and emits `user_profile.md`: a ≤200-line, plain-language brief written in the user's natural register, with the section "How they like to work with an AI" as its operationally most important payload. This is the only file `load_persona` reads at conversation time.

The compression is not lossless. The detailed products remain on disk for cross-session integration, audit, and direct reference.

**Hard constraint on the compressor**: no analytical jargon (e.g. "external validation dependency", "intellectualization defense", "explicit-vs-revealed gap") unless the source conversation itself uses those terms. The brief is a colleague handover, not an academic report. This avoids "prompt pollution" — the assistant adopting a stilted analytical register after loading the brief.

## Five-product output layout

```
personalized/results/profile/
├── system_of_values.md          # Phase 1
├── cognitive_patterns.md        # Phase 2
├── knowledge_graph/             # Phase 3 (directory of typed nodes)
├── behavioral_model/            # Phase 4 (directory of BP-XXX files)
└── user_profile.md              # Final compression (load_persona reads only this)
```

## Methodological invariants

These hold across all phases:

1. **Action over words** — behavioral evidence outweighs self-report
2. **AI-anchoring filter** — subject must have introduced or extended a framing in their own language for it to count as their own
3. **Cluster-boundary discipline** — high-confidence claims require ≥2 clusters
4. **Pre-rational evidence weighted highest** — body symptoms, outbursts, crying, panic
5. **No new findings in audit layer** — `meta-critic` must not produce subject analysis itself
6. **Output language matches source** — every product is written in the conversation's dominant language

## Cross-session integration

A single session is biased by topic, mood, and the subject's framing relationship to that particular AI. Stable claims require multiple sessions.

When a new session enters the pipeline, integration into the persistent products is non-trivial. Sub-problems:

| Sub-problem | Approach |
|-------------|----------|
| **Concept merging** | Vector similarity between definitions + LLM judgment for borderline cases + subject review for the rest |
| **Evidence accumulation** | Each Knowledge Graph node and Behavior Pattern carries a session list, mention count, and confidence trend (rising / stable / falling) |
| **Conflict resolution** | Latest-wins, confidence-weighted, or `evolving` tag pending more sessions — chosen per-finding, not globally |
| **Stability tagging** | `stable` (≥3 sessions) / `context-dependent` / `evolving` / `single-session` |

The compressor re-runs after integration; `user_profile.md` is regenerated.

Cross-session integration is the hardest unsolved part of the pipeline. Human-in-the-loop is the default for conflict resolution.

## Known data biases

Single-session input is always biased — the subject brings only some topics, in a specific mood, with a specific framing relationship to the AI. Phase 4 in particular must distinguish session-state from stable trait. Cross-session integration (above) is the corrective.

## Adjacent documents

- `${CLAUDE_PLUGIN_ROOT}/agents/affect-analyst.md`, `${CLAUDE_PLUGIN_ROOT}/agents/social-dynamics-analyst.md`, `${CLAUDE_PLUGIN_ROOT}/agents/values-analyst.md`, `${CLAUDE_PLUGIN_ROOT}/agents/narrative-analyst.md` — Phase 1 analyst subagents
- `${CLAUDE_PLUGIN_ROOT}/agents/meta-critic.md` — Phase 1 quality auditor subagent
- `${CLAUDE_PLUGIN_ROOT}/agents/synthesis-builder.md` — Phase 1 cross-frame synthesizer subagent (writes `synthesis.md`)
- `methodology/template/orchestration_protocol.md` — pipeline coordination protocol (Phase 1 loop + synthesis dispatch + Phase 2/3/4 dispatch + final compression). Followed by the `/run_pipeline` skill at top-level.
- `${CLAUDE_PLUGIN_ROOT}/agents/cognitive-patterns-builder.md` — Phase 2 builder
- `${CLAUDE_PLUGIN_ROOT}/agents/knowledge-graph-builder.md` — Phase 3 builder
- `${CLAUDE_PLUGIN_ROOT}/agents/behavioral-model-builder.md` — Phase 4 builder
- `${CLAUDE_PLUGIN_ROOT}/agents/profile-compressor.md` — final compressor (writes `user_profile.md`)
- `methodology/template/output_contract_schema.md` — contract format used by all audited agents
- `skills/run_pipeline/SKILL.md` — single user-facing entry point; executes the orchestration protocol
- `skills/load_persona/SKILL.md` — conversation-layer entry point (reads `user_profile.md` only)
