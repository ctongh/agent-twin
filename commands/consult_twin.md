---
description: Consult your persona twin from a working session without polluting this session's context. Pass any question; the twin reads its profile and your recent session, then responds in your voice.
argument-hint: <free-form question>
---

# /consult_twin

Consult the persona twin in its own sub-context. Unlike `/load_persona`, the brief never enters this session's prompt — the twin reads `behavior_brief.md` and the recent session transcript inside a Task dispatch, then returns its first-person response.

To execute, invoke the `consult_twin` skill via the Skill tool. See `skills/consult_twin/SKILL.md` for the full specification.
