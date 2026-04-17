# Examples and Reference

Trigger examples, verification checklists, and good/bad patterns for commit messages and pull requests.

## Trigger examples

### Commit message only

- "write a commit message for this diff"
- "what should the commit message be for these changes?"

### Commit flows

- "commit these changes"
- "make the commit after you show me the message"
- "commit and push this branch once I approve the message"

### Pull request flows

- "draft a PR for this branch"
- "write the PR title and body"
- "create the PR after I approve the text"

### Combined finish-branch flows

- "finish this branch"
- "wrap this up"
- "take this through commit, push, and PR"

### Response pattern

1. Inspect the branch state.
2. Draft the message or PR text.
3. Show the draft and the exact next action.
4. Wait for approval.
5. Execute only the approved scope.

## Commit message verification checklist

Before presenting a drafted commit message, check:

1. Is it imperative mood? ("add", "fix", "refactor" — not "added", "fixes", "refactoring")
2. Would a reviewer understand the scope from the subject alone?
3. If there's a body, does it add information the subject doesn't?
4. Is all text lowercase except proper names, acronyms, and identifiers?

## Commit message examples

### Good

```
fix race condition in WebSocket reconnect logic
```

```
add Stripe webhook handler for subscription events
```

```
refactor auth middleware to support JWT and API key
```

### Good — single subject covering related changes

```
fix login redirect and suppress stale session warning
```

### Good — semicolon when changes can't be expressed as one thought

```
fix login redirect; update session expiry default
```

### Good — with body

```
migrate user table from MongoDB to PostgreSQL

- adds new PostgreSQL schema with UUID primary keys
- backfills existing records via migration script
- removes mongoose dependency

BREAKING CHANGE: user IDs are now UUIDs, not ObjectIds
```

### Bad — past tense

```
added new endpoint for user search
```

### Bad — too vague

```
fix bug
```

### Bad — describes HOW, not WHAT

```
use Promise.all instead of sequential awaits in batch processor
```

Better:

```
parallelize batch processor requests
```

### Bad — filler and verbosity

```
make some small improvements to the login page styling
```

Better:

```
clean up login page styles
```

### Bad — multiple unrelated changes crammed together

```
fix login bug and add dashboard charts and update README
```

This should be split into separate commits.

## PR examples

### Good — simple

Title:

```
add README with setup and MCP configuration docs
```

Body:

```
## Summary
- adds README with package overview and environment setup
- documents MCP client configuration for Cursor, Claude Desktop, and Claude Code
```

### Good — with test plan, when warranted

Title:

```
migrate auth from session cookies to JWT
```

Body:

```
## Summary
- replaces express-session with jsonwebtoken
- adds refresh token rotation with 7-day expiry
- updates all protected routes to use new middleware

## Test plan
- [ ] verify login flow issues new JWT + refresh token
- [ ] verify expired access token triggers silent refresh
- [ ] verify revoked refresh token forces re-login
```

## Body-inclusion rules

Add a commit body (blank line after subject) ONLY when:

- (a) the change is non-obvious and the "why" matters
- (b) there are breaking changes
- (c) multiple distinct changes need itemization

Body format:

- lines ≤ 72 characters
- "- " bullets for multiple items, prose for single explanations
- lowercase except proper names, acronyms, identifiers
- explain WHY when the reason isn't obvious from the subject
- reference ticket/issue IDs when available (e.g. "closes #1234")
- for breaking changes, start body with "BREAKING CHANGE: <description>"

## Test plan inclusion rules

Add a `## Test plan` section to PR body ONLY when:

- (a) the change requires manual verification steps
- (b) there are non-obvious testing considerations
- (c) explicitly requested

## Acronym and identifier casing

Lowercase is the default, except for proper names, acronyms, and identifiers. Examples of things that stay cased:

- React, PostgreSQL, MongoDB, OpenAI, AWS, Stripe
- HTTP, JWT, SSE, UUID, SDK, CLI, API
- file names and code identifiers (e.g. `useMemo`, `settings.json`)
