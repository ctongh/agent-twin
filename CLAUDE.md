# agent-twin — Digital Persona Plugin

This project is a **Claude Code plugin** that builds a structured persona profile from your AI conversation logs, then loads it into future sessions so the assistant adapts to how you actually think and communicate.

---

## Source-of-truth regime

**SKILL.md files are the single source of truth.** Each command (`commands/<name>.md`) is a thin router that points at its corresponding `skills/<name>/SKILL.md`. The SKILL is the spec. `methodology/` contains design rationale only; nothing in `methodology/` instructs execution.

If you find a contradiction between `methodology/`, `commands/`, and a SKILL.md, the SKILL.md wins.

---

## `${CLAUDE_PLUGIN_ROOT}`

Whenever a skill or agent file references `${CLAUDE_PLUGIN_ROOT}`, substitute the **absolute path to the directory containing this CLAUDE.md file** (the plugin root). Claude Code natively expands this token at runtime.

---

## User data root

All user-generated data (captured sessions, analyses, profiles) lives at:

`$HOME/.claude/agent-twin/personalized/`

Why this path: it's in HOME (not the plugin cache), so it survives plugin updates. Never write user data anywhere else.

SKILLs must resolve `$HOME` to an absolute path before calling Read/Write/Edit/Glob tools (those require absolute paths). The standard pattern:

```bash
DATA_ROOT="$(bash -c 'echo $HOME')/.claude/agent-twin/personalized"
```

Then use `$DATA_ROOT/...` for absolute paths. The Python autosave script uses `Path.home()` directly — already correct.

---

## Available skills

Eight slash commands are defined under `commands/`. Each one routes to a `SKILL.md` file.

| Command | SKILL.md | Purpose |
|---|---|---|
| `/extract_gemini` (legacy/optional) | `skills/extract_gemini/SKILL.md` | Import a Gemini conversation via share link. Primary capture is `/save_session` or `/counselor` — use this only for Gemini imports. |
| `/save_session` | `skills/save_session/SKILL.md` | Snapshot the current Claude Code session |
| `/counselor` | `skills/counselor/SKILL.md` | Guided conversation that produces a pipeline-ready session (questionnaire for first-time users, companion mode for returning users) |
| `/run_pipeline` | `skills/run_pipeline/SKILL.md` | Run the full 4-phase analysis pipeline |
| `/load_persona` | `skills/load_persona/SKILL.md` | Load the compiled brief silently into this session |
| `/show_persona` | `skills/show_persona/SKILL.md` | Print compiled persona products to the conversation for inspection (viewer; does not load anything) |
| `/run_meta_critic` | `skills/run_meta_critic/SKILL.md` | Standalone quality audit of existing analyses |
| `/validate_pipeline` | `skills/validate_pipeline/SKILL.md` | Check methodology compliance |

---

## Available agents

Ten subagent definitions live under `agents/`. They are dispatched by `/run_pipeline` via the `Task` tool — **do not dispatch them manually unless debugging**.

| Agent file | Phase | Role |
|---|---|---|
| `agents/affect-analyst.md` | 1 | Emotional architecture, fears, defenses |
| `agents/social-dynamics-analyst.md` | 1 | Power, status, authority relationships |
| `agents/values-analyst.md` | 1 | Value hierarchy — declared vs. revealed |
| `agents/narrative-analyst.md` | 1 | Self-story, identity language, causal attribution |
| `agents/meta-critic.md` | 1 (QA gate) | Audit all four analysts against output contracts |
| `agents/synthesis-builder.md` | 1 (synthesis) | Cross-frame integration → `system_of_values.md` |
| `agents/cognitive-patterns-builder.md` | 2 | Language fields, metaphors, argument structure |
| `agents/knowledge-graph-builder.md` | 3 | Typed concept graph with wiki-linked nodes |
| `agents/behavioral-model-builder.md` | 4 | Intensity-stratified situation→response patterns |
| `agents/behavior-brief-generator.md` | Final | Compress all products to ≤80-line actionable brief |

---

## Pipeline flow

```
CAPTURE → ANNOTATE → PHASE 1 → PHASE 2 → PHASE 3 → PHASE 4 → COMPRESS → LOAD
```

- **Capture**: `/extract_gemini`, `/save_session`, or `/counselor` → `$HOME/.claude/agent-twin/personalized/saves/session/<date>_<id>/`
- **Phase 1**: Four analysts in parallel → meta-critic audit loop (max 3 iterations) → synthesis
- **Phase 2–4**: Deterministic expansions of Phase 1 findings (cognitive patterns, knowledge graph, behavioral model)
- **Compress**: `behavior-brief-generator` → `$HOME/.claude/agent-twin/personalized/results/profile/behavior_brief.md` (≤80 lines)
- **Load**: `/load_persona` reads the brief and silently shapes every response in this session

---

## Key conventions

**`$HOME/.claude/agent-twin/personalized/` is the user data root.** Never commit anything under that directory. All user data (sessions, analyses, profiles) lives there and must stay local.

**`/run_pipeline` runs at top level.** Subagents cannot use the `Task` tool, so the skill itself is the orchestrator. It dispatches all 10 agents as real Claude Code subagents from the top-level conversation context.

**Phase 1 analysts must be dispatched in a single message** (parallel). This is mandatory — the four-frame design depends on independent, non-contaminated analyses from separate contexts.

**Output language matches the source.** If the source conversation is in Traditional Chinese, every product — analyses, profile, brief — is written in Traditional Chinese. Never translate.

**The AI-anchoring filter.** A framing counts as the subject's only if they introduced or extended it in their own words. Statements the subject only echoed back from Claude's framing are excluded from evidence.

**Evidence hierarchy**: pre-rational signals (physical reactions, slips, outbursts) > concrete actions > subject correcting Claude > cross-cluster recurrence > single self-disclosure > AI-anchored statements.

**No new findings in the audit layer.** The meta-critic validates contracts and flags contradictions — it does not produce novel analysis of the subject.

---

## Methodology reference

| File | What it defines |
|---|---|
| `methodology/design_notes.md` | Architectural rationale: why four phases, why only Phase 1 is audited, the AI-anchoring filter, the evidence hierarchy. Not executable. |
| `methodology/output_contract_schema.md` | Contract format applied by the meta-critic at runtime. |

For execution details, read `skills/<name>/SKILL.md`. For agent behavior, read `agents/<name>.md`.

---

## Storage layout

```
Plugin code (${CLAUDE_PLUGIN_ROOT}):
agent-twin/
├── agents/          # 10 subagent system prompts
├── commands/        # 8 slash command routers (one-line dispatch to skill)
├── methodology/     # design_notes.md + output_contract_schema.md only
├── scripts/         # autosave_session.py (Stop hook)
└── skills/          # 8 SKILL.md files (the source of truth for each command)

User data ($HOME/.claude/agent-twin):
$HOME/.claude/agent-twin/
└── personalized/    # ← all user data lives here (never committed)
    ├── saves/session/<date>_<id>/   # Captured conversations
    └── results/profile/             # Compiled persona products
```
