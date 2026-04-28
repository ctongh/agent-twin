---
name: orchestration_protocol
role: Pipeline orchestration protocol — followed by the /run_pipeline skill at top-level
output_language: derived_from_input
---

# Orchestration Protocol

> **Reading guide.** This file is the **orchestration protocol** for the agent-twin pipeline. It is **not** a dispatchable subagent — Claude Code's general-purpose subagents do not have access to the `Task` tool, so a subagent cannot fan out parallel sub-dispatches. Instead, this protocol is followed by the `/run_pipeline` skill at the **top level** of the conversation, where the `Task` tool is available. The skill reads this file, then issues the Task calls described below directly.
>
> An LLM reading this file may follow it sequentially in a single context (without parallel fan-out) as a fallback when nested Task is unavailable, but it loses the cross-agent triangulation that justifies the four-frame design.
>
> For the *why* behind the pipeline architecture, the four-frame design, the audit loop, and the methodological invariants, read `methodology/pipeline.md` instead.

## Identity

The **orchestration runner** is the conversation context that follows this protocol. In the canonical case this is the `/run_pipeline` skill executing at the top level, where the `Task` tool is available. Its responsibilities, in order:

1. **Phase 1 — audited four-frame analysis.** Dispatch four analyst subagents in parallel; run `meta-critic`; iterate until accept or escalate (max 3 iterations); dispatch `synthesis-builder` to produce the synthesis that becomes `system_of_values.md`.
2. **Phase 2 — cognitive patterns build.** Dispatch `cognitive-patterns-builder`. No audit.
3. **Phase 3 — knowledge graph build.** Dispatch `knowledge-graph-builder` with Phase 1 seeds as input. No audit.
4. **Phase 4 — behavioral model build.** Dispatch `behavioral-model-builder` with Phase 1 seeds as input. No audit.
5. **Final compression.** Dispatch `profile-compressor` with all four product paths; emit `user_profile.md`.
6. **Final report.** Return a brief execution log to the caller (typically the `/run_pipeline` skill).

The runner adds **no new analysis** of its own. It coordinates, dispatches, and verifies each step's output exists at the expected path before proceeding.

## Dispatch protocol

The 10 subagents live as Claude Code subagent files at `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md` (project root). Each file declares its own `name:`, `description:`, `model:`, and `tools:` in frontmatter; the system prompt body is loaded as-is when Claude Code spawns the subagent.

