---
name: consult_twin
description: Consult the user's persona twin from inside a working session without polluting this session's context. Pass any free-form question; the twin reads the behavior brief and the recent session transcript in its own sub-context, then responds in the user's first-person voice. Unlike /load_persona, the brief never enters this session's prompt.
---

# consult_twin

A sub-context twin you can ask anything without dragging persona shaping into the current working session. The skill dispatches the `twin-advisor` agent via the Task tool; the agent reads the brief and the recent transcript in its own context, replies in the user's voice, and the response comes back to the orchestrator as plain text. **The brief never enters this session's prompt.**

This is the deliberate complement to `/load_persona`:

| | `/load_persona` | `/consult_twin` |
|---|---|---|
| Scope | persists for the whole session | one Task dispatch, then gone |
| Side effect | every reply afterward is persona-shaped | nothing in this session changes |
| When to use | starting a working session you want to be persona-aware end-to-end | you only need the twin's take at one moment |

The two are orthogonal. The user can have neither, either, or (in principle) both — `/consult_twin` does not call `/load_persona` internally and never will.

## Argument grammar

```
/consult_twin <free-form question>
```

A single free-form string. No flags, no modes. The owner explicitly chose the simplest possible interface ("越無腦越好"). Mode (advisor vs. curious) is inferred from the question shape — see Step 4.

## Step 1 — Resolve $HOME and the brief path

Run a single Bash command to expand `$HOME` and derive the brief path:

```bash
DATA_ROOT="$(bash -c 'echo $HOME')/.claude/agent-twin/personalized"
BRIEF_PATH="$DATA_ROOT/results/profile/behavior_brief.md"
```

All subsequent operations use the resolved absolute paths.

## Step 2 — Verify the brief exists

If the file at `BRIEF_PATH` does not exist, surface exactly one line and stop:

> No persona profile found. Run `/run_pipeline` on a captured session first.

Do not attempt to dispatch the agent without a brief — the agent has nothing to read.

## Step 3 — Locate the current session's transcript (best effort)

Claude Code writes the active session's JSONL under `~/.claude/projects/<encoded-project-path>/`. The encoding rule is: **every path separator becomes `-`** (so `D:\agent-twin` → `D--agent-twin`, `/home/user/proj` → `-home-user-proj`). Verify on this machine before assuming:

```bash
ls "$(bash -c 'echo $HOME')/.claude/projects/" | head
```

Pick the directory entry that matches the current working directory under that encoding.

Then glob `*.jsonl` inside that directory and pick the **newest by mtime** — the active session writes to its file continuously, so the most recently modified JSONL is almost always the current session:

```bash
ENCODED="$(pwd | sed 's#[/\\:]#-#g')"
PROJECTS_DIR="$(bash -c 'echo $HOME')/.claude/projects/$ENCODED"
TRANSCRIPT="$(ls -t "$PROJECTS_DIR"/*.jsonl 2>/dev/null | head -n1)"
```

If no transcript is found (unusual configuration, brand-new session before first turn flushes), proceed with `SESSION_TRANSCRIPT_PATH` empty. Advisor mode still works on the brief alone.

## Step 4 — Mode inference from question shape

This is a soft heuristic. If the result is wrong, the cost is small (the user just rephrases). Future agents editing this SKILL: feel free to refine the prefix list as patterns emerge.

Set `MODE=curious` if the question (case-insensitive, after stripping leading whitespace and punctuation) starts with one of:

- English: `research`, `explore`, `let's look at`, `let's research`, `help me understand`, `i want to learn about`, `i want to understand`, `what should i research`, `what should i learn about`, `tell me about` (when paired with an unfamiliar-domain noun phrase — soft signal only)
- Traditional Chinese: `研究`, `探索`, `了解`, `學習`, `想了解`, `想學`, `幫我了解`, `想研究`

Otherwise set `MODE=advisor`. **Default is advisor.** When uncertain, choose advisor — it's the more useful failure mode.

## Step 5 — Dispatch the twin-advisor agent

Use the Task tool with `subagent_type="twin-advisor"`. Build the prompt as a structured key-value block so the agent can parse it robustly:

```
BRIEF_PATH=<absolute path from Step 1>
SESSION_TRANSCRIPT_PATH=<absolute path from Step 3, or empty>
MODE=<advisor|curious from Step 4>
QUESTION=<the user's question verbatim>
```

The `description` parameter for the Task call should be a short label like `Twin consultation: <first 50 chars of question>`. The agent's tools are `Read` only — it cannot write or run commands; it just reads, thinks, and responds.

## Step 6 — Return the agent's response verbatim

When the agent returns, print its response to the user **without any preamble**. Do not say "Here's what your twin says:" or "The twin responded:". The agent already speaks in first-person; let it land directly.

## Step 7 — One-line trailer

After the response, on a new line, append exactly:

> `(Consulted via twin-advisor — response did not enter this session's prompt context.)`

This is the integrity confirmation: the user wanted assurance that contamination did not happen. Always include it.

## What this skill must not do

- Call `/load_persona`. The two are orthogonal; the whole point is sub-context isolation.
- Read `behavior_brief.md` itself. The agent reads it; the SKILL only checks existence.
- Inject the brief or the transcript into this session's prompt by quoting it back.
- Add framing or commentary around the agent's response. The agent's reply IS the answer.
- Refuse a question because mode inference is ambiguous. Default to advisor.

## Out of scope

- Editing or rebuilding the brief — use `/run_pipeline`.
- Loading the brief into the session — use `/load_persona`.
- Inspecting the profile — use `/show_persona`.
- Auditing analyses — use `/run_meta_critic`.

## Completion checklist

- [ ] `$HOME` resolved via Bash; all paths used were absolute
- [ ] Missing `behavior_brief.md` was reported with the standard one-line message and execution stopped
- [ ] Most recent JSONL under `~/.claude/projects/<encoded-cwd>/` was located, or empty was passed if not found
- [ ] Mode was inferred from the question shape (default advisor)
- [ ] `twin-advisor` was dispatched via the Task tool with the four-key prompt block
- [ ] Agent's response was printed verbatim with no preamble
- [ ] One-line trailer about sub-context isolation was appended
- [ ] No call to `/load_persona` was made
