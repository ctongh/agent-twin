---
description: Run the full digital-persona analysis pipeline on a saved session — Phase 1 (4 analysts in parallel + meta-critic loop + synthesis-builder), then Phase 2/3/4 builders, then profile-compressor → user_profile.md.
argument-hint: [optional session_id of form YYYY-MM-DD_<8hex>, or empty for most-recent]
---

Execute the digital-persona `run_pipeline` skill. Follow the SKILL.md below exactly.

## Argument resolution

Parse `$ARGUMENTS` as follows:

- **Empty** → use the skill's default: pick the most recently modified subdirectory under `${CLAUDE_PLUGIN_ROOT}/personalized/saves/session/` and use it as `session_id`. Confirm the choice with the user before dispatching.
- **Matches `YYYY-MM-DD_<8hex>`** → resolve to `${CLAUDE_PLUGIN_ROOT}/personalized/saves/session/<id>/`.
- **Looks like a path** → infer `session_id` from the trailing directory name.

The skill auto-resolves `input_path`, `source_json_path`, `analyses_dir`, `profile_dir`, `agent_prompts_dir`, and `build_timestamp`.

## Dispatch reminders

- The pipeline runs **at top-level** in this conversation because Claude Code subagents do not have access to the `Task` tool. The skill issues every `Task` dispatch itself; do not delegate the orchestration to a subagent.
- Phase 1 Step 1 dispatches all four analysts in a **single message** (parallel fan-out):

  ```
  Task(subagent_type="affect-analyst", description="...", prompt="...")
  Task(subagent_type="social-dynamics-analyst", description="...", prompt="...")
  Task(subagent_type="values-analyst", description="...", prompt="...")
  Task(subagent_type="narrative-analyst", description="...", prompt="...")
  ```

- On `iterate`, re-dispatch **only** the analysts marked `needs_revision`; analysts that passed carry forward unchanged.
- `synthesis-builder` is a separate stage dispatched after the loop exits (`accept` or `escalate`). It writes both `analyses/synthesis.md` and `results/profile/system_of_values.md`.
- Before Phase 3 / Phase 4 dispatch, clear `<profile_dir>/knowledge_graph/` and `<profile_dir>/behavioral_model/` unless `existing_graph` / `existing_model` were passed as `true` (cross-session merge mode).
- The orchestration protocol governing every dispatch is `${CLAUDE_PLUGIN_ROOT}/methodology/template/orchestration_protocol.md` — read it if uncertain about variable substitution or stale-output handling.

## Pre-flight gate

Before any dispatch, surface a summary to the user (per Step 2 of the skill) and wait for confirmation. Pipeline runs are expensive (~10 minutes typical for a single session). If `<profile_dir>/` already contains products from a different session, warn explicitly before overwriting.

## Surfacing the result

After completion, surface (per Step 5 of the skill):

- Phase 1 iterations + escalation flag + per-analyst final verdict
- Per-phase product paths (`system_of_values.md`, `cognitive_patterns.md`, `knowledge_graph/`, `behavioral_model/`, `user_profile.md`)
- `user_profile.md` line count
- Any caveats from the synthesis Pipeline Caveats section (do **not** silently drop them)

End with the next-action recommendation (per Step 6 of the skill) — typically "Open a new conversation and run `/load_persona`."

@${CLAUDE_PLUGIN_ROOT}/skills/run_pipeline/SKILL.md
