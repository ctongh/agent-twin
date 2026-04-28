# Format Specification

The `extract_gemini` skill produces two files. Their schemas are:

## `conversation.json`

A JSON array of turn objects. Each object:

```json
{
  "order": <integer, 0-indexed turn number>,
  "user": "<user's message text — full content, may contain newlines>",
  "model": "<model's response text — full content, may contain newlines>"
}
```

Constraints:
- The array is ordered chronologically by `order`
- `order` values are unique and contiguous starting from 0
- Both `user` and `model` are strings (may be empty if a turn is partially captured)
- The file is UTF-8 encoded with no BOM

## `annotated.txt`

A plain-text file. Cluster headers and turns interleave:

```
### [<cluster label> | turns <first-turn>+]
[<NNN>] USER: <user text, newlines collapsed to single spaces>
      AI summary: <first ~120 chars of model text, newlines collapsed>...
[<NNN+1>] USER: ...
      AI summary: ...

### [<next cluster label> | turns <next-first-turn>+]
[<NNN+k>] USER: ...
      AI summary: ...
```

Constraints:
- `<NNN>` is `order + 1`, zero-padded to 3 digits (e.g., `[001]`, `[042]`, `[120]`)
- A cluster header precedes every cluster boundary; turns within a cluster have no header
- Cluster labels are short (4–12 words) and in the conversation's dominant language
- Newlines in user/AI text are collapsed to single spaces inside the annotated form
- AI summaries are truncated to roughly 120 characters and end with `...`
- The file is UTF-8 encoded with no BOM

## Validation

To check that a pair of files conforms to this spec:

1. Load `conversation.json`; verify schema
2. Parse `annotated.txt`; for each `[NNN]` line, verify a corresponding turn exists in `conversation.json` with `order = NNN - 1`
3. Verify every turn from `conversation.json` is represented exactly once in `annotated.txt`
4. Verify cluster headers cover every turn (no orphan turns between clusters)

## Compatibility notes

The same format is used downstream by:
- `agents/affect-analyst.md` and other analysts (read `annotated.txt`)
- `agents/orchestrator.md` (passes path to analysts)
- `agents/meta-critic.md` (cross-references back to source data via turn IDs)

Any change to this format requires synchronized updates across the agent prompts and a re-run of `validate_pipeline`.
