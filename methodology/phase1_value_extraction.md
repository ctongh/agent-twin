# Phase 1 — Value Extraction (System of Values)

## Purpose

Phase 1 extracts the subject's **System of Values** from the annotated conversation: the layered structure of what they treat as non-negotiable, what they will protect with effort, what they prefer but trade away, and what is genuinely peripheral.

It is the foundation phase. Its synthesis emits **seeds** that Phase 3 (Knowledge Graph) and Phase 4 (Behavioral Model) expand:

| Phase | Output | Question it answers |
|-------|--------|---------------------|
| **1** | **System of Values** | ***What* matters and how much?** |
| 2 | Cognitive patterns | *How* does the subject think? |
| 3 | Knowledge Graph | How are the subject's concepts connected? |
| 4 | Behavioral Model | What will the subject *do* in situation X? |

Phase 1 is also the **only audited phase**. The four-frame design plus the `meta-critic` Worker–Evaluator loop is what gives Phase 1's output enough rigor to seed downstream phases. Phase 2/3/4 builders are deterministic expansions over either the source text or Phase 1's seeds; their outputs are auditable by the subject directly.

## Inputs

| Item | Description |
|------|-------------|
| Annotated conversation | Output of Stage 2 of the upstream pipeline (raw conversation + topic-cluster headers + per-turn AI summaries). |
| Optional context | One paragraph of situational facts (role, life stage, organizational setting). Avoid identifying details. |

## Process: four-frame parallel + Worker–Evaluator + synthesis

Phase 1 is **not** a single agent. It is a four-frame parallel analysis followed by a Worker–Evaluator audit, then a cross-framework synthesis produced by a dedicated `synthesis-builder` subagent. Each frame surfaces values from a different angle; the synthesis-builder is where the System of Values is actually constructed.

```
            ┌─────────────────────────────────┐
            │ annotated conversation          │
            └──────────────┬──────────────────┘
                           │ (dispatched in parallel)
       ┌──────────────┬────┴────┬──────────────┐
       ▼              ▼         ▼              ▼
  affect-       social-    values-       narrative-
  analyst       dynamics-  analyst       analyst
                analyst
       │              │         │              │
       ▼              ▼         ▼              ▼
            ┌─────────────────────────────────┐
            │ four analyst reports            │
            └──────────────┬──────────────────┘
                           ▼
                     meta-critic
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
              accept         iterate (≤3 rounds)
                  │                 │
                  │                 │ (revisions feed back to analysts)
                  ▼                 │
           synthesis-builder ◄──────┘ (when accepted or escalated)
                  │
                  ▼
              synthesis.md
                  │
                  ▼
            System of Values
            (saved as the Phase 1 product)
```

### Why four frames, not one

A single "values agent" tends to read declared values at face value and miss the gap between explicit statements and revealed preferences. The four-frame design forces triangulation:

| Frame | What it sees that single-frame approaches miss |
|-------|------------------------------------------------|
| **affect-analyst** | Values protected by emotional reaction (fear, anger, crying often signals a touched value) |
| **social-dynamics-analyst** | Values revealed by behavior under power asymmetry and status pressure |
| **values-analyst** | Direct value claims and refusal/persistence patterns |
| **narrative-analyst** | Values implicit in the subject's self-narrative and identity language |

Each frame catches a different signature of "what matters." The synthesis step compares them: when multiple frames converge on the same value, that value is high-confidence. When frames diverge, the divergence itself is informative (e.g., a value defended in narrative but not in behavior).

## Outputs

The Phase 1 product is a single document, conventionally saved at:

```
personalized/results/profile/system_of_values.md
```

Its structure:

### Core (non-negotiable)
Values defended even at significant cost, across multiple contexts. Evidence required: refusals under pressure, persistence despite real downsides, cross-cluster recurrence.

### Boundaries (held with effort)
Values defended in most contexts but sometimes negotiated. Evidence required: visible boundary-setting actions, occasional concessions with stated reasons.

### Strong preferences (defended when easy)
Values pursued when conditions allow but surrendered when costs are high. Evidence: stated preferences, mild irritation when unmet, no major behavioral cost when overridden.

### Trade-able (compromised under pressure)
Values invoked but routinely traded for other priorities. Evidence: explicit acknowledgment of compromise, behavioral pattern of conceding.

### Explicit-vs-Revealed Gaps
A separate section listing places where stated values diverge from revealed preferences, with interpretation. This is often the most useful part of Phase 1 for downstream phases.

