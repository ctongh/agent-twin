# agent-twin

**Turn your AI conversation logs into a structured persona profile — then load it into every new Claude session.**

agent-twin analyzes how you actually think, communicate, and make decisions. It builds a layered profile from your real conversations using a four-frame analytical pipeline, then compresses everything into a practical brief that silently shapes every future response.

```
   CAPTURE           ANALYZE              COMPRESS          LOAD
  ┌────────┐      ┌───────────┐         ┌──────────┐     ┌────────┐
  │ Convo  │ ───▶ │ 4-frame   │ ───────▶│ behavior │ ──▶ │ Every  │
  │  logs  │      │ pipeline  │         │  _brief  │     │session │
  └────────┘      └───────────┘         └──────────┘     └────────┘
/save_session    /run_pipeline                          /load_persona
/extract_gemini   ~20 minutes            ≤80 lines
/counselor        10 subagents
```

---

## Requirements

Python 3.8+ is required for the autosave Stop hook and the `/save_session` skill. Without Python, those features become silent no-ops (the hook never fires; the skill surfaces an error). Everything else — the analysis pipeline, `/load_persona`, `/show_persona`, `/counselor` — works without Python.

Install Python:

- **Windows**: download from https://www.python.org/downloads/ (the official installer enables both `python` and `py` on PATH); or `winget install Python.Python.3.12`
- **macOS**: `brew install python` (Homebrew); the system `python3` also works on macOS 12+
- **Linux**: `sudo apt install python3` (Debian/Ubuntu) or `sudo dnf install python3` (Fedora)

Verify with `python --version` (expect `Python 3.x.x`). No external Python packages are needed.

---

## Commands

| What you're doing | Command | Key outcome |
|---|---|---|
| Import a Gemini conversation | `/extract_gemini` | `conversation.json` + annotated topic clusters |
| Save the current session | `/save_session` | Session snapshot ready for analysis |
| Guided capture or companion mode | `/counselor` | Structured questionnaire or contextual conversation |
| Build the full persona profile | `/run_pipeline` | 5 profile products + actionable behavior brief |
| Load persona into this session | `/load_persona` | Brief silently shapes every subsequent response |
| Re-audit existing analyses | `/run_meta_critic` | Quality verdict without re-running analysts |
| Check methodology compliance | `/validate_pipeline` | Pass/fail per validator, with findings |

`/run_pipeline` is the primary entry point. The other commands feed it (capture) or use its output (load).

---

## Quick Start

<details>
<summary><b>Claude Code</b></summary>

```bash
git clone https://github.com/ctongh/agent-twin.git
cd agent-twin
claude
```

The autosave hook runs automatically on session exit — no extra setup needed for capture. To build your first profile:

```
/counselor
```

Answer the questionnaire, then run `/run_pipeline` when prompted.

</details>

<details>
<summary><b>Configure the autosave hook</b></summary>

