# Output Contract Schema

**Purpose**: Define a lightweight contract format that each analysis agent declares about its own output. Used by `meta-critic` (Worker-Evaluator pattern) to verify the agent's work against its declared deliverables.

**Design philosophy**: Contracts specify *what* and *how* in a way that is machine-checkable, but they accept that persona-extraction work is open-ended — some constraints are "hard" (failing them blocks acceptance) and others are "soft" (failing them generates warnings). Avoid over-engineering: contracts are guardrails, not straitjackets.

---

## Where contracts live

Each agent prompt file (`agents/<name>.md`) embeds its own contract as a single fenced YAML block, identifiable by the marker:

````markdown
```yaml output-contract
contract:
  agent: <agent-name>
  ...
```
````

`meta-critic` extracts the block, loads it as YAML, and validates the agent's output against it.

---

## Schema

```yaml
contract:
  agent: <kebab-case agent name>
  version: <semver, default 1.0>

  # Hard structural requirements about the produced report
  deliverables:
    - id: <stable identifier>
      name: <human-readable section title>
      required: true | false
      type: list | prose | table | yaml | mixed
      hard: true | false        # if false, missing this section produces a warning, not a failure
      constraints:
        # for lists/tables
        count: <"min-max" or exact integer>
        fields_required: [<field>, ...]
        # for prose
        word_count: <"min-max">
        must_address: [<topic>, ...]
        # for yaml
        schema_keys: [<key>, ...]

  # Methodology rules the agent must follow during analysis
  methodology_constraints:
    - id: <stable identifier>
      description: <what the agent should/should not do>
      hard: true | false
      check_method: <one sentence describing how meta-critic verifies>

  # Patterns the agent should explicitly avoid
  anti_patterns:
    - <description of forbidden pattern>

  # Output language policy
  output_language: derived_from_input | en | <explicit>
  # "derived_from_input" = match the dominant language of the source conversation
```

---

## Validation behavior

`meta-critic` applies the contract in this order:

1. **Structural pass** — verify each deliverable's presence and constraint compliance
2. **Methodology pass** — apply each constraint's `check_method`
3. **Anti-pattern scan** — sample-check for forbidden patterns
4. **Verdict synthesis**:

| Outcome | Meaning |
|---------|---------|
| `pass` | All hard checks satisfied. Soft warnings may exist but are acceptable. |
| `pass_with_warnings` | All hard checks satisfied; soft checks have ≥1 failure |
| `needs_revision` | ≥1 hard check failed; specific feedback for the agent to revise |
| `unrecoverable` | Output is structurally so broken that revision cannot fix it; escalate to orchestrator |

The `orchestrator` consumes this verdict to decide whether to accept, re-dispatch, or fall back.

---

## A working example

For an analysis agent (e.g., `affect-analyst`), a typical contract block:

```yaml output-contract
contract:
  agent: affect-analyst
  version: 1.0

  deliverables:
    - id: core_findings
      name: Core Findings
      required: true
      type: list
      hard: true
      constraints:
        count: "5-7"
        fields_required: [title, description, quotes, confidence, rationale]

    - id: synthesis_map
      name: Synthesis Map
      required: true
      type: prose
      hard: true
      constraints:
        word_count: "150-300"

    - id: blind_spots
      name: Blind Spots
      required: true
      type: list
      hard: false
      constraints:
        count: "3-5"

  methodology_constraints:
    - id: prioritize_high_intensity_evidence
      description: Findings labeled high confidence must rest on high-intensity moments (emotional outbursts, body symptoms, direct corrections of the AI), not on agreement statements
      hard: true
      check_method: For each high-confidence finding, sample its quotes and verify intensity markers exist

    - id: respect_cluster_boundaries
      description: Cross-cluster claims must be grounded in two or more clusters; single-cluster evidence cannot support cross-cluster generalization
      hard: false
      check_method: For findings claiming session-wide patterns, verify quote diversity across clusters

  anti_patterns:
    - Pathologizing common situational stress as a personality structure
    - Treating AI-anchored statements as the user's authentic position

  output_language: derived_from_input
```

---

## Important caveat (from project owner)

> Persona extraction is open-ended. Output contracts may not always be fully satisfiable; some legitimate analyses will produce structures the contract didn't anticipate. The contract is a *target*, not a proof obligation. `meta-critic` should distinguish between "agent failed to follow instructions" (a real problem) and "agent produced something the contract didn't predict but is still valuable" (acceptable; report as a warning, not a failure).

This is why most non-structural constraints should default to `hard: false`. Use `hard: true` only for truly non-negotiable guardrails (e.g., privacy violations, citing imaginary turns, output language mismatch).
