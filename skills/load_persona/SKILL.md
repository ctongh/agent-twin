---
name: load_persona
description: Load the user's behavior brief (behavior_brief.md) into the current Claude session so responses adapt to who the user actually is. Invoke explicitly at session start when you want persona-aware assistance.
---

# load_persona

When invoked, read the behavior brief at `$HOME/.claude/agent-twin/personalized/results/profile/behavior_brief.md` and from that point forward let it shape every response in the session.

This skill is invoked **explicitly** — the persona must not auto-load, so the before/after difference is perceptible.

## What this skill reads

A single file: `$HOME/.claude/agent-twin/personalized/results/profile/behavior_brief.md`.

This file is the output of the `behavior-brief-generator` agent (the final stage of `/run_pipeline`). It is a ≤80-line instruction set written entirely from Claude's perspective, with four sections:

1. **背景** — who the user is and their context (3–5 sentences, plain language)
2. **合作方式** — 10–15 imperative instructions: what to do and what not to do
3. **禁區** — absolute prohibitions (5–8 items; most important section)
4. **近期狀況** — current situational context, if present in the source data

The detailed batch-layer products (`system_of_values.md`, `cognitive_patterns.md`, `knowledge_graph/`, `behavioral_model/`) are **not read** by this skill.

## Step 1 — Read behavior_brief.md

Read the file at `$HOME/.claude/agent-twin/personalized/results/profile/behavior_brief.md`.

If the file does not exist, report:

> `behavior_brief.md` does not exist yet. Run `/run_pipeline` on a captured session first, then invoke `/load_persona` again.

If the file exists but is older than the most recent session under `$HOME/.claude/agent-twin/personalized/saves/session/`, surface a soft warning:

> The behavior brief is older than your most recent saved session. Consider re-running `/run_pipeline` to update it.

Do not block on the warning — proceed with the existing brief unless the user asks to refresh.

## Step 2 — Acknowledge and internalize

Write one short line to confirm the brief is active:

> Write one brief line — in the user's language — confirming the brief is now active. Keep it low-key; the persona should be felt, not announced.

Do **not** print the brief contents to the conversation. The brief is operational context, not a document to review. If the user wants to inspect it, they can read `$HOME/.claude/agent-twin/personalized/results/profile/behavior_brief.md` directly.

From this point, every response in the session should follow the instructions in the brief. The **禁區** section takes highest priority.

## Step 3 — Conflict with global config

If the user's global Claude config (`~/.claude/CLAUDE.md` or a project-level `CLAUDE.md`) contradicts something in the brief:

1. **Global / project CLAUDE.md takes precedence.**
2. The brief **supplements** — it adds behavioral context, not new rules.
3. When a conflict is load-bearing for the current response, note it briefly ("Your config prefers X; following that over the brief").

## Out of scope

- Reading the detailed products. The behavior-brief-generator does that during pipeline build.
- Auto-loading on session start. Intentional: explicit invocation keeps the before/after visible.
- Editing or updating `behavior_brief.md`. Updates come from `/run_pipeline`, not in-conversation.

## Completion checklist

- [ ] `behavior_brief.md` was read in full
- [ ] If the file was missing or stale, the user was informed
- [ ] A one-line acknowledgment was written (brief was NOT printed to conversation)
- [ ] No detailed products were loaded
