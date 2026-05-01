---
name: validate_pipeline
description: Run an umbrella validator over the agent-twin project. Confirms the shareable parts are free of personal data, the agent prompts are well-formed, the gitignore covers personal data correctly, and no skill is malicious. Use before committing methodology/template, agents/, or skills/ changes.
---

# validate_pipeline

When invoked, run each implemented sub-validator in sequence. The pipeline passes only when every implemented sub-validator passes. Validators marked `planned` (documented in this SKILL but not yet implemented as files on disk) are skipped gracefully — they do not block the run and do not affect the verdict.

## Current scope

**Currently only `methodology_neutrality` is enforced.** The other three validators listed below are marked `status: planned` — they are documented in the registry but their files do not yet exist under `validators/`, so they are skipped gracefully. Running this skill today exercises a single check.

## Sub-validators

The validators live in `skills/validate_pipeline/validators/`. The table below is the **canonical, table-driven validator registry** — Step 1 of the execution protocol parses these rows to determine which validators to look for. As of writing:

| Validator | Status | What it checks |
|-----------|--------|----------------|
| `methodology_neutrality` | implemented | The shareable framework files (`methodology/`, `agents/`, `skills/*/SKILL.md`, `skills/*/TEMPLATE.md`) reveal *no* identifying information about the subject |
| `agent_format` | planned | Each agent prompt has the required sections (identity, inputs, methodology, output, checklist, contract) and a parseable `output-contract` YAML block |
| `gitignore` | planned | `.gitignore` covers all personal-data paths (`personalized/`, etc.) and does not accidentally exclude framework files |
| `malicious_skill` | planned | Skills do not include obviously dangerous instructions (network exfiltration, mass file deletion, credential access) |

Status semantics:
- `implemented` — the validator has a corresponding markdown file under `validators/<name>.md` and is run on every invocation.
- `planned` — the validator is documented in this table but its file does not yet exist on disk. It is skipped gracefully and counts toward `skipped_count`.

Add a new validator by (a) adding its row to the table above with `status: implemented` (or `planned` if you are recording the intent before writing the file), and (b) dropping a markdown file under `skills/validate_pipeline/validators/<name>.md` that follows the validator schema described below.

## Execution protocol

1. **Enumerate validators from the table, not the directory.** Parse the **Sub-validators** table above (treat each markdown row whose first column is a validator name as one entry; ignore the header and divider rows). For each table entry, record `(name, status)`. This table-driven approach is what makes `skipped_count` meaningful — file-based enumeration cannot see entries that are documented but missing on disk.
2. For each table entry, decide what to do based on `status` and on whether `skills/validate_pipeline/validators/<name>.md` exists:
   - `status: implemented` AND file exists → run it (proceed to step 3).
   - `status: implemented` BUT file missing on disk → treat as a **broken registry entry**: skip with a warning naming the missing file, and increment `skipped_count`. (Either fix the table or add the file before the next run.)
   - `status: planned` → skip gracefully without warning; increment `skipped_count`. The corresponding file may or may not exist; either way, no logic is run.
3. For each validator scheduled to run, read the validator file's front matter (which should also declare `status: implemented`) and instruction body, then follow its check logic against the project tree.
4. Each validator returns:
   - `pass` — no findings
   - `pass_with_warnings` — soft findings only
   - `fail` — at least one hard finding (each finding has a path, a line range, and a description)
5. Aggregate the results across **only the implemented validators that ran**. The umbrella result is:
   - `pass` if every executed validator returned `pass`
   - `pass_with_warnings` if no validator failed but warnings exist
   - `fail` if any validator failed
6. Never error because a planned validator is missing on disk. Print `(<skipped_count> planned validators skipped)` in the summary line.

## Output

Report to the user:

```
validate_pipeline result: <pass | pass_with_warnings | fail>

  <validator-name>: <result>
    <findings, if any, each with file:line and description>

  <validator-name>: <result>
    ...

Summary: N validators, P passed, W warnings, F failures (<S> planned validators skipped)
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
