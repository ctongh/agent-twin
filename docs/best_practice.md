# Best practice — operating agent-twin in everyday use

This guide walks through every command in the order you'll actually use them. If you're brand new, start at `/counselor` and keep reading downward; the later sections (`/run_meta_critic`, `/validate_pipeline`) are for advanced or contributor use and can be skipped on first pass. Each section tells you what the command does, when to reach for it, how to run it, what to expect, the gotchas the SKILL files actually warn about, and what to do next.

---

## /counselor

**What it does**: Runs a guided conversation that produces a session file dense enough for the analysis pipeline. First-time users get a domain-tuned questionnaire; returning users get a contextual companion.

**When to use**:
- You have nothing captured yet and want a clean, dense first session.
- You've run the pipeline before and just want to chat — the skill auto-detects you and switches to companion mode.
- You captured a session before but never analyzed it; the skill notices and offers to talk now while reminding you to run `/run_pipeline` later.

**How to run**:
1. In a fresh Claude Code session, type `/counselor`.
2. Pick a domain track when asked: software development, personal life, research/learning, creative work, or mixed.
3. Acknowledge the disclosed question count and time estimate, then answer the questions one at a time. Skip any that don't fit by saying `skip`. Stop early any time by saying `enough` / `stop` / `夠了` / `停`.
4. When the conversation closes, run `/save_session` to capture it.

<!-- TODO: GIF for /counselor -->
*[Demo GIF will be added]*

**What to expect**: 10–14 questions depending on track, roughly 20–28 minutes. Each question comes with a concrete example angle and an explicit skip option, so you're never stuck. The transcript is the input to the pipeline, so longer, more concrete answers produce a sharper profile.

**Common gotchas**:
- The example angle the skill offers is *scaffolding*, not a frame you have to accept — the AI-anchoring filter strips out anything you only echoed back. Use your own words.
- If you exit early, the skill writes a marker into the transcript so the next `/counselor` invocation can offer to resume from where you stopped.
- Companion mode reads your existing brief silently; do not ask it to "show what you know about me" — that's `/show_persona`'s job.
- Don't mix `/counselor` with other unrelated work in the same Claude Code session. The whole conversation gets captured, and irrelevant turns dilute the analysis signal.

**Next step**: Run `/save_session`, then `/run_pipeline`.

---

## /save_session

**What it does**: Snapshots the current Claude Code conversation into the agent-twin user data root so it can be analyzed later.

**When to use**:
- Right after `/counselor` finishes.
- At the end of any working session that you think contains useful self-revealing material — debugging your own decision style, talking through a hard choice, working a research problem out loud.
- Whenever you want to manually checkpoint instead of relying on the autosave Stop hook.

**How to run**:
1. In the session you want to keep, type `/save_session`.
2. The skill snapshots `conversation.json` to `$HOME/.claude/agent-twin/personalized/saves/session/<date>_<id>/`. Re-running it on the same session overwrites in place — it never duplicates.

<!-- TODO: GIF for /save_session -->
*[Demo GIF will be added]*

**What to expect**: A short confirmation with the path it wrote. Takes well under a second. There's also a Stop hook that runs `/save_session` automatically when sessions end, so manual invocation is mostly a "save now" gesture.

**Common gotchas**:
- Requires Python 3.8+ on PATH. If Python is missing the skill prints a friendly error; the autosave hook silently no-ops. Install Python from python.org / Homebrew / your package manager if you want capture.
- Saving an empty or near-empty session captures very little signal. Have something to talk about first.
- If the session has been running for hours and ranges across many topics, consider opening a fresh session for the next round — `/run_pipeline` performs better on focused captures than on sprawling ones.

**Next step**: Either run `/save_session` again later to accumulate more captures, or run `/run_pipeline` to analyze what you have.

---

## /extract_gemini

**What it does**: Imports a Gemini share-link conversation, schema-checks it, and topic-clusters it into the same shape `/save_session` produces. Legacy / optional.

**When to use**:
- You have a Gemini conversation that you'd like to feed into the pipeline.
- You're migrating from another assistant and have a transcript handy.

**How to run**:
1. Get the public Gemini share link.
2. Type `/extract_gemini` and paste the link when prompted.
3. The skill writes the same `conversation.json` + `annotated.txt` pair under `personalized/saves/session/`.

<!-- TODO: GIF for /extract_gemini -->
*[Demo GIF will be added]*

**What to expect**: Pulls the transcript, validates it, inserts cluster headers, writes the file. Failures are usually link-related (private link, expired share, region-locked).

**Common gotchas**:
- Marked legacy because most users won't need it; native Claude Code captures via `/counselor` or `/save_session` are richer.
- Share links can rot. If the import fails, regenerate the share link in Gemini and try again.
- Imported sessions still go through the same pipeline — no special path. Don't expect different treatment.

**Next step**: `/run_pipeline`.

---

## /run_pipeline

