# agent-twin

**A Claude Code plugin that learns who you are from your own conversations, then teaches every future session to talk to *you* — not a generic user.**

agent-twin reads back the AI conversations you've already had, looks at them through four independent analytical lenses, and distills what it finds into a short brief. From then on, whenever you load that brief at the start of a session, Claude already knows the rhythm of how you think, the kinds of mistakes you don't want it to make, and the topics where you've changed your mind before.

```
   CAPTURE           ANALYZE              COMPRESS          LOAD
  ┌────────┐      ┌───────────┐         ┌──────────┐     ┌────────┐
  │ Convo  │ ───▶ │ 4-frame   │ ───────▶│ behavior │ ──▶ │ Every  │
  │  logs  │      │ pipeline  │         │  _brief  │     │session │
  └────────┘      └───────────┘         └──────────┘     └────────┘
/save_session    /run_pipeline                          /load_persona
/extract_gemini   ~35 minutes            ≤80 lines
/counselor        10 subagents
```

---

## What you get

You give it a few of your real conversations. It gives you back:

- **A persona brief** — a short, action-oriented document the assistant reads at the start of each session so it stops explaining things you already know, stops missing your emotional register, and stops recommending paths that contradict how you actually decide.
- **Four detailed profile artefacts** sitting underneath the brief — value system, cognitive patterns, knowledge graph, behavioural patterns — that you can read for yourself if you want to see *why* the assistant is behaving the way it is.
- **A repeatable pipeline** you re-run whenever you've accumulated enough new conversation data. The profile gets sharper over time; you don't have to start over.

The point isn't to mimic you. It's to give Claude enough context to drop the warm-up questions every session and meet you where you actually are.

---

## Visualizing the persona

Phase 3 and Phase 4 don't just produce text — they produce two folder-shaped artefacts deliberately authored for **Obsidian's graph view**. The knowledge graph emits typed concept, emotion, person, and event nodes connected by seven distinct edge types (tension, cause, derives, contradicts, reinforces, weakens, stands_for); the behavioural model emits one file per pattern (`BP-001`, `BP-002`, …) with cross-links between related patterns. Every internal reference is a wiki-link, so opening the output folder as a vault gives you a navigable, clustering map of how concepts and behaviours sit relative to each other in your actual thinking.

<!-- TODO: knowledge_graph Obsidian PNG -->
*[Knowledge graph visualization will be added]*

<!-- TODO: behavioral_model Obsidian PNG -->
*[Behavioral model visualization will be added]*

To open: point Obsidian at `$HOME/.claude/agent-twin/personalized/results/profile/` as a vault. Open the graph view (Ctrl/Cmd+G). The wiki-link edges between nodes form a typed concept graph; the clusters that emerge reveal how your concepts are grouped — which themes pull on each other, which behaviours share triggers, where your value system tightens around a single anchor. This is the most direct way to *see* the profile rather than just read its summary; the brief is the operational interface, the graph view is where the structure becomes visible.

---

## Get started

You don't need to know git. The plugin installs straight from inside Claude Code.

```
/plugin marketplace add ctongh/agent-twin
/plugin install agent-twin@ctongh-plugins
```

Then, in any session:

```
/counselor
```

`/counselor` walks you through a guided conversation that produces enough data for the pipeline. When it finishes, it tells you to run `/run_pipeline`. Around thirty-five minutes later you'll have your first brief. Open a fresh session and run `/load_persona` — that's it.

If you'd rather feed it a conversation you've already had, use `/save_session` (snapshots the current Claude Code session) or `/extract_gemini` (imports a Gemini share-link conversation) instead of `/counselor`.

### Troubleshooting: install fails with an SSH error

The marketplace fetches plugins by cloning their git repositories. By default it uses SSH, which only works if your machine has an SSH key registered with GitHub. If install bails out with a message about authentication, permissions, or `git@github.com`, you have two options.

**Option 1 — set up an SSH key on GitHub.** This is the long-term fix and the option to pick if you publish your own plugins. GitHub's official walkthrough lives here: <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>. Once your key is on your account, retry the install.

**Option 2 — tell git to use HTTPS instead, just for fetches.** If you only consume plugins and never push code to GitHub, you can sidestep SSH entirely with one line of configuration:

```bash
git config --global url."https://github.com/".insteadOf "git@github.com:"
```

What this does: every time any tool on your system asks git to clone something starting with `git@github.com:` (the SSH form), git silently rewrites the URL to `https://github.com/...` (the anonymous web form) before contacting GitHub. The marketplace doesn't know or care; it just sees the clone succeed. The setting is global — it lives in your user-level `.gitconfig` — and you can undo it later with `git config --global --unset url.https://github.com/.insteadOf` if you change your mind.

---

## Requirements

