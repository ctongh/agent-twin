---
description: Run meta-critic standalone on a directory of analyst outputs (manual audit entry point — orchestrator handles this automatically inside its loop)
argument-hint: [optional session_id of form YYYY-MM-DD_<8hex>, or full analyses_dir path]
---

Execute the agent-twin `run_meta_critic` skill. Follow the SKILL.md below exactly.

## Argument resolution

Parse `$ARGUMENTS` as follows:

- **Empty** → use the skill's default: pick the most recently modified subdirectory under `${CLAUDE_PLUGIN_ROOT}/personalized/saves/session/` and use its `analyses/` directory. Confirm the choice with the user before dispatching.
- **Matches `YYYY-MM-DD_<8hex>`** → resolve to `${CLAUDE_PLUGIN_ROOT}/personalized/saves/session/<id>/analyses/`, with `session_id = <id>`.
- **Looks like a path** → use as `analyses_dir` directly; infer `session_id` from the parent directory name.

Default `iteration = 1` (this is a standalone audit, not part of an orchestrator-driven loop).

## Dispatching the agent

The `meta-critic` agent is a **registered Claude Code subagent** distributed inside this plugin at `${CLAUDE_PLUGIN_ROOT}/agents/meta-critic.md`. To dispatch it:

1. Issue a Task call with `subagent_type: "meta-critic"` (Claude Code loads the system prompt from the agent file automatically — do **not** include it in the task prompt).
2. The task prompt is a short message providing the input variables (`ANALYSES_DIR`, `AGENT_PROMPTS_DIR=${CLAUDE_PLUGIN_ROOT}/agents/`, `SOURCE_DATA_PATH`, `SYNTHESIS_PATH`, `SESSION_ID`, `ITERATION`).
3. Save the agent's returned report text to `<analyses-dir>/meta_critic.md`.
4. Before overwriting an existing `meta_critic.md`, rename the prior one to `meta_critic.<ISO-timestamp>.md` per Step 4 of the skill (manual audit reports are kept as history; only the orchestrator-driven loop overwrites freely).

## Surfacing the verdict

After the audit completes, surface to the user:
- Loop decision (`accept` / `iterate` / `escalate`)
- Per-analyst verdicts (`pass` / `pass_with_warnings` / `needs_revision` / `unrecoverable`)
- Top concerns (anchoring residue, blind spots, calibration flags)
- Path to the saved report
- A next-action recommendation per the skill's Step 6 table

Do **not** re-dispatch analysts from this command — that is the orchestrator's role. This command is read-only with respect to analyst outputs.

@${CLAUDE_PLUGIN_ROOT}/skills/run_meta_critic/SKILL.md