**What it does**: Runs the full four-phase, ten-subagent analysis pipeline on every queued session that's new or has changed since last analysis.

**When to use**:
- Right after your first `/counselor` session, to produce your first brief.
- After accumulating two or three new captures since the last run, when you want the profile to absorb the new material.
- After substantively revising the methodology and wanting to re-derive everything.

**How to run**:
1. Type `/run_pipeline` in any session.
2. The skill detects unanalyzed or stale sessions, prints the queue, gives a soft cost preflight, and proceeds without asking for confirmation.
3. Watch the per-phase progress. The pipeline checkpoints between phases — if it gets interrupted, re-running offers to resume from the last clean boundary.

<!-- TODO: GIF for /run_pipeline -->
*[Demo GIF will be added]*

**What to expect**: ~35 minutes per session (Phase 1 ~12 min, Phase 2 ~2 min, Phase 3 ~10 min, Phase 4 ~10 min, Final ~1 min). Five sessions takes around three hours. The output is five product files: `system_of_values.md`, `cognitive_patterns.md`, `knowledge_graph/`, `behavioral_model/`, and the compressed `behavior_brief.md`.

**Common gotchas**:
- Phase 1 dispatches four analysts in parallel — this is mandatory for the four-frame methodology. Don't try to serialize them by hand.
- The meta-critic can iterate up to 3 times if any analyst fails its contract. That's expected, not a problem; let it run.
- The pipeline can be interrupted safely. State files mean you'll resume, not restart, on the next invocation.
- Don't run `/run_pipeline` on a session that's still in progress — `/save_session` it first, then run.

**Next step**: `/show_persona` to inspect, then `/load_persona` in your next working session.

---

## /show_persona

**What it does**: Prints persona artefacts to the conversation so you can read what the pipeline actually produced.

**When to use**:
- Right after `/run_pipeline` finishes, to skim the brief and sanity-check the synthesis.
- Whenever you're curious *why* `/load_persona` made the assistant behave a particular way.
- When debugging — the brief abstracts; the underlying products explain.

**How to run**:
1. Type `/show_persona` (default: prints the brief).
2. Or pass an argument to print a specific layer: `/show_persona values`, `/show_persona cognitive`, `/show_persona graph`, `/show_persona model`, `/show_persona all`.

<!-- TODO: GIF for /show_persona -->
*[Demo GIF will be added]*

**What to expect**: Direct file dump into the conversation. The brief is ≤80 lines, fits in one screen. The other layers can be longer — `all` is the most verbose.

**Common gotchas**:
- This pollutes the working session's prompt context with persona content. If you want persona-aware help without that pollution, use `/consult_twin` instead.
- The graph view is much more illuminating than the printed knowledge graph — open `personalized/results/profile/` as an Obsidian vault for the visual layer.
- Don't use `/show_persona` for "checking the assistant knows me" — use it to read the artefacts; the assistant only adapts after `/load_persona`.

**Next step**: `/load_persona` in a fresh session, or `/consult_twin` for one-shot consultations.

---

## /load_persona

**What it does**: Silently loads `behavior_brief.md` into the current session so every subsequent reply is shaped by it.

**When to use**:
- At the start of any working session where you want the assistant to skip warm-up and meet you where you are.
- After re-running `/run_pipeline` produces an updated brief — load the new brief in your next session to apply the update.

**How to run**:
1. In a fresh session — ideally the first thing you do — type `/load_persona`.
2. The skill reads only the brief and confirms briefly. From here on, every response is persona-aware.

<!-- TODO: GIF for /load_persona -->
*[Demo GIF will be added]*

**What to expect**: A short acknowledgement, no fanfare. The shaping is silent by design — the assistant doesn't quote your brief at you, it just behaves accordingly.

**Common gotchas**:
- `/load_persona` only reads the brief, not the full Phase 2/3/4 outputs. That's intentional — the brief is the operational interface; the larger artefacts are for human inspection.
- The load is per-session. There's no "persistent" mode — every new session needs an explicit `/load_persona`.
- If you want persona context for one specific question without polluting the whole session, prefer `/consult_twin`.
- Don't call `/load_persona` in the middle of a long session expecting retroactive adaptation — earlier turns are already in context.

**Next step**: Just keep working. The assistant adapts from here.

---

## /consult_twin

**What it does**: Dispatches a sub-context twin that loads your brief, reads recent transcript for context, and replies in your first-person voice — without the brief ever entering your working session's prompt.

**When to use**:
- You're inside a working session and hit a decision branch — "should I refactor or rewrite?" — and want your own take rather than the assistant's.
- You're starting research on something unfamiliar and want the questions you'd ask if you knew where to look.
- You want persona shaping for one specific question and nothing else — the rest of the session stays clean.

