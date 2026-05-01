---
name: save_session
description: Snapshot the current Claude Code conversation into the agent-twin project so that it can be analyzed later by the batch pipeline. Idempotent — re-invoking on the same session overwrites, never duplicates. Use at any natural session-end moment.
---

# save_session

When this skill is invoked, capture the *current* Claude Code conversation and write it into the project in the same shape that `extract_gemini` produces, so downstream analyses see a unified format.

The output schema is documented in `skills/extract_gemini/TEMPLATE.md`. Do not redefine it here; just produce conformant files.

## Step 0 — Preflight: Python availability

This whole skill ultimately depends on Python: Step 3 invokes `scripts/autosave_session.py`, and Step 1's fallback path (when the Claude Code session UUID cannot be resolved from `~/.claude/projects/`) generates a GUID via `python -c "import uuid; print(uuid.uuid4().hex[:12])"`. Verify Python is reachable **before** any Python-dependent operation runs.

Try `python3 --version` first, then `python --version`, then `py --version` (Windows fallback). Record which command succeeded — Steps 1 and 3 should reuse it. If none succeed, tell the user — in their language — "Python 3.8+ is required for /save_session. See README Requirements section for install instructions." Then stop without erroring; do not proceed to Step 1.

## Step 1 — Resolve the session ID

The Claude Code project's session transcripts live (on this user's machine) under a path of the form:

```
~/.claude/projects/<encoded-project-path>/<cc-session-uuid>.jsonl
```

On Windows that is typically `C:/Users/<user>/.claude/projects/<encoded-project-path>/`.

**Resolution order:**

1. List the JSONL files in the project's `~/.claude/projects/<encoded-project-path>/` directory. There is exactly one file matching the *current* session — find it by inspecting the most recently modified JSONL (the active session writes to its file continuously).
2. Extract the CC session UUID from the filename.
3. Derive the save-session ID: `<YYYY-MM-DD>_<first-12-hex-chars-of-cc-session-uuid>`. Use the **first-write date** — i.e. the date the session was first captured. If a directory ending in `_<session-prefix>` already exists under `saves/session/`, reuse it (sessions spanning midnight stay in the original date's directory; the autosave hook only stamps a new date on the very first write). (12 hex chars gives ~1/280-trillion collision probability — collision-resistant for typical use — versus 8 chars at ~1/4-billion.)

This gives a deterministic mapping: the same Claude Code session always maps to the same save-session ID. Re-invoking the skill in the same session overwrites the previous snapshot rather than producing duplicates.

If the JSONL cannot be located (file moved, Claude Code internals changed), fall back to: ask the user to confirm; if they agree, generate a fresh GUID with `python -c "import uuid; print(uuid.uuid4().hex[:12])"` and proceed.

## Step 2 — Create the session directory

```
$HOME/.claude/agent-twin/personalized/saves/session/<save-session-id>/
```

If the directory already exists, that is expected (this is an overwrite). Do not delete the directory or other files within it; only the files this skill writes (`conversation.json`, optionally `annotated.txt`) get overwritten.

## Step 3 — Run the extraction script

The Python preflight is already done in Step 0 — reuse the interpreter (`python3` / `python` / `py`) that succeeded there.

The project ships a ready-to-use extraction script at `scripts/autosave_session.py`. Run it with the Claude Code session UUID piped in as JSON (prefer `python3` on Linux/macOS; use `py` only as a Windows fallback):

```bash
echo '{"session_id": "<CC_SESSION_UUID>"}' | python3 scripts/autosave_session.py
```

`<CC_SESSION_UUID>` is the **Claude Code session UUID** — the filename stem of the active `~/.claude/projects/<encoded-project-path>/<UUID>.jsonl` transcript. **It is NOT the `<save-session-id>` (`YYYY-MM-DD_<prefix>`) derived in Step 1.** The script greps for the JSONL by this UUID; passing the save-session-id here will fail to locate any transcript.

The script will:
1. Locate the JSONL file under `~/.claude/projects/` using the Claude Code session UUID
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
