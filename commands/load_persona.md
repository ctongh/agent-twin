---
description: Load the user's compiled persona profile (Static / Cognitive / Values / Knowledge Graph / Behavioral) into the current session so responses adapt
---

Execute the agent-twin `load_persona` skill. Follow the SKILL.md below exactly.

Read every available product under `${CLAUDE_PLUGIN_ROOT}/personalized/results/profile/`. Build the persona briefing under ~3,000 tokens, with a specific (not generic) "Adjustments for this assistant" section. Print the briefing to the user — they need to see it before continuing. Then let it shape every subsequent response in this session.

If a global `CLAUDE.md` directive conflicts with the briefing, the global directive wins; surface the conflict in your acknowledgment.

This command takes no arguments.

@${CLAUDE_PLUGIN_ROOT}/skills/load_persona/SKILL.md
