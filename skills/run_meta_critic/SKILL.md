---
name: run_meta_critic
description: Run meta-critic on a directory of analyst outputs without going through the full pipeline. Use when you want a standalone audit — e.g. on analyses that are already complete, or to re-check a prior pipeline run. The orchestrator already invokes meta-critic automatically as part of its loop; this skill is the manual entry point.
---

# run_meta_critic

This skill is a thin wrapper that dispatches the `meta-critic` Claude Code subagent (defined in `${CLAUDE_PLUGIN_ROOT}/agents/meta-critic.md`) against a specified analysis directory. The agent does the work; this skill just resolves inputs and surfaces the verdict.

## When to use this vs. the automatic invocation

| Situation | Use |
|-----------|-----|
| Running the full pipeline | The orchestrator handles meta-critic in its loop — no need to call this skill |
| Auditing analyses that were produced outside the orchestrator | This skill |
| Re-auditing after manually editing an analyst report | This skill |
| Cross-checking historical analyses against an updated `meta-critic.md` prompt | This skill |

## Inputs

When invoked, ask the user (or accept arguments) for:

| Input | Description | Default |
|-------|-------------|---------|
| `analyses_dir` | Directory containing the analyst reports to audit | the most recent session under `personalized/saves/session/` |
| `session_id` | The session ID for traceability | inferred from `analyses_dir` (parent directory name) |
| `iteration` | Iteration number — meta-critic enforces escalation at iteration 3 | `1` if running standalone |

The skill auto-resolves:
- `agent_prompts_dir` → `${CLAUDE_PLUGIN_ROOT}/agents/`
- `source_data_path` → `<session-dir>/annotated.txt`
- `synthesis_path` → `<analyses-dir>/synthesis.md` if it exists, else empty

## Step 1 — Resolve inputs

If the user did not specify `analyses_dir`, list `personalized/saves/session/` and pick the most recently modified subdirectory's `analyses/`. Confirm the choice with the user before proceeding.

Verify required files exist:
- At least the four analyst reports (`affect.md`, `social.md`, `values.md`, `narrative.md`)
- The source data (`annotated.txt`)

If files are missing, list what is missing and stop.

## Step 2 — (Optional) review the meta-critic prompt

The agent file `${CLAUDE_PLUGIN_ROOT}/agents/meta-critic.md` is loaded automatically by Claude Code when you dispatch the `meta-critic` subagent — you do **not** need to substitute variables into the prompt body yourself. Read it only if you want to confirm the audit dimensions or its `output-contract` block before dispatching.

## Step 3 — Dispatch the agent

Issue a Task call with `subagent_type: "meta-critic"` and a task prompt that lists these input variables (Claude Code loads the system prompt from the agent file automatically — do not re-include it):

| Variable | Value |
|----------|-------|
| `ANALYSES_DIR` | resolved above |
| `AGENT_PROMPTS_DIR` | `${CLAUDE_PLUGIN_ROOT}/agents/` |
| `SOURCE_DATA_PATH` | `<session-dir>/annotated.txt` |
| `SYNTHESIS_PATH` | `<analyses-dir>/synthesis.md` if exists, else empty |
| `SESSION_ID` | resolved above |
| `ITERATION` | as specified, default `1` |

Wait for completion.

## Step 4 — Save the audit report

Save the agent's output to `<analyses-dir>/meta_critic.md`. If a previous `meta_critic.md` exists, **rename** the prior one to `meta_critic.<timestamp>.md` before overwriting (manual audit reports are kept as history; only the orchestrator-driven loop overwrites freely).

## Step 5 — Surface the verdict to the user

Read the saved report and surface the key findings:

1. **Loop decision** — `accept` / `iterate` / `escalate`
2. **Per-analyst verdicts** — pass / pass_with_warnings / needs_revision / unrecoverable
3. **Top concerns** — anchoring residual rate, blind spots, confidence-calibration flags
4. **Path** to the full audit report

## Step 6 — Recommend next action

Based on the verdict:

| Verdict | Recommendation |
|---------|----------------|
| `accept` | "Phase 1 output is sound. The downstream phases can use this synthesis." |
| `iterate` (any analyst needs revision) | "These analysts need revision — re-run the full pipeline via `/run_pipeline` (the orchestrator handles the iteration loop) or hand-edit the analyst report and re-invoke this skill to re-audit." |
| `escalate` | "Pipeline cannot self-correct. Review the audit report's escalation notes — human judgment required." |

Do not automatically re-dispatch analysts from this skill — that is the orchestrator's job. This skill is read-only with respect to analyst outputs.

## Completion checklist

- [ ] Inputs were resolved (or asked of the user) before dispatching
- [ ] All required source files exist
- [ ] Agent dispatch used the correct variable substitution
- [ ] Prior `meta_critic.md` (if any) was preserved as `meta_critic.<timestamp>.md`
- [ ] The verdict was surfaced clearly to the user
- [ ] No analyst report was modified
- [ ] No re-dispatch of analysts (that is orchestrator's role)

## Why this exists

The orchestrator is the right runner for the full pipeline; it handles iteration and synthesis automatically. But after a pipeline has finished, users sometimes want to *re-audit* — perhaps because the meta-critic prompt was updated, or because they hand-edited a report to fix something. Running the orchestrator from scratch in those cases is wasteful. This skill is the lightweight alternative.
