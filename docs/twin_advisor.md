# twin-advisor — using your persona without polluting the working session

## What it is

`twin-advisor` is a sub-context twin you can consult from inside any working session. It loads your compiled `behavior_brief.md` in a Task-dispatched subagent, reads the recent transcript of the calling session for context, and replies in your first-person voice. The brief never enters the calling session's prompt. When the dispatch ends, the persona is gone again — your working session continues uncontaminated.

You invoke it via `/consult_twin <free-form question>`. One argument, no flags. The skill infers whether you want a decision recommendation (advisor mode) or a question list (curious mode) from the shape of the prompt.

## How it differs from `/load_persona`

| | `/load_persona` | `/consult_twin` |
|---|---|---|
| Scope | the whole session, until it ends | one Task dispatch |
| Side effect | every reply afterward is shaped by the brief | nothing in the calling session changes |
| When to use | you want persona-aware help across many turns | you only need the twin's take at one point |
| Cost of being wrong | the working session starts answering "what's the syntax for X" in persona voice | the question gets a non-persona answer; you rephrase |

The two are orthogonal. `/consult_twin` does not call `/load_persona` internally and never will — that would defeat the entire isolation guarantee.

## The two patterns

### Pattern 1: Decision advisor

You're inside a working session and you hit a branch where the assistant would normally ask you. Instead, ask the twin:

```
You:    I'm looking at this module — should I refactor in place or rewrite from scratch?
        I keep flipping. Use /consult_twin to ask my twin what I'd actually do.

Claude: [dispatches /consult_twin with the question]

Twin (returned to your session):
        Refactor. Rewriting from scratch is the version of myself I keep
        catching that wants the dopamine of a clean slate, but in two weeks
        I'd be re-learning all the edge cases the old code already handles.
        The boring path is right here — split out the worst module, put a
        seam in, port one consumer at a time. If after the second consumer
        I'm still fighting the existing shape, then I revisit rewrite as a
        real option, not a flinch.

        What I'd actually do: pick the gnarliest function tomorrow morning,
        extract it behind an interface, leave the rest alone for the week.

        (Consulted via twin-advisor — response did not enter this session's prompt context.)
```

The orchestrator surfaces the twin's recommendation; you decide what to do with it. The session's prompt context did not gain a single token of brief content.

### Pattern 2: Curious twin (好奇寶寶)

You want to research a topic in a domain you don't know well yet. The hard part of starting research isn't finding answers — it's knowing which questions to ask. The twin knows you, so it can ask better questions in your voice than you can.

```
You:    /consult_twin let's research electrochemical aluminum etching for
        custom anodized parts

Twin:   1. What's the rate equation? I want to know what controls etch
           speed before I care about cosmetics — current density, electrolyte
           composition, temperature, agitation. Mechanism first.

        2. Where do real anodizers screw this up? I'd rather read three
           failure post-mortems than ten happy-path tutorials.

        3. What's the cheapest setup that produces a result I can actually
           measure? Not the hobby kit and not the industrial line — the
           middle path where I'd notice if I changed one variable.

        4. How does this interact with the alloy? I assume 6061 vs 7075
           behaves differently and the difference is the kind of thing
           people only mention in passing.

        5. Who are the two or three people whose writing on this is
           load-bearing? I'd rather find them now than re-derive their
           lessons in six months.

        (Consulted via twin-advisor — response did not enter this session's prompt context.)
```

The twin doesn't try to answer. It produces the question list you would have asked if you already knew where to look. You feed those questions to your actual research workflow.

## Best practice — calling it from a working session

Don't switch to a separate twin-only session for one consultation. Just address the orchestrator from inside whatever you're already doing:

```
You (in any working session):
> I'm stuck on whether to refactor or rewrite this module.
> Use /consult_twin to get my twin's take.
```

The orchestrator dispatches `/consult_twin` with your question. The twin's response comes back. The orchestrator surfaces it. The brief never enters your working session's prompt.

This is the workflow the feature was designed for. Don't `/load_persona` your working sessions defensively — load it only when you actually want pervasive persona shaping. For one-shot consultations, `/consult_twin` is strictly better.

## Limitations

- **The twin only knows the brief.** Phase 2/3/4 detail (`cognitive_patterns.md`, the knowledge graph, behavioral-model files) is not loaded by `twin-advisor`. For deeper introspection on a specific layer, use `/show_persona` separately.
- **Recent context is bounded.** The twin reads roughly the last 30–50 turns or up to ~20K characters of the calling session's JSONL. Long sessions may have lost early context by the time you consult.
- **Mode inference is fuzzy.** The skill keys on prefixes like `research`, `explore`, `let's look at`, `研究`, `探索`, `了解`. If it picks the wrong mode, the answer is harmless — just rephrase. The default is advisor; that's the more useful failure mode.
- **The twin is not you.** It's a high-fidelity simulation built from behavior data. Treat its advice the way you'd treat thinking out loud at 11 PM — useful as a probe, not as authoritative self-knowledge. The brief itself is updated only when you re-run `/run_pipeline`, so the twin lags behind your latest growth.

## When NOT to use it

Don't reach for `/consult_twin` when persona shaping adds nothing:

- Pure factual questions: "what's Python's `sys.maxsize`?" — just ask normally.
- Mechanical tasks: writing tests, formatting JSON, regex translation — persona shaping is overhead.
- Debugging stack traces — the twin doesn't know your code; you do.
- Quick syntax lookups, library docs, "what does this error mean".

The whole point of the sub-context isolation is that you can keep working sessions clean. Don't pollute the consultation surface either — call the twin when you genuinely want the twin, not as a habit.