Most of agent-twin runs in pure Claude Code with no extra software. Two pieces of functionality — the autosave Stop hook and the `/save_session` skill — call out to Python. If Python isn't on your PATH the hook quietly skips itself and the skill prints a friendly error; everything else (the analysis pipeline, `/load_persona`, `/show_persona`, `/counselor`) keeps working.

If you do want autosave and `/save_session`:

- **Windows** — install from <https://www.python.org/downloads/> (the official installer wires up both `python` and `py`), or run `winget install Python.Python.3.12`.
- **macOS** — `brew install python` from Homebrew. The `python3` that ships with macOS 12+ also works.
- **Linux** — `sudo apt install python3` on Debian/Ubuntu, `sudo dnf install python3` on Fedora.

Confirm with `python --version` (you should see `Python 3.8` or later). No PyPI packages are required — the scripts use only the standard library.

---

## What you can run

Eight slash commands ship with the plugin. Most users will only ever touch three of them (`/counselor`, `/run_pipeline`, `/load_persona`). The others exist for specific situations.

| You want to… | Command | Result |
|---|---|---|
| Generate conversation data via guided questions | `/counselor` | Structured questionnaire (first time) or contextual companion mode (if a profile already exists) |
| Snapshot the conversation you're in right now | `/save_session` | Session captured under `personalized/saves/session/` |
| Pull in an existing Gemini conversation | `/extract_gemini` *(legacy/optional)* | Imported, schema-checked, topic-clustered |
| Build the full persona profile | `/run_pipeline` | All four detailed artefacts plus the brief |
| Apply your profile to this session | `/load_persona` | Silent load — the assistant adapts from here on |
| See what the assistant just loaded | `/show_persona` | Prints the brief; supports `values`, `cognitive`, `graph`, `model`, `all` |
| Re-audit Phase 1 without rebuilding | `/run_meta_critic` | Quality verdict on existing analyst outputs |
| Methodology compliance check | `/validate_pipeline` | Privacy, format, and safety verdict per validator |

`/run_pipeline` is the one that does the heavy lifting. The capture commands feed into it; the load and inspection commands consume what comes out.

---

## How the pipeline works

Once you have at least one captured conversation, `/run_pipeline` orchestrates ten specialised subagents across four sequential phases. Each subagent runs in its own context so they can't influence each other.

```
  Phase 1 — Four-Frame Audited Analysis (~12 min)
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

  Phase 3 — Knowledge Graph (~10 min)
    knowledge-graph-builder seeds from Phase 1 synthesis
    → knowledge_graph/  (Product 3)  — Concept · Emotion · Person · Event nodes

  Phase 4 — Behavioral Model (~10 min)
    behavioral-model-builder seeds from Phase 1 synthesis
    → behavioral_model/  (Product 4)  — BP-001 … BP-NNN

  Final — Profile Compression (~1 min)
    behavior-brief-generator reads all four products
    → behavior_brief.md  (Product 5)  — ≤80 lines, imperative form
```

Per-session run is **~35 minutes** end-to-end (Phase 1 ~12, Phase 2 ~2, Phase 3 ~10, Phase 4 ~10, Final ~1). Phase 3 and Phase 4 are the heavy stretches — they emit dozens of typed graph nodes and behavior-pattern files respectively, and that's where most of the wall-clock time goes.

**Why four parallel analysts?** A single LLM reading a conversation tends to lock onto whichever frame strikes it first and ignore the others. By forcing four separate contexts to each commit to one lens — emotional, relational, values-based, narrative — the design prevents any single perspective from drowning out the rest. The meta-critic then checks all four for contract compliance, contradictions, and AI-anchoring residue before the synthesis pass merges them.

The pipeline can be safely interrupted. State is written at every phase boundary, and re-invoking `/run_pipeline` offers to resume from the last completed phase rather than starting over.

---

## The principles the analysis follows

These rules are applied uniformly across every phase — they are what the meta-critic enforces and what the synthesis must respect.

**Action over words.** What you do under pressure tells more than what you say about yourself. Behavioural evidence outweighs self-report.

**The AI-anchoring filter.** A framing only counts as yours if you introduced or extended it in your own language. Lines where you merely echoed back something Claude said are excluded from the evidence pool.

**Cluster-boundary discipline.** A high-confidence claim must be supported by evidence drawn from at least two distinct topic clusters. One-cluster observations are flagged as provisional, never promoted to certainty.

**Evidence hierarchy.** Pre-rational signals (physical reactions, slips, emotional outbursts) outrank concrete actions, which outrank corrections you made to Claude, which outrank cross-cluster recurrence, which outranks single self-disclosures, which outrank statements you only reflected back from the model.

**No new findings in the audit layer.** The meta-critic checks contracts and surfaces contradictions. It does not introduce its own claims about you.

