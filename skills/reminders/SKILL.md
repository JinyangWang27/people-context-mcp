---
name: reminders
description: List pull-based reminders with the people-context tools. Invoke as /people-context:reminders [person] to see all active reminders, or resolve an optional person first and list only theirs.
disable-model-invocation: true
argument-hint: "[person] (optional)"
---

# /people-context:reminders

A thin, user-invoked workflow that lists reminders. When the user names a person it
resolves that identity first, then filters; otherwise it lists everything active.

Optional person filter: **$ARGUMENTS**

## Steps

1. **No person given** (the argument above is empty): call `list_reminders` with no
   `person_id`. It returns active reminders, due-dated first and communication notes
   last.

2. **A person is named:** resolve the identity before filtering.

   - Call `resolve_person` with the given text.
   - **Exactly one confident match** (single candidate, not flagged `ambiguous`):
     call `list_reminders` with that candidate's `person_id`.
   - **`ambiguous` or multiple candidates:** stop and surface the candidate list so
     the user can choose. Do **not** silently drop the person filter and list
     everyone's reminders, and do not guess a candidate.
   - **Empty candidate list:** report that no one matching is stored rather than
     falling back to an unfiltered list; let the user restate who they mean.

## Boundaries

- Read-only workflow: it calls only `resolve_person` and `list_reminders`. It
  performs no writes.
- It never calls or suggests enabling the gated `get_sensitive_person_context` or
  `export_data` tools.
- Ambiguity is always surfaced; the person filter is never silently discarded.
