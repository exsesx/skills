# Text Conventions and Examples

Read this reference when drafting commit or pull request text.

## Detect conventions

Explicit user and repository instructions always outrank inferred history.
Otherwise sample up to 20 recent non-merge commits and, for PRs, recent merged
PRs. Ignore obvious bot noise when it does not represent the human convention.

Treat a pattern present in roughly 60% of the useful sample as strong evidence,
but evaluate subject prefix, casing, length, punctuation, scope style, and body
frequency separately. Small repositories may not have enough history for a
single dominant style.

## Commit fallback

When no stronger convention exists:

- use imperative mood and describe what changed
- keep the subject lowercase except proper names, acronyms, identifiers, file
  names, and version tokens
- keep subject and body lines at 72 characters or fewer
- avoid sentence-ending periods
- use one thought when possible
- join two tightly related thoughts with `;` only when one phrase is unclear
- add a body only for non-obvious rationale, breaking changes, or multiple
  distinct points
- use bullets for distinct points rather than paragraph prose
- reference issue or ticket identifiers only when present in context

Good:

```text
fix login redirect; update session expiry default
```

```text
migrate session storage to PostgreSQL

- adds UUID-backed session records
- backfills active sessions during deployment
- removes the MongoDB session adapter
```

Bad:

```text
added some fixes and updates
```

```text
fix login bug and add dashboard charts and update README
```

Split the second example into independent commits.

## Casing exceptions

Preserve forms such as React, Node.js, PostgreSQL, OpenAI, HTTP, JWT, UUID,
SDK, CLI, `useMemo`, `settings.json`, and version tokens such as Python 3.12.

## Pull request fallback

When there is no template or clear merged-PR convention:

- match the title to the commit-subject convention
- start the body with `## Summary`
- use concise bullets grounded in the full branch diff
- do not add `## Test plan` unless the user requests it or repository policy
  requires it

Example:

```markdown
## Summary
- adds README setup and package configuration guidance
- documents Codex and Claude Code skill invocation
```

Do not invent tests, issue links, reviewers, deployment notes, breaking
changes, or user impact that the branch does not support.
