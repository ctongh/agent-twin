# Design Notes

> **What this file is.** Rationale for the agent-twin pipeline's architectural choices.
> **What it is not.** A protocol Claude executes, a step-by-step recipe, or a file path index. It contains *no* dispatch instructions, *no* output paths to follow, *no* invocations.
>
> Execution lives in the SKILL.md files under `skills/`. Agent behavior lives in the agent files under `agents/`. This file explains the *intent* behind those files. If you want to know what an agent does, read `agents/<name>.md`. If you want to know how a command runs, read `skills/<name>/SKILL.md`.

## Where the source of truth is

`skills/<name>/SKILL.md` is the **single source of truth** for what each command does. `commands/<name>.md` files are thin routers. `agents/<name>.md` files are agent system prompts. This file (`design_notes.md`) is rationale. `output_contract_schema.md` is the only other methodology file — it defines a schema that the meta-critic agent reads at runtime.

If you find a contradiction between this file and a SKILL.md, the SKILL.md wins. Update this file to match.

---

## Why four phases

The pipeline asks four different questions about the subject, and a single agent that tries to answer all four at once tends to muddle them:

| Phase | Question | Why this question, separately |
|---|---|---|
| 1 | *What* matters and how much? | Values are revealed by what the subject defends under cost. Reading them off declared statements alone produces aspirational lists, not actual hierarchies. |
| 2 | *How* does the subject think? | Cognitive style — the subject's metaphors, argument shape, register-switching — operates beneath value-talk and is best read directly off the language. |
| 3 | How are concepts connected? | A graph surfaces second-order structure: hub concepts, tension edges, contradictions held together. Lists hide this. |
| 4 | What will the subject do in situation X? | Predictions need intensity stratification (mild / moderate / severe) and modulator awareness, neither of which falls out of values or graphs cleanly. |

Phase 1 is the foundation: its synthesis emits seeds (concept pairs, situation→response patterns) that Phase 3 and Phase 4 expand. Phase 2 runs independently against the source text — it has no input dependency on Phase 1.

## Why only Phase 1 is meta-critic'd

Phase 1's output is interpretive — claims about what a subject fears, defends, prioritizes. Interpretation is where analysts go wrong: pathologizing situational stress as personality, treating in-the-moment AI-anchored agreement as the subject's settled view, generalizing single-cluster evidence into stable traits. The meta-critic exists to catch these errors before they propagate downstream.

Phase 2/3/4 are deterministic expansions. Phase 2 reports language-level statistics (lexical fields, metaphor density, question types) that the subject can verify by reading their own conversations side by side. Phase 3 reshapes Phase 1 findings into a graph form — every node and edge must be traceable to an analyst report. Phase 4 expands Phase 1 seeds into structured patterns — fabrication is constrained because the seed itself comes from the audited synthesis.

Subject self-review is the validation step for Phase 2/3/4. Adding a meta-critic loop on top would burn tokens without adding signal.

## The four-frame design (Phase 1)

A single "values agent" that reads a conversation tends to default to declared values and miss the gap between what the subject says matters and what they actually defend. Triangulation across four lenses surfaces that gap:

| Lens | What it catches that the others miss |
|---|---|
| Affect | Values protected by emotional reaction (fear, anger, crying often signals a touched value) |
| Social dynamics | Values revealed by behavior under power asymmetry and status pressure |
| Values (direct) | Refusals, persistence under cost, explicit principles |
| Narrative | Values implicit in the subject's self-story and identity language |

Convergence across frames produces high-confidence findings. Divergence is itself informative — a value defended in narrative but not in behavior is data, not a contradiction to resolve.

The four analysts must run from independent contexts. If they shared a single context (e.g., one agent role-playing all four), the cross-frame triangulation collapses into one synthetic perspective. That is why `/run_pipeline` dispatches them as separate Claude Code subagents.

## The AI-anchoring filter

After 30+ turns of conversation, the subject often picks up the AI's vocabulary and framings. A statement like "yes, I do believe in autonomy" *after* the AI has just framed the conversation around autonomy is weak evidence — the subject may simply be agreeing.

The filter: **a framing counts as the subject's only if they introduced it or extended it in their own words.** Statements that only echo the AI's prior framing are downgraded or excluded.

