# agent-twin — Digital Persona Plugin

This project is a **Claude Code plugin** that builds a structured persona profile from your AI conversation logs, then loads it into future sessions so the assistant adapts to how you actually think and communicate.

---

## `${CLAUDE_PLUGIN_ROOT}`

Whenever a skill, agent, or methodology file references `${CLAUDE_PLUGIN_ROOT}`, substitute the **absolute path to the directory containing this CLAUDE.md file** (the project root).

---

## `${AGENT_TWIN_DATA}`

All user data lives under this root. Always resolves to `~/.claude/agent-twin` — **outside** the versioned plugin cache, so data survives plugin updates.

Whenever a skill references a `personalized/` path, it is relative to `${AGENT_TWIN_DATA}`. Full form: `~/.claude/agent-twin/personalized/...`.

---

## Available skills

Seven slash commands are defined under `commands/`. Each one routes to a `SKILL.md` file:

| Command | SKILL.md | Purpose |
|---|---|---|
| `/extract_gemini` | `skills/extract_gemini/SKILL.md` | Import a Gemini conversation via share link |
| `/save_session` | `skills/save_session/SKILL.md` | Snapshot the current Claude Code session |
| `/counselor` | `skills/counselor/SKILL.md` | Guided questionnaire or contextual companion |
| `/run_pipeline` | `skills/run_pipeline/SKILL.md` | Run the full 4-phase analysis pipeline |
| `/load_persona` | `skills/load_persona/SKILL.md` | Load the compiled profile brief into this session |
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

- **Capture**: `/extract_gemini`, `/save_session`, or `/counselor` → `${AGENT_TWIN_DATA}/personalized/saves/session/<date>_<id>/`
- **Phase 1**: Four analysts in parallel → meta-critic audit loop (max 3 iterations) → synthesis
- **Phase 2–4**: Deterministic expansions of Phase 1 findings (cognitive patterns, knowledge graph, behavioral model)
- **Compress**: `behavior-brief-generator` → `${AGENT_TWIN_DATA}/personalized/results/profile/behavior_brief.md` (≤80 lines)
- **Load**: `/load_persona` reads the brief and silently shapes every response in this session

---

## Key conventions

**`${AGENT_TWIN_DATA}/personalized/` is the user data root.** Never commit anything under that directory. All user data (sessions, analyses, profiles) lives at `~/.claude/agent-twin/personalized/` and must stay local.

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
| `methodology/pipeline.md` | Architecture overview, invariants, data bias notes |
| `methodology/orchestration_protocol.md` | Step-by-step protocol executed by `/run_pipeline` |
| `methodology/output_contract_schema.md` | Contract format applied by the meta-critic |
| `methodology/phase1_value_extraction.md` | Why four frames; output structure; quality criteria |
| `methodology/phase2_cognitive_patterns.md` | Six cognitive dimensions; pitfalls |
| `methodology/phase3_knowledge_graph.md` | Node types, edge types, quality rules |
| `methodology/phase4_behavioral_model.md` | BP file format, intensity stratification, evidence rules |

---

## Storage layout

```
Plugin code (${CLAUDE_PLUGIN_ROOT}):
agent-twin/
├── agents/          # 10 subagent system prompts
├── commands/        # 7 slash command entry points
├── methodology/     # Design specs and protocol documents
├── scripts/         # autosave_session.py (Stop hook)
└── skills/          # 7 SKILL.md files (one per command)

User data (${AGENT_TWIN_DATA} = ~/.claude/agent-twin):
~/.claude/agent-twin/
└── personalized/    # ← all user data lives here (never committed)
    ├── saves/session/<date>_<id>/   # Captured conversations
    └── results/profile/             # Compiled persona products
```
