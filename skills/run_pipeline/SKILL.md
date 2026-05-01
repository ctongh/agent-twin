---
name: run_pipeline
description: Run the full agent-twin analysis pipeline on a saved session. Dispatches the four Phase 1 analyst subagents in parallel, runs the meta-critic audit loop, dispatches the synthesis-builder, then the Phase 2/3/4 builders, then the behavior-brief-generator. Produces all four detailed products plus behavior_brief.md. Use when the subject has captured at least one session via /save_session or /counselor and wants a persona profile built.
---

# run_pipeline

This skill is the single user-facing entry point for the batch layer. It runs the entire pipeline end-to-end: Phase 1 audited analysis → synthesis → Phase 2/3/4 builds → final compression to `behavior_brief.md`.

The skill **executes** the orchestration directly at the top level of the conversation, because Claude Code's general-purpose subagents do not have access to the `Task` tool — so the orchestration cannot be delegated to a single subagent. The skill is the runner; the actual analysts/builders are real Claude Code subagents at `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md`.

## When to use this vs. other skills

| Situation | Skill |
|-----------|-------|
| First-time pipeline build for a captured session | `/run_pipeline` (this skill) |
| Re-running the full pipeline after changes to source data | `/run_pipeline` |
| Auditing already-produced analyses (no re-build) | `/run_meta_critic` |
| Just want to load the existing profile in a new conversation | `/load_persona` |
| Capturing a new conversation | `/extract_<source>` or `/save_session` |

## Inputs

When invoked, accept arguments or ask the user for:

| Input | Description | Default |
|-------|-------------|---------|
| `session_id` | The session to analyze | the most recently modified session under `$HOME/.claude/agent-twin/personalized/saves/session/` |
| `context_background` | Optional one-paragraph context (role, life stage). Avoid identifying details. | empty |
| `subject_id` | Short label for the behavior_brief.md title | `Subject` |
| `max_iterations` | Cap on Phase 1 audit loop | `3` |

The skill auto-resolves:
- `input_path` → `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/annotated.txt`
- `source_json_path` → `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/conversation.json`
- `analyses_dir` → `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/analyses/`
- `profile_dir` → `$HOME/.claude/agent-twin/personalized/results/profile/`
- `agent_prompts_dir` → `${CLAUDE_PLUGIN_ROOT}/agents/`
- `build_timestamp` → today's ISO-8601 date

## Step 0 — Resume check (run BEFORE any other work)

The pipeline maintains state at two levels (per-session + global, see Step 1.6 for the full schema). Before doing anything else — before scanning the queue, before annotating, before dispatching any subagent — check whether a prior run left state behind. This handles two failure modes with one mechanism:

- **Crash recovery** — the SKILL was interrupted mid-pipeline (machine reboot, hook timeout, network drive hiccup).
- **Token-exhaustion mid-pipeline** — the user ran out of API budget mid-run; the SKILL crashed at whatever phase was active.

Both reduce to: state file says some phase is `in_progress` or `pending`, the rest of the pipeline did not run. Resume from the next non-complete boundary.

### Step 0.1 — Locate prior state

Read the **global** state file at `$HOME/.claude/agent-twin/personalized/results/profile/pipeline_state.json` if it exists.

Also scan per-session state files at `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/pipeline_state.json` for any session where `phases.analysts` is not `complete`.

### Step 0.2 — Branch on prior state

| Prior state | User-facing prompt | Action on Y / Yes / default | Action on N / No |
|---|---|---|---|
| No state files anywhere | (no prompt — fresh run) | Proceed to Step 1 | n/a |
| All phases (per-session `analysts` for all queued sessions AND global `phase1` / `phase2` / `phase3` / `phase4` / `final`) are `complete` AND `conversation_turns_at_analysis` matches current `turn_count` for every session | "This session already has a complete profile. Re-run the pipeline from scratch? [y/N]" | Archive existing state files (rename to `pipeline_state.<ISO-8601-timestamp>.json` in the same dir) and proceed to Step 1 as a fresh run. | Stop. Tell the user: "Nothing to do. Run `/load_persona` to use the existing profile, or `/show_persona` to inspect it." |
| Any phase is `in_progress` (a prior run was interrupted mid-phase) | "Found an interrupted pipeline run — last in-progress phase was `<phase_name>` at `<updated_at>`. Resume? [Y/n]" | Resume: leave state intact, proceed to Step 1, and per Step 1.6's resume rules re-dispatch the in-progress phase from scratch. | Archive prior state files and proceed to Step 1 as a fresh run. |
| Some phases `complete`, some `pending`, none `in_progress` (clean phase boundary; previous run finished a phase but never started the next) | "Found prior pipeline state — last completed phase was `<phase_name>`. Resume from `<next_phase_name>`? [Y/n]" | Resume: leave state intact, proceed to Step 1, and skip already-complete phases per their step-level skip rules. | Archive prior state files and proceed to Step 1 as a fresh run. |

