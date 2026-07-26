---
name: git-fatality
description: >-
  Finalizes Git work through commit, push, branch, and pull request actions.
  Use when the user explicitly invokes git-fatality or asks to draft commit or
  PR text, commit an agreed scope, push or publish a branch, create or update a
  pull request, or otherwise ship work through one of those actions. Do not
  invoke it implicitly for status or diff review, fetch, pull, merge, rebase,
  cherry-pick, conflict resolution, stash, or branch management unless the same
  request includes a covered finalization action.
---

# Git Fatality

Execute exactly the Git finalization the user requests. Keep the workflow
portable across Codex, Claude Code, and other Agent Skills clients.

## Authorization

- An explicit imperative such as "commit and push" authorizes exactly those
  actions after scope and destination inspection. Do not ask again.
- Never widen the action set. Commit plus push does not imply a PR; push-only
  does not imply staging or committing.
- If invocation names no actions, inspect, propose the action set and text, and
  wait. Preview-first wording also requires a stop before mutation.
- Apply "yes" or "do it" only to the latest concrete proposal. Praise, silence,
  reactions, harness approval, or allow-all modes are not authorization.

## Routine finalization

Use this path only when the requested actions, scope, branch, and destination
are clear and there is no preview, detached `HEAD`, in-progress Git operation,
secret hazard, rewrite/force action, or recovery. Otherwise use the complex
guidance below.

A routine commit-only, push-only, or commit-and-push request is one compact
operation. Do not create or update a formal plan, todo list, or progress
checklist. Give at most one short progress sentence, then act or report a real
blocker.

Inspect current Git state and the exact relevant diff before mutation. Refresh
the branch, `HEAD`, index/worktree scope, upstream, and outgoing commit range on
every invocation. Detect merge, rebase, am, cherry-pick, revert, and bisect
state. Reuse applicable repository instructions, convention mode, remote
knowledge, and successful validation from the current task.

Treat each requested stage independently. Skip a commit with no meaningful
scope and skip a push with no outgoing commits at push time. If every requested
stage is a no-op, report that immediately. Never invent an empty commit or issue
a pointless push.

Finalization does not discover or rerun project builds or tests by default.
Run checks only when the user requests them, applicable repository instructions
require them, or no still-applicable result exists for a required check. Never
bypass normal commit hooks.

For a commit:

- stage only the intended files or hunks and preserve unrelated work
- inspect the complete staged diff and run `git diff --cached --check`
- immediately before committing, reconfirm branch and `HEAD` and re-inspect the
  staged scope
- after committing, inspect the commit and confirm its content matches

For a push, do not touch dirty files. Recheck the branch, selected remote,
upstream, and exact outgoing commits immediately before publishing, then verify
the resulting upstream relationship.

If any authorization-relevant value changes between inspection and mutation,
stop and re-scope before continuing.

## Convention mode

`personal` is the default and performs no history queries for style. Phrases
such as "match repo style" or `conventions: repo` select `repo`; "use my style"
or `conventions: personal` select `personal`. The latest selection persists for
later invocations in the same task until the user changes it.

Use this precedence:

1. exact formatting or naming requested now
2. applicable repository instructions and required PR templates
3. the selected convention source
4. personal conventions when `repo` evidence is unclear or unavailable

In `repo` mode, inspect only bounded evidence for the requested artifact:
recent non-merge commits for commit text, active branch names only when naming
a branch, and recent merged PRs only when PR instructions or templates leave
style unresolved. Never fetch solely to discover style. Push-only and no-op
flows perform no convention lookup.

### Personal commit style

- Use a lowercase imperative subject with no automatic Conventional Commit
  prefix. Describe what changed, not how.
- Target 72 characters or fewer for the subject; move detail into the body.
  Wrap body lines near 72 when practical, but never split or truncate an
  indivisible URL, identifier, filename, command, or version.
- Use a body only for non-obvious rationale, breaking changes, or distinct
  sub-changes. Use a semicolon only for two tightly related clauses and `- `
  bullets for distinct points.
- Use no sentence-ending periods. Keep body prose lowercase too, except proper
  names, acronyms, identifiers, filenames, and versions.
- Include ticket IDs only when supplied, explicitly requested, or required.

### Personal pull request style

Use the required repository template when present. Otherwise use the commit
subject style for the title and `## Summary` with concise bullets. Do not add a
test-plan section unless requested or required. Generated titles and body
bullets follow the personal commit casing and punctuation rules. Read
[references/pull-requests.md](references/pull-requests.md) for any PR drafting
or mutation.

### Personal branch style

- `feature/<topic>` for a new capability or meaningful behavior
- `fix/<topic>` for a defect, regression, or incorrect behavior
- `chore/<topic>` for dependencies, tooling, CI, configuration, documentation,
  tests, or behavior-preserving refactors

Use a meaningful lowercase kebab-case topic of roughly two to six words. Do not
invent ticket IDs. An exact valid branch name supplied by the user wins.

## Complex flows and safety

Read [references/complex-flows.md](references/complex-flows.md) only for branch
creation, named synchronization, multiple commits, ambiguous scope,
preview/pause state binding, failures, recovery, rewrite/force operations, or
other materially complex finalization.

Never invent a commit without meaningful scope; stage a suspected secret;
use `--no-verify` or `--no-gpg-sign`; disable signing; rewrite published
history; force-push; discard work; or delete branches unless the user explicitly
requests the exact risky action after the risk is known. Preserve verified state
on failure. A non-fast-forward push never authorizes an automatic pull, merge,
rebase, or force-push.

Do not print secret values. Treat `.env*`, credentials, keys, tokens, signing
material, and unexpectedly large or generated artifacts as scope hazards;
inspect them without exposing sensitive contents and require confirmation
before staging a suspected secret.