This is the single most important methodology rule. Without it, Phase 1 reports are dominated by the AI's own framing reflected back. The meta-critic explicitly samples for anchoring residue and downgrades analysts whose evidence is more than 30% anchored.

## The closing-cluster discipline

The final topic cluster of an annotated session is structurally a magnet for AI-anchored material — it is where the AI summarizes, ranks, or frames, and the subject reviews and reformulates. Quotes from the closing cluster should not serve as the *primary* evidence for any finding rated medium or high. They may corroborate findings whose primary evidence sits in earlier clusters.

This rule is downstream of the AI-anchoring filter — it generalizes the same concern to a positional rule that is mechanically checkable.

## Evidence hierarchy

Not all evidence is equal. The analysts and the synthesis-builder rank evidence in this order, strongest first:

1. **Pre-rational signals** — body symptoms, outbursts, crying, panic. Hardest to fabricate or retroactively rationalize.
2. **Concrete actions described** — what the subject *did*, with situational detail.
3. **Direct correction of, or pushback against, the AI** — escapes anchoring by definition.
4. **Cross-cluster recurrence** — themes that surface independently across multiple unrelated topics.
5. **Single self-disclosure** — useful but one data point.
6. **Statements echoing the AI's prior framing** — lowest weight; treat as anchored.

A finding that rests entirely on tier 5 or 6 evidence does not earn high confidence, no matter how clear the statement looks.

## Cluster-boundary discipline

In long sessions, subject behavior shifts by topic. Treating turns 1–30 (one topic) and turns 80–110 (a different topic) as a uniform stream conflates context-specific states with stable traits.

The rule: **a finding labeled high confidence must show evidence from at least two distinct topic clusters, with quotes from those clusters in the finding's evidence block** — narrative prose gesturing at cross-cluster support does not satisfy the rule. Single-cluster patterns get medium confidence and an explicit scope note.

This is what topic-cluster annotation is for. Without cluster boundaries, "the subject is X" overfits to whichever cluster dominated the session.

## Output language matches the source

Every product — analyses, synthesis, system of values, cognitive patterns, knowledge graph nodes, behavior patterns, the final brief — is written in the dominant language of the source conversation. If the user wrote in Traditional Chinese, every report is in Traditional Chinese. Translation loses the subject-coined vocabulary and metaphor systems that Phase 2 and the narrative analyst depend on.

Each agent declares `output_language: derived_from_input` in its output contract and verifies it in its checklist. The meta-critic flags language mismatch as a hard failure.

## No new findings in the audit layer

The meta-critic validates output contracts, scans for anchoring residue, and flags cross-agent contradictions. It does not produce its own analysis of the subject. Anything that looks like a new claim about the subject in a meta-critic report is a violation — that work belongs back in the analysts.

This rule keeps the audit honest. If the meta-critic could insert its own findings, the loop would converge on the meta-critic's preferences rather than what the analysts triangulated.

## Single-session bias

A single session is biased by topic, mood, and the subject's framing relationship to that particular AI on that particular day. Stable claims about the subject require multiple sessions. The pipeline can run on a single session — it will produce all four products — but the subject and any downstream consumer should treat first-pass results as provisional until cross-session evidence accumulates.

Cross-session integration (concept merging, evidence accumulation, conflict resolution, stability tagging) is the hardest unsolved part of this pipeline. The current approach is to run per-session and surface the integration as a roadmap item.

## The compressed brief

The conversation layer (`/load_persona`) reads exactly one file: `behavior_brief.md`. The detailed products (system_of_values, cognitive_patterns, knowledge_graph, behavioral_model) stay on disk for cross-session integration, audit, and direct subject inspection.

The brief is written entirely as instructions to Claude — every sentence must be something Claude can act on in the next response. Analytical jargon is banned ("intellectualization defense", "external validation dependency", "value hierarchy") unless the source conversation itself uses those terms. The brief is a colleague handover, not an academic report. This avoids "prompt pollution" — the assistant adopting a stilted analytical register after loading the brief.

The brief is silent — `/load_persona` does not print it. The brief shapes responses; it is not a document for the user to review during loading. A separate command exists if the user wants to inspect the brief contents.