**Archiving rule:** when the user declines a resume, do **not** delete prior state files. Rename them in place to `pipeline_state.<ISO-8601-with-no-colons>.json` (e.g. `pipeline_state.2026-04-29T142311.json`). This preserves audit trail and never destroys data on user decline.

### Step 0.3 — Why this naturally covers token exhaustion

If the user runs out of API budget mid-pipeline, the SKILL crashes wherever it was. The state file's last-written boundary marks the resume point. Next invocation hits Step 0, sees one phase `in_progress`, offers resume. No special-case code is needed — it's the same crash-recovery path.

### Step 0.4 — What this is NOT

- **No mid-subagent checkpointing.** A subagent's internal progress is opaque; if it dies, we restart the whole subagent. That's acceptable: cost of one rerun is small compared to the complexity of recovering partial outputs.
- **No partial Phase-1 recovery.** If three of four analysts completed and the fourth died, we re-dispatch all four (Phase 1 Step 1 is the boundary). The analysts are designed to overwrite their outputs deterministically.
- **No separate `/resume_pipeline` command.** Resume lives inside `/run_pipeline`'s start path.

## Step 1 — Build the session queue

**Pre-check: is there data to analyze?**

If `$HOME/.claude/agent-twin/personalized/saves/session/` has no subdirectories containing `conversation.json`, stop and tell the user — in their language — to run `/counselor` first. Do not launch it automatically.

**Counselor reminder (soft):**

If `$HOME/.claude/agent-twin/personalized/results/profile/behavior_brief.md` does not yet exist, add one short informational line suggesting they run `/counselor` at least once for better analysis quality. Do not block on this.

**Build the queue:**

Scan every subdirectory under `$HOME/.claude/agent-twin/personalized/saves/session/` that contains a `conversation.json`. For each session, read its `session_meta.json` (for `turn_count`) and `pipeline_state.json` (for `conversation_turns_at_analysis` and `phases`).

