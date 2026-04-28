---
description: Run the umbrella validator over the digital-persona project (privacy / format / safety checks)
---

Execute the digital-persona `validate_pipeline` skill. Follow the SKILL.md below exactly.

Run every implemented sub-validator under `${CLAUDE_PLUGIN_ROOT}/skills/validate_pipeline/validators/`, skip ones marked `status: planned`, and aggregate the results into a single umbrella verdict (`pass` / `pass_with_warnings` / `fail`). Report each validator's findings individually — never silently aggregate.

This command takes no arguments.

@${CLAUDE_PLUGIN_ROOT}/skills/validate_pipeline/SKILL.md
