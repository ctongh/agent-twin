---
name: save_session
description: Snapshot the current Claude Code conversation into the agent-twin project so that it can be analyzed later by the batch pipeline. Idempotent — re-invoking on the same session overwrites, never duplicates. Use at any natural session-end moment.
---

# save_session

When this skill is invoked, capture the *current* Claude Code conversation and write it into the project in the same shape that `extract_gemini` produces, so downstream analyses see a unified format.

The output schema is documented in `skills/extract_gemini/TEMPLATE.md`. Do not redefine it here; just produce conformant files.

## Step 1 — Resolve the session ID

The Claude Code project's session transcripts live (on this user's machine) under a path of the form:

```
~/.claude/projects/<encoded-project-path>/<cc-session-uuid>.jsonl
```

On Windows that is typically `C:/Users/<user>/.claude/projects/<encoded-project-path>/`.

**Resolution order:**

1. List the JSONL files in the project's `~/.claude/projects/<encoded-project-path>/` directory. There is exactly one file matching the *current* session — find it by inspecting the most recently modified JSONL (the active session writes to its file continuously).
2. Extract the CC session UUID from the filename.
3. Derive the save-session ID: `<YYYY-MM-DD>_<first-8-hex-chars-of-cc-session-uuid>`. Use today's date.

This gives a deterministic mapping: the same Claude Code session always maps to the same save-session ID. Re-invoking the skill in the same session overwrites the previous snapshot rather than producing duplicates.

If the JSONL cannot be located (file moved, Claude Code internals changed), fall back to: ask the user to confirm; if they agree, generate a fresh GUID with `python -c "import uuid; print(uuid.uuid4().hex[:8])"` and proceed.

## Step 2 — Create the session directory

```
$HOME/.claude/agent-twin/personalized/saves/session/<save-session-id>/
```

If the directory already exists, that is expected (this is an overwrite). Do not delete the directory or other files within it; only the files this skill writes (`conversation.json`, optionally `annotated.txt`) get overwritten.

## Step 3 — Run the extraction script

**Preflight: check Python is available.** If neither `python --version` nor `py --version` succeeds, tell the user: "Python 3.8+ is required for /save_session. See README Requirements section for install instructions." Then stop without erroring.

The project ships a ready-to-use extraction script at `scripts/autosave_session.py`. Run it with the session JSON piped in:

```bash
echo '{"session_id": "<SESSION_ID>"}' | python scripts/autosave_session.py
```

The script will:
1. Locate the JSONL file under `~/.claude/projects/` using the session ID
2. Extract user/assistant text turns (skipping tool calls and system events)
3. Write `conversation.json` to `$HOME/.claude/agent-twin/personalized/saves/session/<save-session-id>/`

**Do not write a new script inline.** Always use `scripts/autosave_session.py`.

If the script fails (Python not found, JSONL not located, etc.), report the specific error and ask the user to check that Python 3 is installed and accessible.

## Step 4 — Token-aware truncation

If the resulting conversation would be very large, prefer user content over assistant content. Apply this rule **after** building the turns list:

- If total characters across all turns ≤ 500,000: write everything as-is
- If total characters > 500,000:
  - keep `user` content in full (always)
  - for each turn whose `model` exceeds 2,000 chars, truncate to the first 2,000 chars and append `...[truncated]`
  - if still over 500,000 after this, repeat truncation at 1,000 chars
  - record the truncation policy applied as a top-level metadata entry: write a sibling file `meta.yaml` with keys `total_chars`, `truncation_applied`, `truncation_threshold`

The point is to preserve the user side of the conversation losslessly (the analysts' primary signal) while bounding storage.

## Step 5 — Write the standardized files

Write `conversation.json` to:

```
$HOME/.claude/agent-twin/personalized/saves/session/<save-session-id>/conversation.json
```

If the session is large enough to skip annotation in this skill (it would consume considerable tokens), produce `conversation.json` only and tell the user that `annotated.txt` will be produced when they next run the analysis pipeline. If the session is small (< 100,000 chars), proceed to Step 6 and produce `annotated.txt` here.

## Step 6 — (Optional, small sessions) auto-annotate

For small captures, follow the same annotation procedure described in `skills/extract_gemini/SKILL.md` Step 5. Save to `annotated.txt` in the same session directory.

## Step 7 — Confirm

Report to the user:
- the save-session ID
- total turn count
- total character count
- whether truncation was applied
- whether annotation was produced
- path(s) to the file(s)

## Completion checklist

- [ ] Save-session ID is deterministic w.r.t. the Claude Code session UUID
- [ ] The session directory exists; pre-existing unrelated files were not touched
- [ ] `conversation.json` parses against the schema in `skills/extract_gemini/TEMPLATE.md`
- [ ] If truncation was applied, `meta.yaml` records the policy
- [ ] If `annotated.txt` was produced, it conforms to the same TEMPLATE
- [ ] No other session directories were modified

## Idempotency contract

Calling `save_session` twice within the same Claude Code session must produce **identical** files (assuming the second call captures more recent content, the second call simply overwrites — never appends, never creates a sibling directory).

## Out of scope (deliberately)

- Cleanup / retention of old session captures (will be addressed later)
- Cross-session deduplication (different CC sessions may have overlapping content; this is fine)
- Anything that requires network access (capture is local-only)

Saved. Next: run `/run_pipeline` to analyze, or run `/save_session` again later to update.
