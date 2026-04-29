---
name: validate_pipeline
description: Run an umbrella validator over the agent-twin project. Confirms the shareable parts are free of personal data, the agent prompts are well-formed, the gitignore covers personal data correctly, and no skill is malicious. Use before committing methodology/template, agents/, or skills/ changes.
---

# validate_pipeline

When invoked, run each implemented sub-validator in sequence. The pipeline passes only when every implemented sub-validator passes. Validators marked future-work are skipped gracefully — they do not block the run and do not affect the verdict.

## Current scope

**Currently only `methodology_neutrality` is enforced.** The other three validators listed below are planned future work — their files do not yet exist under `validators/`. Running this skill today exercises a single check.

## Sub-validators

The validators live in `skills/validate_pipeline/validators/`. As of writing:

| Validator | Status | What it checks |
|-----------|--------|----------------|
| `methodology_neutrality` | implemented | The shareable framework files (`methodology/`, `agents/`, `skills/*/SKILL.md`, `skills/*/TEMPLATE.md`) reveal *no* identifying information about the subject |
| `agent_format` | future work — not yet implemented | Each agent prompt has the required sections (identity, inputs, methodology, output, checklist, contract) and a parseable `output-contract` YAML block |
| `gitignore` | future work — not yet implemented | `.gitignore` covers all personal-data paths (`personalized/`, etc.) and does not accidentally exclude framework files |
| `malicious_skill` | future work — not yet implemented | Skills do not include obviously dangerous instructions (network exfiltration, mass file deletion, credential access) |

Add a new validator by dropping a markdown file under `skills/validate_pipeline/validators/<name>.md` that follows the validator schema described below.

## Execution protocol

1. Enumerate the validators by listing files under `skills/validate_pipeline/validators/`. Validators that exist as files are run; validators referenced in this SKILL but missing on disk (the future-work entries above) are **skipped gracefully** — keep a `skipped_count` and surface it in the output.
2. For each validator file, read its front matter. Skip files marked `status: planned` or `status: future` (they are stubs without runnable logic). Increment `skipped_count`.
3. Run each implemented validator: read its instruction body, follow its check logic against the project tree.
4. Each validator returns:
   - `pass` — no findings
   - `pass_with_warnings` — soft findings only
   - `fail` — at least one hard finding (each finding has a path, a line range, and a description)
5. Aggregate the results across **only the implemented validators that ran**. The umbrella result is:
   - `pass` if every executed validator returned `pass`
   - `pass_with_warnings` if no validator failed but warnings exist
   - `fail` if any validator failed
6. Never error because a future-work validator is missing on disk. Print `(<skipped_count> future-work validators skipped)` in the summary line.

## Output

Report to the user:

```
validate_pipeline result: <pass | pass_with_warnings | fail>

  <validator-name>: <result>
    <findings, if any, each with file:line and description>

  <validator-name>: <result>
    ...

Summary: N validators, P passed, W warnings, F failures (<S> future-work validators skipped)
```

If any failures, include for each:
- File path (project-relative)
- Line range
- The pattern or content that triggered the failure
- A specific suggestion for the fix

## Validator schema

Each validator is a markdown file with this front matter and structure:

```markdown
---
validator: <name>
status: implemented | planned
severity: hard | soft
scope: [list of project paths it reads]
---

# <validator-name>

## What it checks
[plain prose]

## Detection logic
[step-by-step procedure for the executing agent]

## Failure criteria
[what triggers a hard finding]

## Suggested fixes
[remediation guidance]
```

## Completion checklist

- [ ] Every implemented validator was executed
- [ ] Each validator's findings are surfaced individually (not silently aggregated)
- [ ] The summary reports counts of pass / warnings / failures
- [ ] If any failure occurred, the umbrella result is `fail`

## Out of scope

- Performance / cost analysis of agent prompts (a separate concern)
- Functional correctness of analysis output (that is `meta-critic`'s job, not this skill's)
- Schema migrations between project versions

## Why this skill exists

The validation principle (taken directly from the project owner): *if an agent reads all the methodology files, it should know exactly how to analyze a subject — yet still know nothing about any specific subject.* This skill is the automated enforcement of that principle, and as the project grows the umbrella collects more invariants under the same gate.