**How to run**:
1. From inside any working session, type `/consult_twin <free-form question>`.
2. The skill dispatches a Task subagent that loads your brief, reads the recent transcript, and returns a first-person reply.
3. The reply is surfaced; the brief is gone again. Your session's prompt context is unchanged.

<!-- TODO: GIF for /consult_twin -->
*[Demo GIF will be added]*

**What to expect**: A focused, persona-voiced answer. Advisor mode for decision-shaped questions; question-list mode for research-shaped prompts. The skill infers from prefixes like `research`, `let's look at`, `探索`.

**Common gotchas**:
- The twin only knows the brief, not the deeper Phase 2/3/4 artefacts. For deeper inspection, use `/show_persona` separately.
- Recent context for the twin is bounded (~30–50 turns / 20K characters). Long sessions may have lost early context by the time you consult.
- The twin is a high-fidelity simulation, not you. Treat its advice as thinking out loud, not authoritative self-knowledge.
- Don't use `/consult_twin` for pure-factual questions, mechanical tasks, or stack-trace debugging — persona shaping adds nothing there.

**Next step**: Either act on the twin's reply or rephrase if mode inference picked the wrong frame.

---

## /run_meta_critic

**What it does**: Runs the meta-critic standalone over an existing analyses directory, producing a quality verdict without rebuilding anything else.

**When to use**:
- You suspect a Phase 1 analyst's output drifted and want a focused re-audit.
- You're debugging the methodology — testing whether a contract change catches what it should.
- You want to validate someone else's analyses produced outside the pipeline.

**How to run**:
1. Locate the analyses directory (typically under a session's `analyses/` subdir).
2. Type `/run_meta_critic` and supply the directory when prompted.

<!-- TODO: GIF for /run_meta_critic -->
*[Demo GIF will be added]*

**What to expect**: Per-analyst verdicts: accept, iterate (with reason), or escalate. No new findings about the subject — only contract compliance, contradiction flags, and AI-anchoring residue checks.

**Common gotchas**:
- The meta-critic is forbidden from producing novel claims about the subject. If you see anything that looks like new analysis in its output, that's a violation worth reporting.
- This is the manual entry point. `/run_pipeline` already runs the meta-critic automatically as part of the Phase 1 loop — you don't need to invoke it separately during a normal pipeline run.
- A verdict of `iterate` doesn't mean the analyst was wrong overall — it just means at least one contract clause failed. Read the reason carefully.

**Next step**: If verdicts indicate iteration, re-dispatch the failing analysts (typically via re-running the pipeline phase). If everything accepts, no action needed.

---

## /validate_pipeline

**What it does**: Runs the umbrella methodology validator across the agent-twin project — privacy checks, format checks, safety checks.

**When to use**:
- Before committing changes to `methodology/`, `agents/`, or `skills/`.
- When contributing a new validator.
- When auditing the codebase for personal-data leakage before publishing.

**How to run**:
1. From any session in the project, type `/validate_pipeline`.
2. The skill iterates over every implemented validator under `skills/validate_pipeline/validators/` and reports per-validator pass/fail.

<!-- TODO: GIF for /validate_pipeline -->
*[Demo GIF will be added]*

**What to expect**: A pass/fail per validator with surfaced failures inline. Privacy validator confirms shareable parts are free of personal data; format validator checks contract YAML; safety validator scans agent prompts.

**Common gotchas**:
- This is a contributor-facing surface. End users don't normally need to run it.
- Failures are usually obvious (a path under `personalized/` got accidentally staged, a contract block went malformed). Fix the root issue, then re-run.
- New validators only need a front-matter `status: implemented` to be picked up. The umbrella discovers them automatically.

**Next step**: Fix any failures, then commit.

---

## Workflows

### First-time setup

You just installed the plugin and have nothing captured.

1. `/counselor` — pick a track, answer 10–14 questions over ~20 minutes. Skip anything that doesn't fit.
2. `/save_session` — captures the conversation.
3. `/run_pipeline` — wait ~35 minutes for the first profile.
4. `/show_persona` — skim the brief; verify the synthesis sounds like you.
5. New session → `/load_persona` — start using a persona-aware assistant.

### Update after new conversations

You've been using the assistant for a couple of weeks and feel the brief is stale.

1. Make sure recent useful sessions were captured (the autosave Stop hook usually handles this; manual `/save_session` if you want to be sure).
2. `/run_pipeline` — it auto-detects which sessions are new or changed and only analyzes those. Roughly 35 minutes per session in the queue.
3. `/show_persona` — confirm the new brief reflects recent shifts.
4. Next working session → `/load_persona` to apply the updated brief.

### Working session with twin consultation

You're deep in a working session and want your own take on a branch.

1. Don't `/load_persona` defensively — keep the working session clean.
2. When you hit a fork, type `/consult_twin <your question>` from inside the session.
3. The twin replies in first-person voice; the brief never enters your prompt context.
4. Continue working. If the twin's answer is off-frame, rephrase and try again — the cost of being wrong is low.
