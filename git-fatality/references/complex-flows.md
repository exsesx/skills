# Complex Git Flows

Read this reference only when finalization includes branch creation, named
synchronization, multiple commits, ambiguous scope, a preview or pause,
recovery, or a risky operation.

Before mutation, detect detached `HEAD` and merge, rebase, am, cherry-pick,
revert, or bisect state. Do not treat an in-progress operation as routine or
create an unrelated commit inside it. Continue or conclude it only when the
user requested that exact operation and the state is appropriate.

## Preview, ambiguity, and state drift

- A vague invocation with no action verbs requires a concrete action-set and
  text proposal before mutation.
- Preview-first wording requires a stop after drafting.
- Bind a paused commit proposal to the branch, `HEAD`, and a read-only hash of
  the raw staged diff. Bind a push proposal to the branch, remote, upstream,
  and outgoing range.
- After new user input or any relevant state change, re-inspect and compare
  those values. Re-scope instead of acting on stale authorization.
- A formal plan is optional only when it materially clarifies independent
  commits, ambiguity, synchronization, PR mutation, or recovery.

## Branch creation

Create or switch branches only when requested or included in an authorized
end-to-end flow. Keep a suitable current branch when no new branch was
requested, and never rename it implicitly.

Use the user's exact valid name first. In `personal` mode, use the branch policy
in `SKILL.md`. In `repo` mode, inspect active local branch names and only the
configured remotes needed for evidence. Normalize remote namespaces, exclude
symbolic remote `HEAD` refs and stale refs, and fall back to the personal policy
when no dominant convention exists.

Use create-only semantics. Pause for an invalid name, collision, unsafe base,
unexpected branch state, or a requested rename. Never force-create, reset, or
create an orphan branch unless explicitly requested after the risk is known.

## Named synchronization

When explicit invocation or a mixed finalization request names fetch, pull,
merge, rebase, cherry-pick, or conflict resolution, perform only the named
operation and strategy. Inspect dirty state and divergence first.

Do not substitute merge for rebase, pull for fetch, stash for a dirty tree, or
force behavior for a rejected update. A requested merge authorizes its merge
commit, not an unrelated later commit, push, or PR.

## Ambiguous scope and multiple commits

- Named files or changes define the scope; stage only those paths or hunks.
- "All" or "everything" includes every inspected change except suspected
  secrets or other hazards that require confirmation.
- When staged and unstaged changes coexist, use the request and current task
  context. Pause only when the boundary cannot be resolved safely.
- Split independent changes when requested or when one commit would conceal
  meaningful scope boundaries. Re-inspect the index before each commit.
- Push-only work never stages, unstages, commits, or discards dirty files.

## Failure and recovery

- Hook or signing failure: preserve the index and never weaken the check.
- Authentication, network, or hosting failure: preserve local state and report
  the blocker.
- Non-fast-forward push: inspect divergence; do not choose pull, merge, rebase,
  or force-push without authorization.
- Partial PR success: verify whether the PR exists before retrying creation.
- Rewrite, force-push, discard, or deletion: explain the concrete risk and
  require authorization for that exact action.

After every mutation, verify authoritative Git or hosting state. Preserve and
report hook-created or generated changes instead of staging them silently.
