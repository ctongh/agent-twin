---
name: extract_gemini
description: Capture a conversation from a Gemini share link and prepare it (with topic-cluster annotation) for the agent-twin analysis pipeline. Use when the user wants to import a Gemini conversation into the persona project.
---

# extract_gemini

> **Legacy / optional capture path.** This SKILL imports a Gemini share-link conversation. The primary capture path for agent-twin is `/save_session` (snapshots the current Claude Code session) or `/counselor` (guided questionnaire). Use `/extract_gemini` only if you specifically want to import a Gemini conversation.

When this skill is invoked, walk the user through extracting a Gemini conversation and producing the three files the analysis pipeline needs:

| File | Purpose |
|------|---------|
| `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/conversation.json` | Raw turn-by-turn capture |
| `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/annotated.txt` | Same content with topic-cluster headers |
| `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/session_meta.json` | Capture metadata so `/run_pipeline` can scan the queue |

The format spec lives in `skills/extract_gemini/TEMPLATE.md`. Real samples live in `skills/extract_gemini/samples/`.

### `session_meta.json` schema

This file mirrors what the autosave Stop hook (`scripts/autosave_session.py`) writes for `/save_session` captures, so `/run_pipeline`'s queue-scan logic can treat both capture paths uniformly. Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | The full save-session ID (`YYYY-MM-DD_<12-hex>`). |
| `turn_count` | integer | Number of `{order, user, model}` entries in `conversation.json`. |
| `saved_at` | string (ISO-8601) | When this capture was written. Use the value of `datetime.now().isoformat()`. |
| `source` | string | Capture path tag — set to `"extract_gemini"` so future tooling can distinguish capture origins from autosave (`"save_session"`). |

Any future capture path (e.g. `/extract_chatgpt`) must write the same schema with its own `source` value.

## Step 1 — Generate session ID and create directory

