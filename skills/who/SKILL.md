---
name: who
description: Resolve who a person is with the people-context tools. Invoke as /people-context:who <query> to identify a name, nickname, or partial reference and, only on a single confident match, read that person's stored context.
disable-model-invocation: true
argument-hint: <name | nickname | partial reference>
---

# /people-context:who

A thin, user-invoked workflow that answers "who is this person?" by composing the
existing read-only people-context tools. It resolves identity first and reads
context only when the resolution is unambiguous.

The user asked about: **$ARGUMENTS**

## Steps

1. **Resolve first.** Call `resolve_person` with the query above. Do not ask the
   user who they mean before resolving, and do not call any other people-context
   tool first.

2. **Branch on the resolution outcome — do not guess.**

   - **Exactly one confident match** (a single candidate and the result is *not*
     flagged `ambiguous`): call `get_person_context` once with that candidate's
     `person_id` to report what is known — narrow identity, active relationships and
     affiliations, and the recent facts/interactions slice. This is the only case in
     which a second read happens.
   - **`ambiguous`, or more than one candidate:** stop and present the returned
     candidate list with each candidate's score and match reason. Let the user
     choose or add distinguishing detail. Never silently pick a candidate, and never
     call `get_person_context` for a guessed identity.
   - **Empty candidate list** (no confident match): report that no one matching is
     stored. Do not read context and do not invent an identity. You may note that
     `/people-context:remember` can record them.

## Boundaries

- Read-only workflow: it calls only `resolve_person` and, on a single unambiguous
  match, `get_person_context`. It performs no writes.
- It never calls or suggests enabling the gated `get_sensitive_person_context` or
  `export_data` tools; the ordinary context bundle is the intended, complete view.
- Preserve the `ambiguous` candidate-list contract exactly — surfacing candidates is
  the correct outcome, not a failure to work around.
