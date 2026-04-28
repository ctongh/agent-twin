---
description: Snapshot the current Claude Code conversation into the agent-twin project (idempotent; overwrites the same session)
---

Execute the agent-twin `save_session` skill. Follow the SKILL.md below exactly.

Resolve the session ID deterministically from the active Claude Code JSONL as Step 1 specifies — do not generate a fresh GUID unless the JSONL truly cannot be located.

This command takes no arguments. If `$ARGUMENTS` is non-empty, treat it only as a hint for the user's intent and ignore it for the actual ID derivation.

@${CLAUDE_PLUGIN_ROOT}/skills/save_session/SKILL.md