Throughout this protocol, "dispatch via the Task tool" means: issue a `Task` call with:
- `subagent_type: <agent name>` (matches the `name:` field in the subagent's frontmatter; e.g., `affect-analyst`, `meta-critic`, `synthesis-builder`)
- `description`: a short label (e.g. `affect-analyst Phase 1 iter 1`)
- `prompt`: the task prompt — a short message providing the input variables the subagent's system prompt references (e.g. `INPUT_PATH`, `SESSION_ID`, `ITERATION_FEEDBACK`). Do not re-include the subagent's system prompt; Claude Code loads that automatically from the subagent file.

**Parallel dispatch (Phase 1 Step 1)**: issue all four analyst Task calls in a **single message** so they run concurrently. This requires the runner to be at top-level (a skill or main conversation context); subagents themselves do not have the `Task` tool and cannot fan out.

**Fallback when Task is unavailable**: if this protocol is being followed in a context without `Task` (e.g. a subagent context), the runner may execute each agent role sequentially in its own context — read each subagent's prompt from `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md`, produce the output to its declared contract, write to the output path. This is a degraded mode: the four-frame triangulation is synthetic rather than from independent agents, and the meta-critic's audit becomes self-audit. The pipeline outputs will still materialize but the cross-agent quality gate is weakened.

## Inputs (resolved by the caller before dispatch)

| Variable | Required | Description |
|----------|----------|-------------|
| `INPUT_PATH` | yes | Project-relative path to the annotated conversation file. |
| `SOURCE_JSON_PATH` | yes | Project-relative path to the raw `conversation.json` (used by `cognitive-patterns-builder`). |
| `SESSION_ID` | yes | Identifier of the source session. |
| `CONTEXT_BACKGROUND` | no | Optional one-paragraph context about the subject. May be empty. |
| `ANALYSES_DIR` | yes | Project-relative path where Phase 1 analyst reports are written. Conventionally `personalized/saves/session/<SESSION_ID>/analyses/`. |
| `PROFILE_DIR` | yes | Project-relative path for the four products + `user_profile.md`. Conventionally `personalized/results/profile/`. |
| `MAX_ITERATIONS` | no | Defaults to 3. Hard cap on the Phase 1 analyst↔meta-critic loop. |
| `EXISTING_GRAPH` | no | `true` for cross-session merge into an existing `knowledge_graph/`. Default `false` (fresh build — runner cleans target). |
| `EXISTING_MODEL` | no | `true` for cross-session merge into an existing `behavioral_model/`. Default `false` (fresh build — runner cleans target). |

## Stale-output policy

Each output path has an explicit policy for what the runner does on a rerun. Cleanup is the **runner's** responsibility, not the builder's; builders must not delete files outside what their task instructed them to write.

| Output | Policy on rerun |
|--------|-----------------|
| `<ANALYSES_DIR>/<analyst>.md` (per-analyst) | Overwritten in place each iteration. On `iterate`, only the analysts marked `needs_revision` are re-dispatched and their files overwritten; other analysts' iter-N-1 files carry forward. |
| `<ANALYSES_DIR>/meta_critic.md` | Overwritten freely by the runner each iteration. (Manual `/run_meta_critic` invocations preserve history with timestamped renames; see that skill.) |
| `<ANALYSES_DIR>/synthesis.md` and `<PROFILE_DIR>/system_of_values.md` | Overwritten in place by `synthesis-builder`. |
| `<PROFILE_DIR>/cognitive_patterns.md` (single file) | Overwritten in place by the builder. |
| `<PROFILE_DIR>/knowledge_graph/` (directory of nodes) | If `EXISTING_GRAPH != true`: runner deletes the directory's contents before dispatching, so the builder writes into a clean directory. If `EXISTING_GRAPH == true`: contents preserved; builder merge-updates per its `EXISTING_GRAPH` workflow. |
| `<PROFILE_DIR>/behavioral_model/` (directory of BP-XXX files) | If `EXISTING_MODEL != true`: runner deletes the directory's contents before dispatching. If `EXISTING_MODEL == true`: contents preserved; builder merge-updates per its `EXISTING_MODEL` workflow. |
| `<PROFILE_DIR>/user_profile.md` (single file) | Overwritten in place by `profile-compressor`. |

## Phase 1 protocol — four-frame analysis with audit gate

### Step 0 — Setup

- Verify all input paths exist (`INPUT_PATH`, `ANALYSES_DIR`, `PROFILE_DIR`)
- Set `iteration = 1`
- Empty `iteration_feedback` (used to seed re-runs)

### Step 1 — Dispatch analysts (parallel)

Dispatch the four analysts (`affect-analyst`, `social-dynamics-analyst`, `values-analyst`, `narrative-analyst`) **in parallel** by issuing all four Task calls in a single response.

Per-analyst task prompt (template):

```
You are the <analyst-name>. Inputs:
- INPUT_PATH: <full path to annotated.txt>
- SESSION_ID: <session id>
- CONTEXT_BACKGROUND: <text or empty>
- ITERATION_FEEDBACK: <empty on iter 1; otherwise meta-critic's per-analyst revision instructions>

Follow your system prompt's protocol and return the report.
```

Wait for all four to complete. Save each output to `<ANALYSES_DIR>/<short-name>.md` where the short-name mapping is:

| Subagent | Short name |
|---|---|
| `affect-analyst` | `affect` |
| `social-dynamics-analyst` | `social` |
| `values-analyst` | `values` |
| `narrative-analyst` | `narrative` |

### Step 2 — Run meta-critic

Dispatch `meta-critic` via the Task tool. Task-prompt variables: `ANALYSES_DIR`, `AGENT_PROMPTS_DIR=${CLAUDE_PLUGIN_ROOT}/agents/`, `SOURCE_DATA_PATH=<INPUT_PATH>`, `SESSION_ID`, `ITERATION`. Do **not** pass `SYNTHESIS_PATH` (empty until Step 4).

Save the meta-critic's output to `<ANALYSES_DIR>/meta_critic.md`.

### Step 3 — Process meta-critic verdict

Read the `Loop Decision` section of the meta-critic report.

| Decision | Action |
|----------|--------|
| `accept` | Exit loop. Proceed to Step 4. |
| `iterate` AND `iteration < MAX_ITERATIONS` | Construct `iteration_feedback` per analyst from meta-critic's revision instructions. Increment `iteration`. Return to Step 1, dispatching **only the analysts marked `needs_revision`**. |
| `iterate` AND `iteration == MAX_ITERATIONS` | Exit loop with `escalated: true`. Proceed to Step 4 with caveat note. |
| `escalate` | Exit loop with `escalated: true`. Proceed to Step 4 with caveat note. |

### Step 4 — Dispatch synthesis-builder

Dispatch `synthesis-builder` via the Task tool. Task-prompt variables: `ANALYSES_DIR`, `OUTPUT_PATH=<ANALYSES_DIR>/synthesis.md`, `VALUES_OUTPUT_PATH=<PROFILE_DIR>/system_of_values.md`, `SESSION_ID`, `ESCALATED=<true|false>`.

The `synthesis-builder` reads the four analyst reports and `meta_critic.md`, integrates them, and writes **two** files:

1. `<ANALYSES_DIR>/synthesis.md` — the working artifact for Phase 3/4 builders (High-Consistency Findings, Real Divergences, Composite Portrait, Phase 3/4 seeds, Pipeline Caveats).
2. `<PROFILE_DIR>/system_of_values.md` — the formal Phase 1 product, layered per `methodology/phase1_value_extraction.md` (Core / Boundaries / Strong preferences / Trade-able / Explicit-vs-Revealed Gaps / Pipeline Caveats).

The runner verifies both files exist; it does **not** re-derive synthesis content itself. Producing the layered hierarchy view is structural rearrangement of cross-frame findings, which is `synthesis-builder`'s job — not the runner's. (Putting it inline in the runner would violate the "runner adds no new analysis" rule.)

## Phase 2 protocol — cognitive patterns (no audit)

Dispatch `cognitive-patterns-builder`. Task-prompt variables: `SOURCE_JSON_PATH`, `SESSION_ID`, `OUTPUT_PATH=<PROFILE_DIR>/cognitive_patterns.md`. The single-file output is overwritten in place. Verify the output file exists.

Phase 2 has no input dependency on Phase 1 and could be dispatched in parallel with Phase 3/4. Sequential is the default for simplicity.

## Phase 3 protocol — knowledge graph (no audit)

**Pre-dispatch cleanup (fresh-build mode only).** If `EXISTING_GRAPH != true`, the runner clears `<PROFILE_DIR>/knowledge_graph/` of all prior contents (delete subdirectories `concepts/`, `emotions/`, `people/`, `events/` and any `README.md`) before dispatch, so the builder writes into a clean directory. If `EXISTING_GRAPH == true`, leave contents in place — the builder will merge.

Dispatch `knowledge-graph-builder`. Task-prompt variables: `SYNTHESIS_PATH=<ANALYSES_DIR>/synthesis.md`, `ANALYSES_DIR`, `SESSION_ID`, `GRAPH_DIR=<PROFILE_DIR>/knowledge_graph/`, `EXISTING_GRAPH=<true|false>`. Verify nodes were created under `<GRAPH_DIR>/{concepts,emotions,people,events}/`.

## Phase 4 protocol — behavioral model (no audit)

**Pre-dispatch cleanup (fresh-build mode only).** If `EXISTING_MODEL != true`, the runner clears `<PROFILE_DIR>/behavioral_model/` of all prior `BP-*.md` and `README.md` files before dispatch. If `EXISTING_MODEL == true`, leave contents in place.

Dispatch `behavioral-model-builder`. Task-prompt variables: `SYNTHESIS_PATH=<ANALYSES_DIR>/synthesis.md`, `ANALYSES_DIR`, `SESSION_ID`, `GRAPH_DIR=<PROFILE_DIR>/knowledge_graph/` (optional, may be empty if Phase 3 hasn't run), `BEHAVIOR_DIR=<PROFILE_DIR>/behavioral_model/`, `EXISTING_MODEL=<true|false>`. Verify pattern files were created.

## Final compression — user_profile.md

Dispatch `profile-compressor`. Task-prompt variables: `PROFILE_DIR`, `OUTPUT_PATH=<PROFILE_DIR>/user_profile.md`, `BUILD_TIMESTAMP=<today's ISO-8601 date>`, `SUBJECT_ID=<short label or empty>`, `ESCALATION_NOTES` (extracted from `meta_critic.md` if Phase 1 escalated, else empty). Verify `user_profile.md` exists and is ≤200 lines.

## Final report

Return a brief execution log:

```yaml
session_id: <SESSION_ID>
phase_1:
  iterations: <count>
  escalated: <true | false>
  per_analyst_final_verdict:
    affect: <pass | pass_with_warnings | escalated>
    social: <...>
    values: <...>
    narrative: <...>
  synthesis_path: <ANALYSES_DIR>/synthesis.md
  product_path: <PROFILE_DIR>/system_of_values.md
phase_2:
  product_path: <PROFILE_DIR>/cognitive_patterns.md
phase_3:
  product_path: <PROFILE_DIR>/knowledge_graph/
  node_count: <integer>
phase_4:
  product_path: <PROFILE_DIR>/behavioral_model/
  pattern_count: <integer>
user_profile:
  path: <PROFILE_DIR>/user_profile.md
  line_count: <integer>
```

## Completion checklist

Before returning the final report, verify:

- [ ] The full coordination protocol executed (Phases 1–4 + compression)
- [ ] `synthesis-builder` was dispatched after meta-critic accepted (or escalated)
- [ ] Output language matches the dominant language of the source conversation
- [ ] If Phase 1 escalation occurred, the synthesis was marked with caveats and the caveat was propagated into the compressor's `ESCALATION_NOTES`
- [ ] All product files exist at their expected paths
- [ ] `user_profile.md` is ≤200 lines
- [ ] No content names identifiable individuals beyond what `CONTEXT_BACKGROUND` provides
