---
name: remember
description: Record durable knowledge about a person with the people-context tools. Invoke as /people-context:remember <description> to make an explicit person assertion via remember_person, or to stage extracted facts, affiliations, and interactions for later review.
disable-model-invocation: true
argument-hint: <what to remember about a person>
---

# /people-context:remember

A thin, user-invoked workflow that captures durable knowledge about people. It
routes the request down exactly one of two existing paths and keeps the user in
control of every write.

The user wants to remember: **$ARGUMENTS**

## Decide the path from what the user actually stated

Route on the content of the description above. Do not scan prior conversation for
additional things to persist, and do not apply automatic classification heuristics
beyond this one explicit description.

- **Explicit person assertion → `remember_person`.** When the description is a
  direct assertion that a specific person exists or should be recorded — a name,
  optionally aliases/nicknames, a one-line summary of who they are, and optionally
  that they are the user (`is_self`) — it fits `remember_person`'s contract. Call
  `remember_person` with those fields only. If it returns `ambiguous_person`, present
  the returned candidates and let the user pick rather than guessing; if it returns
  `self_already_exists`, report the existing self record instead of creating another.

- **Everything else → `stage_candidates` (propose only).** Facts (predicate/value),
  affiliations (org/role), interactions, or anything extracted or inferred from prior
  context does **not** fit `remember_person`. Extract concise, structured candidates
  using only the strict `person` / `interaction` / `affiliation` / `fact` vocabulary
  with batch-local `ref`s, and call `stage_candidates`. Never copy raw conversation,
  note, or transcript text into a candidate field.

## Staging stays a proposal

`stage_candidates` only proposes. After staging, tell the user the batch is pending
and can be inspected with `review_import`. **Do not** call `commit_import` — the
commit is an explicit, later, user-approved step performed after the user reviews the
batch. Never commit automatically or in the same breath as staging.

## Boundaries

- Uses only `remember_person` and `stage_candidates` (and `review_import` for
  inspection). It never calls `commit_import`.
- It never calls or suggests enabling the gated `get_sensitive_person_context` or
  `export_data` tools.
- It does not misuse `remember_person` to encode facts, relationships, or
  interactions that tool cannot represent — those always go through staging.
