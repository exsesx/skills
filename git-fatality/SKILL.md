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

- Resolve the requested actions from the current request and established
  conversation context. Requests such as "commit and push" or "can you push
  this?" authorize those actions after relevant inspection. Earlier scoped
  authorization remains valid when the action, scope, and destination still
  match; do not ask again just because the skill is invoked in a later turn.
- Never widen the action set. Commit plus push does not imply a PR; push-only
  does not imply staging or committing. Creating a PR includes publishing the
  inspected, already committed scope needed for that PR; it does not include
  making a new commit. Explicit restrictions such as "do not push" win.
- If neither the request nor established context identifies authorized actions,
  inspect, propose the action set and text, and wait. Preview-first wording
  requires a stop before mutation.
- Apply "yes" or "do it" only to the latest concrete proposal. Praise, silence,
  reactions, harness approval, or allow-all modes are not authorization.

Explicit user instructions take precedence over this skill's defaults. Complete
authorized inspection and drafting before asking a necessary question. If a
skill rule requires a pause, name and link to the file, quote the relevant rule,
and explain the concrete unresolved action or scope.

## Routine finalization

Use this path only when the requested actions, scope, branch, and destination
are clear and there is no preview, detached `HEAD`, in-progress Git operation,
secret hazard, rewrite/force action, or recovery. Otherwise use the complex
guidance below.

A routine commit-only, push-only, or commit-and-push request is one compact
operation. Do not create or update a formal plan, todo list, or progress
checklist. Give at most one short progress sentence, then act or report a real
blocker.

Inspect the current branch, `HEAD`, worktree/index status, and exact relevant
diff before mutation. Detect merge, rebase, am, cherry-pick, revert, and bisect
state. Inspect upstreams, remote refs, and outgoing commits when publishing;
inspect the base and published head for PR work. A local commit or text-only
commit draft needs no remote lookup. Reuse applicable repository instructions,
convention mode, remote knowledge, and successful validation from the current
task.

Treat each requested stage independently. Skip a commit with no meaningful
scope. A push is complete only when the intended remote branch exists at the
intended commit and any requested upstream setup is satisfied. A new branch
can need publishing even when its commits already exist on another remote
branch. If every requested stage is complete, report that immediately.

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
destination ref, and exact outgoing commits immediately before publishing.
Check the actual remote ref rather than relying only on cached tracking refs
or ahead counts. After publishing, verify that remote ref's commit and the
intended upstream relationship.

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
