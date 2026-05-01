---
description: Run meta-critic standalone on a directory of analyst outputs (manual audit entry point — orchestrator handles this automatically inside its loop)
argument-hint: [optional session_id of form YYYY-MM-DD_<hex>, or full analyses_dir path]
---

# /run_meta_critic

Run meta-critic as a standalone audit on an existing analyses directory. The orchestrator already invokes meta-critic inside `/run_pipeline`'s loop; this command is the manual entry point for re-auditing without rebuilding.

To execute, invoke the `run_meta_critic` skill via the Skill tool. See `skills/run_meta_critic/SKILL.md` for the full specification.