Generate a session ID with format `YYYY-MM-DD_<12-char-hex-guid>` (matching `/save_session`'s convention). You can produce the GUID with:

```bash
python3 -c "import uuid; print(uuid.uuid4().hex[:12])"
```

Create the directory:

```
$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/
```

Tell the user the session ID you generated.

### Existing-directory handling

A 12-hex GUID is collision-resistant for typical use (~1/280-trillion space), but a re-extract on the same day can still collide if the user reuses an ID intentionally. Before writing into an existing `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/`:

1. If the directory exists and contains files (`conversation.json`, `annotated.txt`, or an `analyses/` subdir), **stop** and ask the user. Two acceptable choices:
   - **Generate a fresh session ID** (default; safer). Re-run Step 1 with a new GUID. Any prior pipeline outputs at the old ID are preserved untouched.
   - **Overwrite explicitly.** The user must confirm. Then `rm -rf` only the files this skill is about to write (`conversation.json`, `annotated.txt`); leave any sibling `analyses/` directory intact (those belong to the pipeline, not this skill).
2. If the directory exists but is empty, just write into it.

Do not silently overwrite. The session ID is the de-facto join key for downstream products; collisions create silent data-corruption risk.

## Step 2 — Provide capture instructions

Ask the user for a Gemini share link (a URL like `gemini.google.com/share/<id>`). If they don't have one yet, instruct them to open the conversation in Gemini and click the share button.

**The scraper is browser-only.** `scraper.js` uses `window`, `document`, and `MutationObserver` — it is **not** runnable as `node scraper.js` from a terminal. The user must paste it into the DevTools Console of the open Gemini share page.

Then walk the user through the capture procedure:

1. Open the Gemini share link in a browser (the share URL must already be loaded in the visible tab).
2. **Scroll to the top of the conversation.** Gemini uses virtual scrolling, so every turn must enter the DOM at least once — start at the top.
3. Open DevTools by pressing `F12` (or right-click → *Inspect*), then switch to the **Console** tab.
4. **Open `skills/extract_gemini/scraper.js`, copy the *Step 1* block, paste it into the Console, and press Enter.** It will start logging "捕捉第 N 輪" as it captures turns.
5. Scroll smoothly through the **entire** conversation from top to bottom. The `MutationObserver` picks up each turn as it scrolls into view.
6. Confirm the captured count in the Console matches the user's expected turn count.
7. **Copy the *Step 2* block from `scraper.js`, paste it into the Console, and press Enter.** A file named `gemini-conversation.json` will download via the browser.

You can read the actual scraper at `skills/extract_gemini/scraper.js` and paste the relevant blocks for the user. Do not attempt to run it from a terminal — it has no Node entry point.

## Step 3 — Receive the captured file

Ask the user to confirm the file downloaded. Then move it to the session directory:

```bash
mv ~/Downloads/gemini-conversation.json $HOME/.claude/agent-twin/personalized/saves/session/<session_id>/conversation.json
```

(Adjust the source path for the user's OS.)

## Step 4 — Validate format

Check the JSON against the expected shape:

```python
import json, sys
with open('$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/conversation.json') as f:
    data = json.load(f)
assert isinstance(data, list)
assert all('order' in t and 'user' in t and 'model' in t for t in data)
print(f"OK — {len(data)} turns")
```

If the structure differs, refer to `skills/extract_gemini/samples/conversation.json` to see the expected shape and ask the user to recapture.

## Step 5 — Auto-cluster and annotate

Read the entire `conversation.json` and group consecutive turns by topic. **You do this by reading the user-side text and naming coherent clusters** — this is judgement work, not regex work. Aim for clusters of roughly 3–15 turns each; longer clusters are acceptable when topics genuinely persist.

Output to `annotated.txt` in this format (see `skills/extract_gemini/samples/annotated.txt` for a working example):

```
### [<topic label> | turns N+]
[NNN] USER: <user message, single-line>
      AI summary: <first ~120 chars of model response>...
[NNN+1] USER: ...
      AI summary: ...

### [<next topic label> | turns M+]
...
```

Rules:
- Topic labels are short (4–12 words), descriptive, in the conversation's dominant language
- Insert a `### [...]` header only at cluster boundaries, not on every turn
- Replace newlines in user/AI text with single spaces (the analysts read line-by-line)
- Truncate AI summaries at ~120 chars and append `...`

## Step 5.5 — Write `session_meta.json`

Write `session_meta.json` to the session directory using the schema documented at the top of this SKILL. This file is required so `/run_pipeline`'s queue scan can read `turn_count` without re-parsing `conversation.json`.

Example content:

```json
{
  "session_id": "<YYYY-MM-DD>_<12-hex>",
  "turn_count": <len(conversation.json)>,
  "saved_at": "<ISO-8601 timestamp>",
  "source": "extract_gemini"
}
```

Match the schema produced by `scripts/autosave_session.py` for `/save_session` captures (plus the `source` discriminator) so both capture paths are interchangeable downstream.

## Step 6 — Confirm and report

Print a summary to the user:
- Session ID
- Total turns captured
- Number of topic clusters identified
- Paths to the three files (`conversation.json`, `annotated.txt`, `session_meta.json`)

Tell the user the session is now ready for the analysis pipeline (the next skill they typically invoke is the analysis trigger — referenced separately).

## Completion checklist

Before declaring done, verify:

- [ ] Session ID matches format `YYYY-MM-DD_<12-char-hex>`
- [ ] `conversation.json` exists at the expected path and parses as the expected schema
- [ ] `annotated.txt` exists at the expected path
- [ ] `session_meta.json` exists at the expected path with `session_id`, `turn_count`, `saved_at`, `source: "extract_gemini"`
- [ ] Cluster headers cover every turn (no orphan turns between clusters)
- [ ] Topic labels are descriptive and language-matched
- [ ] AI summaries are truncated at ~120 chars
- [ ] No file from the user's prior sessions was overwritten unintentionally

## Validation against existing data

If the user already has a captured conversation at the canonical path, you can validate the skill's annotation step by re-running it on that file and diffing against the existing `annotated.txt`. Cluster names will rarely match exactly, but turn-format compliance and cluster count should be in the same ballpark.

## Files in this skill directory

```
skills/extract_gemini/
├── SKILL.md              ← you are here
├── TEMPLATE.md           ← format specification
├── scraper.js            ← the two-step browser-console capture script
└── samples/
    ├── conversation.json ← minimal valid input
    └── annotated.txt     ← minimal valid output
```

Imported. Next: run `/run_pipeline` to analyze the captured conversation.
