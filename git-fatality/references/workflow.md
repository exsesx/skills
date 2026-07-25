# Execution Workflow

Read this reference only when executing a state-changing Git or GitHub stage.

## Authorization and state

- An explicit imperative in the current request authorizes the named action
  set. Drafting is still required, but a second approval round is not.
- Preview-first wording such as "show me before committing" or "create it after
  I approve" requires a stop after the draft.
- A vague explicit invocation with no verbs requires a proposed action set and
  approval.
- If the user approves a proposal with "yes" or "do it", apply it only to that
  proposal.
- After staging, record `branch`, `HEAD`, and `staged_snapshot` from
  `scripts/git-snapshot.sh`. Recheck all three immediately before committing.

## Branch creation

Create a branch only when the user requests it or it is an explicit stage in an
authorized end-to-end flow.

If the current branch is already suitable and no new branch was requested,
keep it. Do not rename an existing branch unless the user explicitly asks.
Inspect active local branch names first. When remote samples are needed,
enumerate each configured remote separately and remove its
`refs/remotes/<remote>/` namespace, for example with
`%(refname:lstrip=3)`. Exclude symbolic `<remote>/HEAD` and stale refs; never
treat a remote name such as `origin` as part of the branch convention.
Compare type or ticket prefixes, separator style, topic casing, and typical
topic length; do not call a pattern clear from one incidental branch.

Use this naming precedence:

1. the user's exact valid branch name
2. a clear repository convention from active local and remote branches
3. `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, or `chore/<topic>`

Keep fallback topics lowercase, short, and hyphen-separated. Include a ticket
only when the user supplies one or the repository clearly requires it. If the
name and base are both clear, announce the inferred name and continue under the
existing branch-creation authorization. Pause for ambiguity, collision, an
unexpected base, or a request to rename an existing branch.

Use create-only semantics for ordinary branch creation. Never force-create,
reset an existing branch, or create an orphan branch unless the user explicitly
requests that exact behavior.

## Named synchronization prerequisites

When explicit invocation or a mixed finalization request names fetch, pull,
merge, rebase, cherry-pick, or conflict resolution, perform only the named
operation and strategy. Inspect dirty state and divergence first.

Do not silently substitute merge for rebase, pull for fetch, stash for a dirty
tree, or force operations for a rejected update. A requested merge authorizes
the merge commit produced by that merge, but not a later unrelated commit,
push, or PR.

## Staging and commit scope

- If specific files or changes are named, stage only those paths or hunks.
- If the user says "all" or "everything", stage all inspected changes except
  suspected secrets or other hazards that require confirmation.
- If only staged changes exist, commit the staged set.
- If staged and unstaged changes coexist, use the request and thread context to
  identify intent. Pause only when the boundary cannot be determined safely.
- For push-only work, never stage or commit dirty files.
- Preserve unrelated changes even when they make the worktree dirty.
- Split independent work into atomic commits when requested or when one commit
  would conceal meaningful boundaries. Re-snapshot after each commit.

## Verification

Use repository instructions and established commands to choose proportionate
checks. At minimum before committing:

- inspect the complete cached diff
- run `git diff --cached --check`
- confirm no generated-file drift or newly staged paths appeared
- compare `branch`, `HEAD`, and `staged_snapshot` with the approved proposal

After committing, verify `git show --stat --oneline HEAD` and current status.
Before pushing, recheck the branch, selected remote, upstream, and exact commit
range. After pushing, verify the local branch and upstream relationship.
Preserve and report any hook-created or generated changes instead of staging
them silently.

## Push behavior

Push the exact current branch to its configured upstream. If none exists,
choose the configured push remote or the single clear repository remote and
use `git push -u <remote> <branch>`. Do not assume `origin` when multiple
remotes make the destination ambiguous.

Refresh remote-tracking refs when freshness matters and the environment allows
it, but never turn a push request into an unrequested pull, merge, or rebase.

## Failure recovery

- Hook failure: report the hook output; do not use `--no-verify` automatically.
- Signing failure: preserve the index; do not disable signing automatically.
- Authentication or network failure: preserve state and report the blocker.
- Non-fast-forward push: inspect divergence; do not force-push automatically.
- Partial PR success: verify whether the PR exists before retrying creation.
- Backend unavailable: finish safe local drafting and verification, then stop
  before the blocked mutation.
