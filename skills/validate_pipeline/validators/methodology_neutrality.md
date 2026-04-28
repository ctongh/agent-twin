---
validator: methodology_neutrality
status: implemented
severity: hard
scope:
  - methodology/**
  - agents/**
  - skills/**/SKILL.md
  - skills/**/TEMPLATE.md
---

# methodology_neutrality

## What it checks

That nothing in the **shareable framework** (`methodology/`, `agents/`, public skill files) reveals identifying information about any specific subject.

The benchmark for this validator is the project owner's principle:

> Reading all the methodology files should let an agent know exactly *how* to analyze a subject — yet still know **nothing** about any specific subject.

## Detection logic

Run two passes over each in-scope file:

### Pass 1 — Direct identifier scan (mechanical)

Look for anchored personal data. Flag any of:

- **Proper nouns of people**: any human name (heuristic: proper-cased token followed by relational language like 主管, 同事, 女友, 老闆, partner, boss, manager, colleague). The token itself or its description, not generic placeholders.
- **Organization names**: company names, department codes, internal product names. Whitelist generic placeholders like `[Company X]`, `[your organization]`.
- **Specific project names**: internal project identifiers that could not appear in any other subject's life.
- **Specific quotes with turn IDs**: a `>` quoted block followed by `[NNN]` that did not come from the validator's own samples (i.e., quotes from real subject data have leaked into the framework).
- **Specific personal details**: ages, dates that map to one subject's life (e.g., birthdays), exact salary numbers, specific addresses or universities.
- **Hardcoded counts that imply one specific dataset**: e.g., "120 turns", "5 sessions", "this conversation has X". These imply one specific subject's data.

### Pass 2 — Inferential check (semantic)

Read each file and ask, *if this is the only context I have, can I describe a specific person?* This includes implications, not just direct mentions:

- A list of vocabulary "the subject uses" reveals the subject's professional background and personality
- A list of "metaphors the subject coined" maps onto a real worldview
- A list of "behavior patterns" with concrete recovery options like *partner support* or *trusted supervisor* implies the subject has a partner, has a supervisor, etc.
- A description of "this is why we removed reflections/" implies one specific incident
- Status notes like "Phase 2 已完成" imply one subject's progress

For each suspected inferential leak: cite the file, the lines, and the inference it enables.

## Failure criteria

A finding is a **hard** failure (validator returns `fail`) when:

- A specific human name appears
- A specific organization name appears
- A specific project name (not generic) appears
- A direct quote with a turn ID appears that cannot be traced to the validator's own samples
- A personal detail (age, exact figure, address-equivalent) appears
- A hardcoded count implies a single specific dataset

A finding is a **soft** warning (validator returns `pass_with_warnings`) when:

- Vocabulary lists are too suggestive of one professional background
- Examples implicitly assume one type of relationship structure
- Status / progress notes leak a specific subject's progress
- Sample data (in `samples/`) appears to be derived from a real subject rather than synthesized

## Suggested fixes

| Pattern | Fix |
|---------|-----|
| Proper noun of person | Replace with bracketed placeholder (e.g., `[a close personal contact]`, `[primary supervisor]`) |
| Specific organization | Replace with `[Company X]` or remove entirely if not load-bearing |
| Specific project name | Replace with `[Project A]` or describe by *type* rather than name |
| Real quote + turn ID | Move to `personalized/` or remove from the framework file |
| Specific count | Replace with variable (e.g., `N turns`) or remove |
| Suggestive vocabulary list | Either generalize the list to *categories* of vocabulary, or move the example list to `personalized/` |
| Status note | Move project-status notes to `personalized/` or to README outside `template/` |

## How the executing agent runs this

When the executing agent runs this validator:

1. Enumerate files in scope (resolve the glob patterns above)
2. For each file: apply Pass 1, then Pass 2
3. For each finding, record: file path, line range (or 1-line span), the matched content (or inference described), severity (hard / soft)
4. Return a structured report:

```yaml
validator: methodology_neutrality
result: pass | pass_with_warnings | fail
findings:
  - file: <path>
    lines: <N or N-M>
    severity: hard | soft
    matched: <verbatim or inferred>
    suggestion: <what to change>
  - ...
```

## Examples

**Direct hit (hard)**:
```
File: methodology/phase4_behavioral_model.md, line 122
Matched: "對話者可以把最核心的幾個 BP 分享給親近的人（女友、信任的主管）"
Severity: hard
Suggestion: replace "女友、信任的主管" with "trusted personal contacts"
```

**Inferential (soft)**:
```
File: methodology/phase2_cognitive_patterns.md, lines 11-16
Matched: a list of vocabulary domains naming domain-specific jargon plus introspective
language pointing toward one professional and psychological background
Inference: implies a software engineer with strategic-business exposure and a particular
psychological vocabulary
Severity: soft
Suggestion: generalize to "domain-specific vocabulary categories" without listing instances
```
