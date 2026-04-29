---
description: Run the full agent-twin analysis pipeline on a saved session — Phase 1 (four analysts in parallel + meta-critic loop + synthesis-builder), then Phase 2/3/4 builders, then behavior-brief-generator
argument-hint: [optional session_id of form YYYY-MM-DD_<8hex>, or empty for most-recent]
---

# /run_pipeline

Run the full agent-twin analysis pipeline on a captured session. Produces the four detailed products plus `behavior_brief.md`. Proceeds without waiting for confirmation.

To execute, invoke the `run_pipeline` skill via the Skill tool. See `skills/run_pipeline/SKILL.md` for the full specification.
