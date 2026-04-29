---
name: show_persona
description: Print the user's compiled persona profile to the conversation for inspection. Default shows behavior_brief.md only; arguments select specific products or list multi-file products (knowledge_graph, behavioral_model). This skill is a viewer — it does NOT load anything into Claude's behavior. Use /load_persona for that.
---

# show_persona

A viewer. Reads compiled persona products from disk and prints them to the conversation so the user can inspect what the pipeline produced. Does not modify any file. Does not alter Claude's behavior in this session.

For the silent-load semantics that adapt responses to the user, see `/load_persona`.

## Argument grammar

```
/show_persona              → brief        (default)
/show_persona brief        → behavior_brief.md
/show_persona values       → system_of_values.md
/show_persona cognitive    → cognitive_patterns.md
/show_persona graph        → list files under knowledge_graph/
/show_persona model        → list files under behavioral_model/
/show_persona all          → brief + values + cognitive inline, then graph and model file lists
/show_persona --full       → alias for `all`
```

Any other argument → reject with a one-line error that lists the valid forms.

## Step 1 — Resolve the data root

Run a single Bash command to expand `$HOME` to an absolute path, then derive the profile directory:

```bash
DATA_ROOT="$(bash -c 'echo $HOME')/.claude/agent-twin/personalized"
PROFILE_DIR="$DATA_ROOT/results/profile"
```

All subsequent Read/Write/Edit/Glob calls must use absolute paths derived from `$PROFILE_DIR`.

## Step 2 — Locate brief; check freshness

Always check `$PROFILE_DIR/behavior_brief.md` first, even when the argument is not `brief`:

- If the file does not exist, print exactly:

  > No persona profile found at `<absolute PROFILE_DIR>/`. Run `/run_pipeline` on a captured session first.

  Then stop. Do not attempt to read other products — without a brief, the profile is incomplete.

- If the file exists but its mtime is older than ~30 days, print a one-line soft warning before showing anything:

  > Brief is older than 30 days (last updated `<YYYY-MM-DD>`). Consider re-running `/run_pipeline`.

  Do not block — proceed with the requested view.

Use `stat` (or equivalent) on the file to get the mtime. The 30-day cutoff is a soft heuristic; do not treat it as a hard error.

## Step 3 — Dispatch on argument

### `brief` (default)

Read `$PROFILE_DIR/behavior_brief.md` in full and print it verbatim. No preamble, no header, no closing remark — just the file contents.

### `values`

Read `$PROFILE_DIR/system_of_values.md`. If missing, say so on one line (`system_of_values.md not found at <path>`) and stop. Otherwise print verbatim.

### `cognitive`

Read `$PROFILE_DIR/cognitive_patterns.md`. Same missing-file handling as `values`. Print verbatim.

### `graph`

Use Glob with pattern `$PROFILE_DIR/knowledge_graph/**/*.md` to enumerate files. If the directory is missing or empty, say `knowledge_graph/ is empty or not built yet at <path>` and stop.

Otherwise list each file as a relative path rooted at `knowledge_graph/`, one per line, sorted. Then add one line:

> Designed for Obsidian's graph view. Open `<absolute path to knowledge_graph/>` as a vault to navigate the typed concept graph.

Do **not** inline file contents.

### `model`

Use Glob with pattern `$PROFILE_DIR/behavioral_model/**/*.md` to enumerate files. Same missing/empty handling as `graph`.

List each file as a relative path rooted at `behavioral_model/`, one per line, sorted. Then add one line:

> Designed for Obsidian's graph view. Open `<absolute path to behavioral_model/>` as a vault to navigate the BP files.

Do **not** inline file contents.

### `all` / `--full`

Run, in order:

1. `brief` (print behavior_brief.md)
2. A single blank line, then `---`, then a blank line as a section break
3. `values` (print system_of_values.md, or its missing-file line)
4. Section break
5. `cognitive` (print cognitive_patterns.md, or its missing-file line)
6. Section break
7. `graph` (file list + Obsidian note)
8. Section break
9. `model` (file list + Obsidian note)

The two multi-file products stay as file lists in this mode too — never inline them.

## What this skill must not do

- Modify, create, or delete any file under `$PROFILE_DIR` or anywhere else.
- Inline contents of `knowledge_graph/` or `behavioral_model/` files in any mode.
- Print decorative banners, titles, "now showing X", or trailing summaries around the file contents. The file content is the output.
- Re-read a previously loaded brief from session memory. Always read fresh from disk.
- Claim or imply that anything was loaded into Claude's behavior. This is a viewer.
- Translate or reformat the file contents. Print verbatim, including the source language (Traditional Chinese is normal here).

## Out of scope

- Editing or rebuilding the profile. Use `/run_pipeline`.
- Loading the profile into the active session. Use `/load_persona`.
- Auditing the analyses for quality. Use `/run_meta_critic`.

## Completion checklist

- [ ] `$HOME` was resolved via Bash before any file access
- [ ] All file paths used were absolute
- [ ] Missing `behavior_brief.md` was reported with the resolved path and execution stopped
- [ ] Stale brief (>30 days) surfaced a one-line warning but did not block
- [ ] For `graph` and `model` modes, files were listed (not inlined) and the Obsidian note was shown
- [ ] No file was modified
- [ ] No banner, header, or "now showing" preamble was added around file contents
