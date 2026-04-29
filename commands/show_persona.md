---
description: Print the compiled persona profile to the conversation for inspection (viewer; does not load anything into Claude's behavior)
argument-hint: [empty | brief | values | cognitive | graph | model | all | --full]
---

# /show_persona

Print the compiled persona products from `$HOME/.claude/agent-twin/personalized/results/profile/` to the conversation. Default shows `behavior_brief.md`; arguments select specific products or list multi-file products. This is a viewer — for silent loading that adapts responses, use `/load_persona`.

To execute, invoke the `show_persona` skill via the Skill tool. See `skills/show_persona/SKILL.md` for the full specification.