**Defensive fallback for missing `session_meta.json`:** if the meta file does not exist (e.g. a legacy capture from before the `extract_gemini` schema fix, or a partially-written session), do not error. Instead, compute `turn_count` by loading `conversation.json` and using `len(data)` (the file is a JSON array of `{order, user, model}` objects per `scripts/autosave_session.py`'s schema). Log a single one-line warning — in the user's language — that meta is missing for this session and the count was inferred. Then proceed as normal.

Apply this logic:

| Condition | Action |
|-----------|--------|
| No `pipeline_state.json` exists | Add to queue — never analyzed |
| `phases.final != "complete"` | Add to queue — was interrupted |
| Current `turn_count` > `conversation_turns_at_analysis` | Add to queue — has new content |
| Current `turn_count` == `conversation_turns_at_analysis` AND `final == "complete"` | Skip — already up to date |

If the user specified a `session_id` explicitly, process only that session (bypass queue scan).

**Sort and display:**

Sort the queue by session directory creation date, oldest first. Tell the user — in their language — how many sessions are queued and the estimated total time (~35 min per session; 5 sessions ≈ ~3 hours). Then proceed without waiting for confirmation.

If the queue is empty, tell the user everything is already up to date.

**Directory setup:**

Pre-create `$HOME/.claude/agent-twin/personalized/results/profile/analyses/`, `knowledge_graph/concepts/`, `knowledge_graph/emotions/`, `knowledge_graph/people/`, `knowledge_graph/events/`, and `behavioral_model/` before dispatching any agents.

## Step 1.5 — Per-session annotated.txt

For **each session in the queue**, check if `annotated.txt` exists.

- If it exists: proceed.
- If missing: generate it by reading `conversation.json` and inserting sequential topic cluster headers (`[Cluster 01]`, `[Cluster 02]`, …) every 5–8 turns based on topic shifts. Tell the user — in their language — what you are doing and that it will continue automatically. Write to `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/annotated.txt`.

## Step 1.6 — Pipeline state files (checkpoint / resume detail)

State is split across two files — one per-session (covers what's specific to a single capture: annotation + analysts) and one global (covers everything cumulative: meta-critic, synthesis, phase 2/3/4, brief).

### Per-session state file

Path: `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/pipeline_state.json`

Schema:
```json
{
  "session_id": "<session_id>",
  "conversation_turns_at_analysis": 0,
  "started_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>",
  "phases": {
    "annotated_txt": "pending|in_progress|complete",
    "analysts":      "pending|in_progress|complete"
  },
  "phase1_iterations": 0,
  "phase1_escalated": false,
  "notes": ""
}
```

`notes` is a free-text scratch field the SKILL may append to for resume context (e.g. "iter 2 escalated due to evidence gap on values"). Optional; do not require it for parsing.

### Global state file

Path: `$HOME/.claude/agent-twin/personalized/results/profile/pipeline_state.json`

Schema:
```json
{
  "last_session_id": "<most-recently-processed-session-id>",
  "started_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>",
  "phases": {
    "phase1":  "pending|in_progress|complete",
    "phase2":  "pending|in_progress|complete",
    "phase3":  "pending|in_progress|complete",
    "phase4":  "pending|in_progress|complete",
    "final":   "pending|in_progress|complete"
  },
  "phase1_iteration_count": 0,
  "phase1_meta_critic_verdict": "accept|iterate|escalate|null",
  "phase1_escalated": false,
  "notes": ""
}
```

`phase1` is the cumulative meta-critic + synthesis pass run **after** all queued sessions have completed their per-session `analysts` phase. The four downstream phases plus the final brief are then run once each.

### Atomic writes are mandatory for state files

Both state files must be written **atomically**. A killed process (Ctrl-C, OS shutdown, network drive hiccup, token exhaustion crashing the SKILL) must not leave a half-written state file at the canonical path — that would brick the resume protocol.

Use this pattern in any environment that supports it:

1. Write the new content to `<path>.tmp` first.
2. Then perform a same-volume rename (`mv -f`, `os.replace`, `Move-Item -Force`) onto the final path.

The autosave Stop hook (`scripts/autosave_session.py`) ships with an `atomic_write_text` helper — use the same approach here. If the SKILL is invoking the Write tool directly, the rename-into-place step matters more than the temp filename: write fresh content in a single Write call (not append-then-truncate). Treat any state file with an unparseable JSON tail as corrupt, archive it (rename to `pipeline_state.corrupt.<timestamp>.json`), and treat that session/global slot as fresh.

### Per-session state update protocol

- Before generating annotated.txt: set `annotated_txt` → `in_progress` (atomic write)
- After annotated.txt written: set `annotated_txt` → `complete` (atomic write)
- Before dispatching analysts: set `analysts` → `in_progress` (atomic write)
- After analysts complete and output is verified: set `analysts` → `complete` AND set `conversation_turns_at_analysis` to the current turn count (atomic write)
- After each Phase 1 meta-critic iteration: increment `phase1_iterations` and (post-loop) record `phase1_escalated` (atomic write)
- Write using the Write tool — never delegate to a subagent.

### Global state update protocol

- Before running global Phase 1 (meta-critic + synthesis on cumulative analyses): set `phase1` → `in_progress`; record `started_at` if first run (atomic write)
- After global Phase 1 completes: set `phase1` → `complete`; record `phase1_iteration_count`, `phase1_meta_critic_verdict`, `phase1_escalated` (atomic write)
- At the start of each downstream phase: set the corresponding key (`phase2`, `phase3`, `phase4`, `final`) → `in_progress` (atomic write)
- At the successful end of each downstream phase: set the corresponding key → `complete` (atomic write)
- On final brief written and verified: set `final` → `complete`; refresh `updated_at` (atomic write)

### Cleanup after a successful run

Keep the state files. They are useful on the next invocation (Step 0 will see all phases `complete` and prompt for re-run). Do not delete them at end of pipeline.

### Resuming an interrupted session in the queue

If a session's per-session state shows `analysts: in_progress` (was interrupted mid-analysis), re-run its analysts from scratch. The analysts will re-read the cumulative report and the full session — no data is lost. Same logic applies to global phases marked `in_progress`: re-dispatch the corresponding builder.

## Step 2 — Pre-flight notice

Print a brief notice — in the user's language — that covers:
- Session being analyzed (`<session_id>`)
- Estimated time: **~35 minutes per session** (5 sessions ≈ ~3 hours). Phase 3 and Phase 4 are the heavy parts (~10 min each).
- What each phase does (one line each: four analysts in parallel → quality check → synthesis; language patterns; knowledge graph; behavioral model; final collaboration brief)
- An encouraging line — something warm that acknowledges this is meaningful work and they're on their way

### Step 2.1 — Soft cost preflight

Before dispatching any subagent, compute a back-of-envelope cost estimate for the queue. This is informational only — do **not** wait for confirmation.

Procedure:
1. For each session in the queue, get the byte size of its `annotated.txt` (or, if not yet generated, of `conversation.json`). Sum across the queue to get `total_bytes`.
2. Approximate input tokens: `tokens ≈ total_bytes / 4` (1 token ≈ 4 chars heuristic; works for ASCII and is a slight overestimate for CJK, which is fine for a soft estimate).
3. Approximate dispatch count per session: 4 phase-1 analysts × up to 3 iterations + 1 meta-critic + 1 synthesis + 3 builders (cognitive / knowledge graph / behavioral) + 1 brief generator ≈ **10–13 subagent calls per session**, each reading the full annotated.txt for that session. Use **12** as a working midpoint per session.
4. Total tokens read across the run ≈ `tokens × 12` (rough; the brief generator reads the products instead of annotated.txt, so this slightly overcounts — acceptable for a soft estimate).

Print **one line** before dispatch, in the user's language, of the form:

```
Estimated work: <N> session(s), ~<X>K tokens read across ~<M> subagent calls. Proceeding...
```

Where:
- `<N>` = number of sessions in the queue
- `<X>` = `round((tokens × 12) / 1000)` (rounded to nearest thousand)
- `<M>` = `N × 12` (working midpoint)

**Do not ask for confirmation.** The user already invoked this skill deliberately. Just start immediately after the line.

Then proceed immediately to Step 3.

## Step 3 — Execute the protocol at top-level

Each Task dispatch uses:
- `subagent_type`: matches the `name:` field in the agent's frontmatter
- `description`: short label
- `prompt`: lists the input variables the agent expects — do **not** re-include the system prompt

### Loop: for each session in queue (oldest first)

Repeat the following block for every session in the queue before proceeding to the global phases.

---

**Skip analysts for this session if its state shows `analysts: complete` AND `conversation_turns_at_analysis` equals current turn count** (already fully analyzed, nothing new). Otherwise proceed.

Update session state: set `analysts` → `in_progress`.

### Phase 1 Step 1 — analysts in parallel

Dispatch all four analyst Task calls **in a single message** so they run concurrently:

```
Task(subagent_type="affect-analyst", description="affect Phase 1 iter <N>", prompt="...")
Task(subagent_type="social-dynamics-analyst", description="social Phase 1 iter <N>", prompt="...")
Task(subagent_type="values-analyst", description="values Phase 1 iter <N>", prompt="...")
Task(subagent_type="narrative-analyst", description="narrative Phase 1 iter <N>", prompt="...")
```

Per-analyst task prompt template:

```
You are the <analyst-name>. Inputs:
- INPUT_PATH: <full path to annotated.txt>
- SESSION_ID: <session id>
- CONTEXT_BACKGROUND: <text or empty>
- ITERATION_FEEDBACK: <empty on iter 1; otherwise the meta-critic's per-analyst revision instructions>
- EXISTING_REPORT_PATH: <path to results/profile/analyses/<analyst>.md if it exists, else empty>

Follow your system prompt's protocol and return the report.
```

Wait for all four to complete. Save each subagent's returned text to `<analyses_dir>/<short-name>.md` where:

| Subagent | Short name |
|---|---|
| `affect-analyst` | `affect` |
| `social-dynamics-analyst` | `social` |
| `values-analyst` | `values` |
| `narrative-analyst` | `narrative` |

### Phase 1 Step 2 — meta-critic

Dispatch:

```
Task(subagent_type="meta-critic", description="meta-critic iter <N>", prompt="...")
```

Task-prompt variables:
- `ANALYSES_DIR`: <analyses_dir>
- `AGENT_PROMPTS_DIR`: `${CLAUDE_PLUGIN_ROOT}/agents/`
- `SOURCE_DATA_PATH`: <input_path>
- `SESSION_ID`: <session id>
- `ITERATION`: <N>

Save the returned report to `<analyses_dir>/meta_critic.md`.

### Phase 1 Step 3 — process verdict

Parse the meta-critic's `Loop Decision` section.

| Decision | Action |
|---|---|
| `accept` | Exit loop. Proceed to Step 4. |
| `iterate` AND `iteration < max_iterations` | Build per-analyst `iteration_feedback` from meta-critic's revision instructions. Increment `iteration`. Return to Step 1, dispatching **only the analysts marked `needs_revision`**. Other analysts' outputs from the previous iteration carry forward unchanged. |
| `iterate` AND `iteration == max_iterations` | Exit loop with `escalated: true`. Proceed to Step 4. |
| `escalate` | Exit loop with `escalated: true`. Proceed to Step 4. |

### Phase 1 Step 4 — synthesis-builder (produces both synthesis.md and system_of_values.md)

Dispatch the synthesis-builder as its own stage:

```
Task(subagent_type="synthesis-builder", description="synthesis Phase 1", prompt="...")
```

Task-prompt variables:
- `ANALYSES_DIR`: <analyses_dir>
- `OUTPUT_PATH`: `<analyses_dir>/synthesis.md`
- `VALUES_OUTPUT_PATH`: `<profile_dir>/system_of_values.md`
- `SESSION_ID`: <session id>
- `ESCALATED`: `true` if the loop exited via escalation, else `false`

The synthesis-builder writes both files directly: `synthesis.md` for downstream builders and `system_of_values.md`. Verify both exist before proceeding.

**After synthesis completes — end of per-session analyst loop:**

Save each analyst's returned report to both:
- `$HOME/.claude/agent-twin/personalized/saves/session/<session_id>/analyses/<short-name>.md` (session-specific copy for traceability)
- `$HOME/.claude/agent-twin/personalized/results/profile/analyses/<short-name>.md` (cumulative — overwrite with this updated version)

Update session state: set `analysts` → `complete`, `conversation_turns_at_analysis` = current turn count, `phase1_iterations` = N, `phase1_escalated` = true/false.

**→ Repeat loop for next session in queue, if any.**

---

### Global phases (run once, after all sessions in queue are processed)

Update global state (`results/profile/pipeline_state.json`): set `phase1` → `in_progress`.

Run meta-critic on `results/profile/analyses/` (the cumulative reports). Then synthesis-builder. Update global state: set `phase1` → `complete`.

### Phase 2 — cognitive-patterns-builder

**Skip if `pipeline_state.phases.phase2 == "complete"` and verification passed.**

Update state: set `phase2` → `in_progress`.

```
Task(subagent_type="cognitive-patterns-builder", description="cognitive patterns build", prompt="...")
```

Task-prompt variables: `SOURCE_JSON_PATH`, `SESSION_ID`, `OUTPUT_PATH=<profile_dir>/cognitive_patterns.md`.

Verify it exists before proceeding. Update state: set `phase2` → `complete`.

### Phase 3 — knowledge-graph-builder

**Skip if `pipeline_state.phases.phase3 == "complete"` and verification passed.**

Update state: set `phase3` → `in_progress`.

**Existing-graph mode:** If prior profile results exist and `phase1` was not re-run this session, set `EXISTING_GRAPH=true` (merge mode). Otherwise fresh-build: clear `<profile_dir>/knowledge_graph/` before dispatch.

```
Task(subagent_type="knowledge-graph-builder", description="knowledge graph build", prompt="...")
```

Task-prompt variables: `SYNTHESIS_PATH=<analyses_dir>/synthesis.md`, `ANALYSES_DIR`, `SESSION_ID`, `GRAPH_DIR=<profile_dir>/knowledge_graph/`, `EXISTING_GRAPH=<true|false>`.

Verify nodes were created. Update state: set `phase3` → `complete`.

### Phase 4 — behavioral-model-builder

**Skip if `pipeline_state.phases.phase4 == "complete"` and verification passed.**

Update state: set `phase4` → `in_progress`.

**Existing-model mode:** If prior profile results exist and `phase1` was not re-run this session, set `EXISTING_MODEL=true` (merge mode). Otherwise fresh-build: clear `<profile_dir>/behavioral_model/` of all prior `BP-*.md` and `README.md` before dispatch.

```
Task(subagent_type="behavioral-model-builder", description="behavioral model build", prompt="...")
```

Task-prompt variables: `SYNTHESIS_PATH=<analyses_dir>/synthesis.md`, `ANALYSES_DIR`, `SESSION_ID`, `GRAPH_DIR=<profile_dir>/knowledge_graph/`, `BEHAVIOR_DIR=<profile_dir>/behavioral_model/`, `EXISTING_MODEL=<true|false>`.

Verify pattern files were created. Update state: set `phase4` → `complete`.

### Final — behavior-brief-generator

**Skip if `pipeline_state.phases.final == "complete"` and verification passed.**

Update state: set `final` → `in_progress`.

```
Task(subagent_type="behavior-brief-generator", description="behavior brief generation", prompt="...")
```

Task-prompt variables: `PROFILE_DIR=<profile_dir>`, `OUTPUT_PATH=<profile_dir>/behavior_brief.md`, `SUBJECT_ID=<subject_id>`, `BUILD_TIMESTAMP=<today's ISO-8601 date>`.

Verify `<profile_dir>/behavior_brief.md` exists and is ≤80 lines. Update state: set `final` → `complete`.

The full pipeline run is long (~35 minutes typical for a single session; 5 sessions ≈ ~3 hours). Inform the user that the dispatch has started and report progress between phase boundaries.

## Step 4 — Surface the execution log

When all phases complete, surface to the user:

1. **Phase 1 result** — iterations completed, escalation flag, per-analyst final verdict
2. **Per-phase product paths** — system_of_values.md, cognitive_patterns.md, knowledge_graph/, behavioral_model/
3. **behavior_brief.md** — line count, path
4. **Any caveats** from the synthesis Pipeline Caveats section

Example surface format:

```
Pipeline complete for session <session_id>.
  Phase 1: <N> iteration(s), <accepted|escalated>
    affect:    pass / pass_with_warnings / escalated
    social:    ...
    values:    ...
    narrative: ...
  Phase 1 synthesis: <analyses_dir>/synthesis.md
  Phase 2: cognitive_patterns.md (<lines> lines)
  Phase 3: knowledge_graph/ (<concept_count> concepts, <person_count> people, ...)
  Phase 4: behavioral_model/ (<pattern_count> patterns)
  Final:   behavior_brief.md (<lines> lines)

Caveats:
  - [list from synthesis Pipeline Caveats, if any]

Next: invoke /load_persona in a new conversation to make the profile active.
```

## Step 5 — Suggest next action

Based on the result:

| Outcome | Recommendation |
|---------|----------------|
| Phase 1 accepted, all phases produced | "Pipeline complete. Open a new Claude Code session and run `/load_persona`, or use `/counselor` to continue building context." |
| Phase 1 escalated | "Phase 1 could not converge; the synthesis was produced with caveats. Read `<analyses_dir>/meta_critic.md` for unresolved concerns. The downstream phases ran but you may want to address the caveats and re-run." |
| A downstream builder produced no output | "Builder <name> did not write to its expected path — check the Task return text for the error and the agent's completion checklist." |

## Completion checklist

- [ ] Inputs were resolved (or asked of the user) before dispatching
- [ ] All required source files for the session exist
- [ ] Phase 1 Step 1 dispatched all four analysts in a single message (parallel)
- [ ] Re-dispatch on iterate only included analysts marked `needs_revision`
- [ ] `synthesis-builder` was dispatched as a separate stage after the meta-critic verdict
- [ ] All five product paths were verified to exist
- [ ] Caveats from Pipeline Caveats were preserved (not silently dropped)
- [ ] Next-action recommendation was given

## Why this skill exists

Running the pipeline manually means resolving every variable, dispatching every analyst, running the meta-critic loop, dispatching the synthesis-builder, then the three downstream builders, then the brief generator — by hand. This skill collapses that to a single invocation. It is the natural Claude Code idiom: skills hide complexity behind a one-line user-facing entry point.

**Why the skill, not an agent, is the runner**: Claude Code subagents do not have access to the `Task` tool. If the orchestration were delegated to a subagent, that subagent could not fan out parallel sub-dispatches — it would have to role-play all four analysts in a single context, losing the cross-agent triangulation that justifies the four-frame design. Skills run at the top-level conversation context, where `Task` is available, so the skill can issue real parallel dispatches against real Claude Code subagents (one fresh context per analyst, with its own system prompt and tool restrictions).

## Out of scope

- Incremental pipeline runs (rebuilding only one phase) — for now, the pipeline always runs end-to-end. Incremental dispatch is a planned roadmap item.
- Cross-session integration — when multiple sessions exist, this skill currently runs per-session. Cross-session merge is a planned roadmap item.
- Auto-loading the profile after build — by design, `/load_persona` must be invoked explicitly so the user perceives the before/after difference.

Pipeline complete. Next: run `/load_persona` to apply the brief to this session, or `/show_persona` to inspect what was built.
