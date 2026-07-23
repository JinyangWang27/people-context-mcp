---
name: remember
description: Record durable knowledge about a person with the people-context tools. Invoke as /people-context:remember <description> to make an explicit person assertion via remember_person, or to stage extracted facts, affiliations, and interactions for later review.
disable-model-invocation: true
argument-hint: <what to remember about a person>
---

# /people-context:remember

A thin, user-invoked workflow that captures durable knowledge about people. It
routes the request down one of the existing paths below and keeps the user in
control of every write.

The user wants to remember: **$ARGUMENTS**

## Decide the path from what the user actually stated

Route on the content of the description above. Do not scan prior conversation for
additional things to persist, and do not apply automatic classification heuristics
beyond this one explicit description.

### 1. Explicit person assertion → `remember_person`

When the description is a direct assertion that a specific person exists or should be
recorded — a name, optionally aliases/nicknames, a one-line summary of who they are,
and optionally that they are the user (`is_self`) — it fits `remember_person`'s
contract. Call `remember_person` with those fields only. If it returns
`ambiguous_person`, present the returned candidates and let the user pick rather than
guessing; if it returns `self_already_exists`, report the existing self record
instead of creating another.

### 2. Extracted facts, affiliations, or interactions → resolve first, then stage

Facts (predicate/value), affiliations (org/role), and interactions do **not** fit
`remember_person`. They go through staging, using only the strict `person` /
`interaction` / `affiliation` / `fact` vocabulary with batch-local `ref`s. Before
constructing the batch:

- **Resolve every referenced person first** with `resolve_person`, and use the
  resolved canonical identity (canonical name, or a known handle) in that person's
  candidate. The stager matches an existing person only by an exact normalized name
  or handle, so a partial reference like `Alice` would otherwise be committed as a
  **new duplicate** of the stored `Alice Smith`. Resolving first and using the
  canonical name prevents that.
- If resolution is `ambiguous`, surface the candidates and let the user choose before
  staging; do not guess. If resolution is empty, the person is genuinely new — stage
  them as a new `person` candidate.

Then call `stage_candidates`. Never copy raw conversation, note, or transcript text
into a candidate field.

### 3. Anything that fits neither path → report the limitation, do not force it

Some requests fit neither `remember_person` nor the strict staging vocabulary. A
**relationship** ("Alice is my sister") is the common case: staging has no
relationship candidate type, so emitting one fails validation, and flattening it into
a generic fact hides the edge from the relationship graph. Do **not** force such a
request into staging. Tell the user plainly that this workflow records people
(`remember_person`) and facts/affiliations/interactions (staged for review) only, and
that relationships and other unsupported data are not captured here.

## Staging stays a proposal

`stage_candidates` only proposes. After staging, tell the user the batch is pending
and can be inspected with `review_import`. **Do not** call `commit_import` — the
commit is an explicit, later, user-approved step performed after the user reviews the
batch. Never commit automatically or in the same breath as staging.

## Boundaries

- Uses only `resolve_person`, `remember_person`, and `stage_candidates` (and
  `review_import` for inspection). It never calls `commit_import`.
- It never calls or suggests enabling the gated `get_sensitive_person_context` or
  `export_data` tools.
- It does not misuse `remember_person` to encode facts, relationships, or
  interactions that tool cannot represent, and it does not force unsupported data
  (such as relationships) into the staging schema.