If you move the project directory, update the path in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python /absolute/path/to/agent-twin/scripts/autosave_session.py",
        "async": true,
        "timeout": 30
      }]
    }]
  }
}
```

Requires Python 3. No external dependencies.

</details>

---

## All 7 Skills

### Capture — Get conversations into the pipeline

| Skill | What It Does | Use When |
|---|---|---|
| [extract_gemini](skills/extract_gemini/SKILL.md) | Imports a Gemini share-link conversation; validates schema, auto-generates topic-cluster annotations | You have Gemini conversations you want analyzed |
| [save_session](skills/save_session/SKILL.md) | Snapshots the active Claude Code session; deterministic session ID; token-aware truncation; idempotent | You want to capture the current conversation before it ends |
| [counselor](skills/counselor/SKILL.md) | First-time: asks 10 questions one at a time with natural follow-up. Returning: reads your profile silently and opens contextually | Starting from scratch, or wanting a guided reflection session |

### Analyze — Build the profile

| Skill | What It Does | Use When |
|---|---|---|
| [run_pipeline](skills/run_pipeline/SKILL.md) | Orchestrates all 10 subagents across 4 phases; queue scanning; checkpoint/resume; produces 5 profile products | You have at least one captured session and want a profile built |

### Load — Put the profile to work

| Skill | What It Does | Use When |
|---|---|---|
| [load_persona](skills/load_persona/SKILL.md) | Reads `behavior_brief.md`; checks for staleness; one-line acknowledgment; brief shapes every response from that point | Opening a new session and wanting the assistant to adapt to you |

### Quality — Audit and validate

| Skill | What It Does | Use When |
|---|---|---|
| [run_meta_critic](skills/run_meta_critic/SKILL.md) | Standalone audit of existing analyst outputs against output contracts; no re-dispatch; timestamped history | Reviewing Phase 1 quality without re-running the full pipeline |
| [validate_pipeline](skills/validate_pipeline/SKILL.md) | Runs sub-validators (methodology neutrality, etc.); aggregates pass/fail verdict with per-validator findings | Before sharing or publishing methodology files |

---

## The Analysis Pipeline

`/run_pipeline` dispatches 10 specialized subagents across 4 sequential phases. Each phase runs independently; only Phase 1 carries a quality gate.

```
  Phase 1 — Four-Frame Audited Analysis (~10–12 min)
  ┌─────────────────────────────────────────────────────────────┐
  │  Step 1: Four analysts dispatched in parallel               │
  │    affect-analyst  ·  social-dynamics-analyst               │
  │    values-analyst  ·  narrative-analyst                     │
  │                                                             │
  │  Step 2: meta-critic audits all four                        │
  │    verdict: accept / iterate (max 3×) / escalate            │
  │                                                             │
  │  Step 3: synthesis-builder cross-frame integration          │
  │    → system_of_values.md  (Product 1)                       │
  └─────────────────────────────────────────────────────────────┘
  Phase 2 — Cognitive Patterns (~2 min)
    cognitive-patterns-builder reads source conversation
    → cognitive_patterns.md  (Product 2)

  Phase 3 — Knowledge Graph (~3 min)
    knowledge-graph-builder seeds from Phase 1 synthesis
    → knowledge_graph/  (Product 3)  — Concept · Emotion · Person · Event nodes

  Phase 4 — Behavioral Model (~3 min)
    behavioral-model-builder seeds from Phase 1 synthesis
    → behavioral_model/  (Product 4)  — BP-001 … BP-NNN

  Final — Profile Compression (~1 min)
    behavior-brief-generator reads all four products
    → behavior_brief.md  (Product 5)  — ≤80 lines, imperative form