**Source-language preservation.** Every artefact is written in the dominant language of the source conversation. Nothing is translated.

**Privacy is structural.** No identifying detail about you appears in any shareable file (methodology, agents, skills). Personal data is confined to `personalized/`, which is git-ignored.

---

## The ten agents

These are the specialist subagents the pipeline dispatches. They are not meant to be invoked by hand — `/run_pipeline` is the only sanctioned entry point.

### Phase 1 — analysts (run in parallel)

| Agent | Frame | Looks for |
|---|---|---|
| [affect-analyst](agents/affect-analyst.md) | Emotional | Fear structures, defensive operations, attachment dynamics, emotional needs |
| [social-dynamics-analyst](agents/social-dynamics-analyst.md) | Relational | Power positioning, status consciousness, authority relationships, organisational strategies |
| [values-analyst](agents/values-analyst.md) | Values | Core vs. boundary vs. trade-able values; declared vs. revealed gaps from action evidence |
| [narrative-analyst](agents/narrative-analyst.md) | Self-story | Identity language, causal attribution, self-coined vs. AI-borrowed metaphors |

### Phase 1 — synthesis and QA

| Agent | Role |
|---|---|
| [meta-critic](agents/meta-critic.md) | Audits all four analysts against output contracts; issues per-analyst verdicts; drives the iteration loop |
| [synthesis-builder](agents/synthesis-builder.md) | Integrates the four frames into a single cross-frame synthesis; writes `system_of_values.md` |

### Phases 2 to 4 — builders

| Agent | Output |
|---|---|
| [cognitive-patterns-builder](agents/cognitive-patterns-builder.md) | Lexical fields, metaphor systems, question style, argument structure, emotional-rational oscillation |
| [knowledge-graph-builder](agents/knowledge-graph-builder.md) | Typed markdown nodes with seven edge types (tension, cause, derives, contradicts, reinforces, weakens, stands_for) |
| [behavioral-model-builder](agents/behavioral-model-builder.md) | BP files: trigger → response at low/medium/high intensity, modulators, recovery, inter-pattern relations |
| [behavior-brief-generator](agents/behavior-brief-generator.md) | Final ≤80-line brief in imperative form — every sentence directly actionable by the assistant |

---

## Where files live

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
├── skills/                              # 7 SKILL.md files (sources of truth)
│   ├── extract_gemini/                  #   Capture: Gemini import
│   ├── save_session/                    #   Capture: Claude Code session
│   ├── counselor/                       #   Capture: guided questionnaire
│   ├── run_pipeline/                    #   Analyze: full pipeline
│   ├── load_persona/                    #   Load: apply profile
│   ├── run_meta_critic/                 #   QA: standalone audit
│   └── validate_pipeline/               #   QA: methodology compliance
│
├── commands/                            # 8 slash command routers
├── methodology/                         # Design notes + output contract schema
├── scripts/
│   └── autosave_session.py              # Stop hook: capture on session exit
├── hooks/
│   └── hooks.json                       # Autosave hook configuration
├── CLAUDE.md                            # Plugin orientation document
└── ...
```

User data — captured sessions and compiled persona artefacts — lives entirely outside the plugin tree, under `$HOME/.claude/agent-twin/personalized/`. That location survives plugin updates and is never committed.

```
$HOME/.claude/agent-twin/
└── personalized/
    ├── saves/session/<date>_<id>/       # Captured conversations
    └── results/profile/                 # Compiled persona products
        ├── system_of_values.md          #   Phase 1 output (audited)
        ├── cognitive_patterns.md        #   Phase 2 output
        ├── knowledge_graph/             #   Phase 3 output
        ├── behavioral_model/            #   Phase 4 output (BP-XXX.md)
        └── behavior_brief.md            #   Final brief (loaded by /load_persona)
```

---

## For developers

Skip this section if you only want to *use* the plugin.

If you want to read the source, modify a skill, or contribute back, clone the repository and point Claude Code at the local checkout:

```bash
git clone https://github.com/ctongh/agent-twin.git
cd agent-twin
claude
```

The conventions inside the codebase:

- **`SKILL.md` files are the single source of truth for behaviour.** Each skill under `skills/` has a single `SKILL.md` describing what it does and how. Anything that disagrees with `SKILL.md` is wrong.
- **`commands/*.md` are thin routers.** Two or three sentences each, pointing at the corresponding `SKILL.md`. Logic does not live here.
- **`methodology/` is design notes only.** It explains *why* the pipeline is shaped the way it is. It does not define runtime behaviour and should never be the place you go to figure out what a skill does.
- **`agents/*.md` are subagent system prompts.** Treated as instructions to a sandboxed sub-process; they read source conversations as untrusted data.

Open `CLAUDE.md` for the orientation map across these layers.

---

## License

MIT