### Seeds for Phase 3 and Phase 4
The synthesis also emits two short lists used by downstream builders:

- **Phase 3 seeds**: 5–10 concept pairs in the form `concept_A ↔ concept_B (relation)`
- **Phase 4 seeds**: 5–10 patterns in the form `Situation → Response (confidence)`

Each seed is grounded in evidence from at least two analysts.

## Quality criteria

A System of Values document is acceptable when:

1. **Every layer placement rests on action evidence**, not just declared preference. A "Core" value with no behavioral data supporting it is suspect.
2. **The four frames substantially agree on Core values**. Genuine disagreement at the Core layer means more analysis is needed; one frame is probably misreading.
3. **Explicit-vs-Revealed Gaps are populated**. If this section is empty, the analysis is too generous to the subject's self-narrative.
4. **AI anchoring has been filtered**. Values endorsed in-the-moment under AI framing are not Core values; the subject must have named or extended them in their own language.
5. **Cross-cluster evidence supports cross-domain values**. A value claimed to apply broadly should have evidence from clusters covering different life domains.

## Pitfalls

### Treating self-statements as values
The subject says "X matters to me." This is one data point. Without behavioral evidence, X is at most a *strong preference*, not a value. Many subjects state values they aspire to but do not actually defend.

### AI-anchored values
After 50+ turns, the subject may have absorbed a value framework from the AI's earlier responses. Statements like "yes, I do believe in X" after the AI has already framed X are weak evidence. Look for the subject *naming X first*.

### Single-cluster overreach
A value defended only in one life domain (e.g., career) is not necessarily a domain-general value. It might be domain-specific. The four frames help here: if affect, narrative, and social-dynamics all see it only in one cluster, label its scope explicitly.

### Stage-specific states presented as stable values
A subject in burnout has different priorities than the same subject at baseline. Phase 1 must distinguish stage-state from stable trait. Use evidence from at least two distinct session stages for any "stable" value claim.

### Pathologizing situational stress
Common early-career anxiety is not a "personality structure of attachment to external validation." Phase 1 must not over-pathologize. The meta-critic explicitly checks for this.

## Pipeline integration

| Concern | Where handled |
|---------|---------------|
| Variable injection (paths, session IDs) | the `/run_pipeline` skill passes inputs via the task prompt when dispatching each subagent |
| Iteration loop | the `/run_pipeline` skill, following `methodology/template/orchestration_protocol.md`, branches on the `meta-critic` verdict, max 3 rounds |
| Quality gate | `meta-critic` validates each analyst's output against its declared contract |
| Cross-framework synthesis | `synthesis-builder` is dispatched after the audit accepts (or escalates); it reads the four analyst reports + `meta_critic.md` and writes `synthesis.md` |
| Output-language consistency | All agents declare `output_language: derived_from_input` and check in their checklists |
| Privacy / neutrality of methodology | `validate_pipeline` skill checks that this document and the subagent files contain no subject-specific content |

## Where Phase 1 fits in product flow

For users with **existing conversation history**:
1. Use `extract_<source>` skill to pull data and standardize format
2. Run the four-frame pipeline (this is Phase 1)
3. Output appears in `personalized/results/profile/system_of_values.md`
4. Phase 2/3/4 builders run, then `profile-compressor` produces `user_profile.md`
5. `load_persona` skill makes the compressed profile available to future conversations

For users with **only forward-going conversations**:
1. Use `save_session` skill at end of each session
2. Once enough sessions accumulate (suggested: ≥5 sessions or ≥10K tokens of user content), run Phase 1 across all saved sessions
3. Downstream phases and the compressed profile update as more sessions are added

## See also

- `methodology/template/pipeline.md` — overall pipeline architecture
- `methodology/template/output_contract_schema.md` — how each agent declares its expected output
- `${CLAUDE_PLUGIN_ROOT}/agents/values-analyst.md` — the direct values-extraction frame
- `${CLAUDE_PLUGIN_ROOT}/agents/synthesis-builder.md` — the subagent that produces `synthesis.md` from the four analyst reports
- `methodology/template/orchestration_protocol.md` — how Phase 1 + synthesis-builder dispatch is sequenced and how the rest of the pipeline is dispatched
- `methodology/template/phase3_knowledge_graph.md` — downstream consumer of Phase 1 seeds
- `methodology/template/phase4_behavioral_model.md` — downstream consumer of Phase 1 seeds