```

**Why four frames in parallel?** Each analyst reads the same conversation through a different lens — emotional, relational, values-based, narrative. Running them in separate contexts prevents any one frame from contaminating another. The meta-critic then checks for contradictions and filters AI-anchoring residue before synthesis.

---

## The 10 Agents

Pre-configured specialist subagents. Dispatched exclusively by `/run_pipeline` — not for manual invocation.

### Phase 1 Analysts (dispatched in parallel)

| Agent | Frame | Looks For |
|---|---|---|
| [affect-analyst](agents/affect-analyst.md) | Emotional | Fear structures, defensive operations, attachment dynamics, emotional needs |
| [social-dynamics-analyst](agents/social-dynamics-analyst.md) | Relational | Power positioning, status consciousness, authority relationships, organizational strategies |
| [values-analyst](agents/values-analyst.md) | Values | Core vs. boundary vs. trade-able values; declared vs. revealed gaps from action evidence |
| [narrative-analyst](agents/narrative-analyst.md) | Self-story | Identity language, causal attribution, self-coined vs. AI-borrowed metaphors |

### Phase 1 Synthesis & QA

| Agent | Role |
|---|---|
| [meta-critic](agents/meta-critic.md) | Audits all four analysts against output contracts; issues per-analyst verdicts; drives the iteration loop |
| [synthesis-builder](agents/synthesis-builder.md) | Integrates all four frames into a single cross-frame synthesis; writes `system_of_values.md` |

### Phases 2–4 Builders

| Agent | Output |
|---|---|
| [cognitive-patterns-builder](agents/cognitive-patterns-builder.md) | Lexical fields, metaphor systems, question style, argument structure, emotional-rational oscillation |
| [knowledge-graph-builder](agents/knowledge-graph-builder.md) | Typed markdown nodes with seven edge types (tension, cause, derives, contradicts, reinforces, weakens, stands_for) |
| [behavioral-model-builder](agents/behavioral-model-builder.md) | BP files: trigger → response at low/medium/high intensity, modulators, recovery, inter-pattern relations |
| [behavior-brief-generator](agents/behavior-brief-generator.md) | Final ≤80-line brief in imperative form — every sentence must be directly actionable by the assistant |

---

## Methodology Principles

Every product is governed by a set of invariants applied consistently across all phases:

**Action over words.** Behavioral evidence outweighs self-report. What someone does under pressure reveals more than what they say about themselves.

**AI-anchoring filter.** A concept counts as the subject's only if they introduced or extended it in their own language. Statements that only echo Claude's framing are excluded from evidence.

**Cluster-boundary discipline.** High-confidence claims require evidence from at least two separate topic clusters. Single-cluster observations are flagged as provisional.

**Evidence hierarchy.** Pre-rational signals (physical reactions, slips, emotional outbursts) > concrete actions > subject correcting Claude > cross-cluster recurrence > single self-disclosure > AI-anchored statements.

**No new findings in the audit layer.** The meta-critic validates contracts and flags contradictions between analysts — it never introduces novel analysis of the subject.

**Output language matches source.** Every product is written in the dominant language of the source conversation. No translation.

**Privacy-neutral framework.** No identifying details about the subject appear in any shareable file (methodology, agents, skills). All personal data lives in `personalized/`, which is git-ignored.

---

## Project Structure

```
agent-twin/
├── agents/                              # 10 subagent system prompts
│   ├── affect-analyst.md                #   Phase 1
│   ├── social-dynamics-analyst.md       #   Phase 1
│   ├── values-analyst.md                #   Phase 1
│   ├── narrative-analyst.md             #   Phase 1
│   ├── meta-critic.md                   #   Phase 1 (QA gate)
│   ├── synthesis-builder.md             #   Phase 1 (synthesis)
│   ├── cognitive-patterns-builder.md    #   Phase 2
│   ├── knowledge-graph-builder.md       #   Phase 3
│   ├── behavioral-model-builder.md      #   Phase 4
│   └── behavior-brief-generator.md      #   Final compression
│
├── skills/                              # 7 SKILL.md files
│   ├── extract_gemini/                  #   Capture: Gemini import
│   ├── save_session/                    #   Capture: Claude Code session
│   ├── counselor/                       #   Capture: guided questionnaire
│   ├── run_pipeline/                    #   Analyze: full pipeline
│   ├── load_persona/                    #   Load: apply profile
│   ├── run_meta_critic/                 #   QA: standalone audit
│   └── validate_pipeline/               #   QA: methodology compliance
│
├── commands/                            # 6 slash command routers
├── methodology/                         # Design notes + output contract schema
├── scripts/
│   └── autosave_session.py              # Stop hook: capture on session exit
│
├── hooks/
│   └── hooks.json                       # Autosave hook configuration
│
├── CLAUDE.md                            # Project context for Claude Code
│
└── personalized/                        # ← git-ignored; all user data
    ├── saves/session/<date>_<id>/       #   Captured conversations
    └── results/profile/                 #   Compiled persona products
        ├── system_of_values.md          #   Phase 1 output (audited)
        ├── cognitive_patterns.md        #   Phase 2 output
        ├── knowledge_graph/             #   Phase 3 output
        ├── behavioral_model/            #   Phase 4 output (BP-XXX.md)
        └── behavior_brief.md            #   Final brief (loaded by /load_persona)
```

---

## Why agent-twin?

AI assistants adapt to tone and topic within a session — but start fresh every time. The patterns in how you think, what you value, and how you respond under pressure never carry over.

agent-twin solves this by treating your conversations as behavioral data. The four-frame pipeline extracts what words alone don't surface: the emotional architecture underneath how you argue, the value hierarchy revealed by what you refused, the power dynamics embedded in how you describe your relationships. These aren't inferred from self-report — they're derived from evidence across multiple independent analytical frames, audited for quality, and compressed into a format the assistant can actually use.

The goal is not to simulate you — it's to give the assistant enough context to stop making the same category of mistakes: explaining things you already know, missing the emotional register of a situation, recommending paths that contradict how you actually make decisions.

---

## License

MIT
