---
name: extract_gemini
description: Capture a conversation from a Gemini share link and prepare it (with topic-cluster annotation) for the agent-twin analysis pipeline. Use when the user wants to import a Gemini conversation into the persona project.
---

# extract_gemini

When this skill is invoked, walk the user through extracting a Gemini conversation and producing the two files the analysis pipeline needs:

| File | Purpose |
|------|---------|
| `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/conversation.json` | Raw turn-by-turn capture |
| `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/annotated.txt` | Same content with topic-cluster headers |

The format spec lives in `skills/extract_gemini/TEMPLATE.md`. Real samples live in `skills/extract_gemini/samples/`.

## Step 1 — Generate session ID and create directory

Generate a session ID with format `YYYY-MM-DD_<8-char-hex-guid>`. You can produce the GUID with:

```bash
python -c "import uuid; print(uuid.uuid4().hex[:8])"
```

Create the directory:

```
$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/
```

Tell the user the session ID you generated.

### Existing-directory handling

The hex GUID makes collision essentially impossible, but a re-extract on the same day can collide if the user reuses an ID intentionally. Before writing into an existing `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/`:

1. If the directory exists and contains files (`conversation.json`, `annotated.txt`, or an `analyses/` subdir), **stop** and ask the user. Two acceptable choices:
   - **Generate a fresh session ID** (default; safer). Re-run Step 1 with a new GUID. Any prior pipeline outputs at the old ID are preserved untouched.
   - **Overwrite explicitly.** The user must confirm. Then `rm -rf` only the files this skill is about to write (`conversation.json`, `annotated.txt`); leave any sibling `analyses/` directory intact (those belong to the pipeline, not this skill).
2. If the directory exists but is empty, just write into it.

Do not silently overwrite. The session ID is the de-facto join key for downstream products; collisions create silent data-corruption risk.

## Step 2 — Provide capture instructions

Ask the user for a Gemini share link (a URL like `gemini.google.com/share/<id>`). If they don't have one yet, instruct them to open the conversation in Gemini and click the share button.

Then show them the capture procedure:

1. Open the share link in a browser
2. **Scroll to the top of the conversation** (this forces all turns to render — Gemini uses virtual scrolling and the scraper depends on every turn being in the DOM at least once)
3. Open DevTools (`F12`) → Console
4. Paste the contents of `skills/extract_gemini/scraper.js` Step 1 block, press Enter — it will start logging captures
5. Scroll smoothly through the **entire** conversation from top to bottom (the MutationObserver picks up each turn as it scrolls into view)
6. Confirm the captured count matches the user's expected turn count
7. Paste the Step 2 block to download `gemini-conversation.json`

You can read the actual scraper at `skills/extract_gemini/scraper.js` and paste the relevant blocks for the user.

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

## Step 6 — Confirm and report

Print a summary to the user:
- Session ID
- Total turns captured
- Number of topic clusters identified
- Paths to the two files

Tell the user the session is now ready for the analysis pipeline (the next skill they typically invoke is the analysis trigger — referenced separately).

## Completion checklist

Before declaring done, verify:

- [ ] Session ID matches format `YYYY-MM-DD_<8-char-hex>`
- [ ] `conversation.json` exists at the expected path and parses as the expected schema
- [ ] `annotated.txt` exists at the expected path
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
