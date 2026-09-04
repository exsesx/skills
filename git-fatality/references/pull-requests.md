# Pull Request Workflow

Read this reference only when drafting, creating, or updating a pull request.

## Interpret intent

- "Draft" or "write PR text" means title and body only.
- "Create" or "open a PR" means a ready PR unless the user says remote draft.
- "Create a draft PR" means use the hosting platform's draft state.
- Creating a PR includes publishing its inspected, already committed scope
  when needed. Inspect the destination and outgoing commits first; pause if
  their scope or destination is unclear. It does not authorize a new commit,
  rewriting history, or updating an existing PR.
- Honor explicit restrictions. With "do not push", use the published head only
  when the user requested that scope; otherwise explain the unpublished scope
  and finish the text before asking how to proceed.

## Resolve style and content

Use the precedence in `SKILL.md`. Search template names case-insensitively in
the repository root, `docs/`, and hosting configuration directories such as
`.github/`. Check `PULL_REQUEST_TEMPLATE.md` and `.txt`, plus `.md` and `.txt`
work-type templates inside `PULL_REQUEST_TEMPLATE/`. Read templates from the
default branch when the hosting platform does. Use the selected template
verbatim as the skeleton, preserve its sections and order, and fill every
required field.

In `personal` mode, do not query merged PR history for style. Without a required
template, use the personal title style and `## Summary` with concise,
diff-grounded bullets. Apply the personal commit casing and punctuation rules
to generated PR titles and body bullets.

In `repo` mode, still inspect required templates first. Query a bounded sample
of recent merged PRs only when written instructions and templates leave
structure or tone unresolved. Fall back to personal style when the sample is
inconsistent, insufficient, or unavailable.

Do not invent tests, issues, reviewers, deployment notes, breaking changes, or
user impact. Add a test-plan section only when requested or required.

## Inspect branch and base

Choose the base in this order:

1. the user's explicit base
2. the head branch's configured hosting merge base
3. the repository's default branch from the hosting platform
4. the remote `HEAD` symbolic ref

Before creation, check for an open PR with the same head. Do not create a
duplicate or overwrite an existing PR under creation-only authorization.
Update it only when explicitly requested or after approval of a concrete update.

Resolve the intended head repository and branch, then compare local `HEAD`
with the actual published head commit. Publish the authorized committed scope
when needed, following the push checks in `SKILL.md`. Confirm the remote head
matches the inspected commit before creating the PR.

For creation or an update, build the title and body from the merge-base diff
`base...publishedHead` and commit range `base..publishedHead`, using the verified
published head. This excludes unrelated changes made on the base after the
branches diverged. For a text-only draft, local committed scope is allowed;
use `base...HEAD` and identify it as unpublished when it differs from the remote.
Exclude uncommitted files in both cases.

## Assignee and labels

Self-assign with `@me` by default. A named assignee replaces that default; an
explicit opt-out leaves the PR unassigned.

Inspect the complete available label set. Apply only existing labels that
clearly match the work, and never create labels. Explicit labels or an explicit
label opt-out override inference.

## Create or update safely

Use available hosting tools with explicit base, head, title, body, and draft
state. Prefer a body file over shell-interpolated multiline text. For GitHub,
`gh pr create` or `gh pr edit` is suitable when available; pass assignees and
labels during creation when possible.

If no authenticated hosting tool is available, finish the requested text and
local verification, then report the blocked remote mutation instead of claiming
success.

After creation or update, read authoritative hosting state and verify the URL,
ready/draft state, base, head repository and branch, head commit, title, body,
assignees, and labels. If metadata application fails after creation, report the
PR as created and the metadata step as incomplete rather than retrying creation.
