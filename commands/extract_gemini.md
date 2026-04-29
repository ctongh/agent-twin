---
description: (legacy/optional) Capture a Gemini share-link conversation and prepare it (with topic-cluster annotation) for the agent-twin analysis pipeline. Primary capture is /save_session or /counselor.
argument-hint: [optional Gemini share URL]
---

# /extract_gemini

**Legacy / optional capture path.** The primary capture flow for agent-twin is `/save_session` (snapshots the current Claude Code session) or `/counselor` (guided questionnaire). Use `/extract_gemini` only if you specifically want to import a Gemini share-link conversation.

To execute, invoke the `extract_gemini` skill via the Skill tool. See `skills/extract_gemini/SKILL.md` for the full specification.
