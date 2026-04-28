---
description: Capture a Gemini share-link conversation and prepare it (with topic-cluster annotation) for the agent-twin analysis pipeline
argument-hint: [optional Gemini share URL]
---

Execute the agent-twin `extract_gemini` skill. Follow the SKILL.md below exactly, step by step.

If `$ARGUMENTS` is non-empty, treat it as the Gemini share URL the user wants to capture (skip asking for it in Step 2). Otherwise ask the user for the URL as the skill directs.

@${CLAUDE_PLUGIN_ROOT}/skills/extract_gemini/SKILL.md
