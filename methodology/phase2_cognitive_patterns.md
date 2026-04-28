# Phase 2 — Cognitive Patterns

## Purpose

Phase 1 (values) answers *what* the subject treats as important. Phase 2 answers **how they think** — the language they use, the metaphor systems they construct, the way they build arguments, the rhythm of their emotional/rational oscillation.

Phase 2 is the most language-level of the four phases. It produces naming conventions and structural cues that downstream phases lean on:

| Phase | Output | Question it answers |
|-------|--------|---------------------|
| 1 | System of Values | *What* matters and how much? |
| **2** | **Cognitive Patterns** | ***How* does the subject think?** |
| 3 | Knowledge Graph | How are the subject's concepts connected? |
| 4 | Behavioral Model | What will the subject *do* in situation X? |

Phase 2 is **independent of Phase 1**. It does not consume Phase 1's seeds; it operates directly on the source conversation. It can run in any order relative to the others and is **not audited by `meta-critic`** — its findings are language-level statistics interpreted qualitatively, and the subject can sanity-check the result directly.

## Inputs

| Item | Description |
|------|-------------|
| Source conversation | Raw `conversation.json` from `personalized/saves/session/<session_id>/`. The annotated form is not required (cluster headers are not load-bearing for language-level analysis). |
| Optional baseline statistics | If a quantitative pre-pass is run, its JSON output is fed into the builder. |

## Process: builder agent + optional quantitative pre-pass

```
            ┌─────────────────────────────┐
            │ source conversation (JSON)  │
            └──────────────┬──────────────┘
                           │
      ┌────────────────────┴───────────────────┐
      │                                        │
      ▼ (optional, recommended)                ▼
quantitative pre-pass                  cognitive-patterns-builder
(Python: counters,                     (LLM agent reading source +
 question types,                        baseline stats; produces the
 connectives, density)                  qualitative profile)
      │                                        │
      └────────────────────┬───────────────────┘
                           ▼
                 cognitive_patterns.md
                 (Phase 2 product)
```

The quantitative pre-pass is recommended but not required. It catches what the eye misses (frequency distributions, question-type ratios, connective usage); the builder catches what regex misses (metaphor systems, argument shape, metacognitive patterns).

## Analysis dimensions

The builder must address these six dimensions. Each is its own section in the output.

### 1. Lexical fields

A subject's writing typically mixes vocabularies from multiple domains; the code-switching pattern is itself data. Common fields include (illustrative, not exhaustive): engineering / technical, business / strategy, psychology / philosophy, everyday / colloquial, AI-mediated language.

Questions to answer:
- Which fields are most frequent? (signals where the subject's cognitive home is)
- What contexts trigger field-switching? (e.g., does the subject reach for engineering metaphors when emotions rise?)
- Which expressions are subject-coined vs. AI-borrowed?

### 2. Metaphor system

Apply Lakoffian conceptual-metaphor analysis. Identify the source domains the subject draws from when describing experience: materials, war, food, machines, biology, games, journeys, etc.

- What is the dominant metaphor type?
- What worldview do these metaphors collectively imply?
- Which metaphors recur across multiple unrelated topics? Those are *core metaphors* and likely encode identity claims.

### 3. Question style

- Distribution of "why" / "how" / "whether" / "what" question types
- Open-ended vs. closed-ended
- Whether questions come paired with the subject's own hypothesis ("do you think X?")

### 4. Argument structure

How does the subject get from observation to conclusion?
- Inductive (collecting cases)
- Deductive (deriving from principles)
- Analogical (using A to explain B)
- Frame-switching (jumping between framings within a single turn — count rate)
- Contradiction handling (integrate, accept coexistence, switch sides)

### 5. Emotional–rational oscillation

Many reflective subjects show layered self-understanding: rational acknowledgment alongside an admitted emotional reaction. Distinguish *layered* (acknowledging both) from *integrated* (treating both as one).

- Ratio of emotional vs. rational language
- Sequence: emotion → rationalization, or rationalization → emotion?
- Whether emotional expression is consistently rewrapped in analytical language afterward (a signature of intellectualization defenses)

### 6. Metacognition

Some subjects exhibit strong meta-awareness: they predict the AI's response, predict their own reactions, name their own patterns.

- Frequency of metacognitive statements
- Accuracy (do their self-predictions hold?)
- Function (is metacognition a tool for change, or a sophisticated way of avoiding change?)

## Outputs

The Phase 2 product is a single document at:

```
personalized/results/profile/cognitive_patterns.md
```

Structure:

```markdown
# Cognitive Patterns

## Lexical-Field Distribution
[stats + interpretation]

## Core Metaphor System
[primary metaphor types + worldview implications + list of recurring core metaphors]

## Question Style
[stats + characterization]

## Argument Structure
[modes of reasoning + frame-switching rate + contradiction handling]

## Emotional–Rational Oscillation
[layered vs. integrated; sequencing patterns]

## Metacognition
[frequency + accuracy + function]

## Cognitive Strengths and Blind Spots
[integrated assessment]
```

## Quality criteria

A Cognitive Patterns document is acceptable when:

1. **Each dimension has both a quantitative anchor and a qualitative interpretation.** "X happens often" is not enough; how often, vs. what baseline, with what interpretation.
2. **Core metaphors are evidenced across at least two unrelated topics.** A metaphor used only when discussing one topic is topic-specific, not core.
3. **Subject-coined vs. AI-borrowed language is distinguished.** Phrases the subject only adopted after the AI introduced them are not part of their native cognitive style.
4. **The "Strengths and Blind Spots" section connects findings across dimensions.** A list of dimensions without integration is incomplete.

## Pitfalls

### Confusing register with cognition
A subject who writes formally in one context and casually in another may have the same cognitive style across both. Register is a sociolinguistic variable; cognitive style is the underlying machinery.

### Treating AI-borrowed phrases as native
After 50+ turns, the subject often picks up the AI's vocabulary. Filter these out by checking whether the phrase appears in the AI's prior turns before the subject first used it.

### Overreading rare patterns
Frame-switching twice in 120 turns is not a pattern. The builder must report base rates, not just counts.

### Mistaking metacognition for change
A subject who names their own patterns is exhibiting awareness, not necessarily transformation. Phase 2 must not treat naming as evidence of resolution.

## Pipeline integration

| Concern | Where handled |
|---------|---------------|
| Builder dispatch | `orchestrator` runs `cognitive-patterns-builder` after Phase 1 (or in parallel; Phase 2 has no input dependency on Phase 1) |
| Optional quantitative pre-pass | Provided by the builder skill or by an external Python script; output is fed into the builder as supplementary input |
| Output-language consistency | The builder declares `output_language: derived_from_input` |
| Privacy / neutrality of methodology | `validate_pipeline` skill checks that this document contains no subject-specific content |

## Where Phase 2 fits in product flow

Phase 2 produces `cognitive_patterns.md`. The `profile-compressor` reads this file (alongside the Phase 1/3/4 products) when it builds `user_profile.md`. Phase 2's findings most directly inform the **"How they tend to think"** and **"How they like to work with an AI"** sections of the compressed profile.

## See also

- `methodology/template/pipeline.md` — overall pipeline architecture
- `methodology/template/phase1_value_extraction.md` — Phase 1 (sibling phase, foundation)
- `methodology/template/phase3_knowledge_graph.md` — uses Phase 2's lexical fields and metaphors as naming sources
- `methodology/template/phase4_behavioral_model.md` — uses Phase 2's argument structure and oscillation patterns
- `agents/cognitive-patterns-builder.md` — the builder prompt
- `agents/orchestrator.md` — how Phase 2 is dispatched in the overall pipeline
