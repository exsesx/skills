---
name: git-fatality
description: >-
  Use this skill whenever the user explicitly invokes git-fatality, and
  otherwise when they ask to draft commit or pull request text, stage and
  commit an agreed scope, push or publish a branch, create or update a pull
  request, or finalize or ship branch work through a covered commit, push, or
  PR action. Support combined flows, including creating a branch before
  commit, push, and PR creation. Do not invoke it implicitly for status or
  diff review, fetch or pull, merge, rebase, cherry-pick, conflict resolution,
  stash, branch management, or general synchronization unless the same
  request also includes a covered finalization action; in mixed requests,
  apply it only to the finalization segment.
---

# Git Fatality

Finalize exactly the Git work the user requests. Keep the workflow portable
across Codex, Claude Code, and other Agent Skills clients; never depend on
client-specific permission metadata for safety.

## Operating contract

- Treat explicit invocation in either client as intentional activation.
- Treat an explicit command such as "commit and push" as authorization for
  exactly those actions after inspection and scope verification. Do not ask
  for the same approval a second time.
- Treat "create a branch, commit, push, and create a PR" as authorization for
  that complete sequence, including choosing a branch name when one can be
  inferred safely.
- Pause before acting only when the user asks for a preview first, the scope or
  destination is materially ambiguous, repository state changes after the
  proposal, or execution would require an action the user did not authorize.
- If the user invokes the skill without naming actions, inspect, propose the
  action set and text artifacts, and wait for approval.
- Never widen the request. Commit plus push does not imply PR creation; push
  only does not imply staging or committing; PR text only does not imply PR
  creation.
- Apply "yes" or "do it" to the most recently proposed action set. Compliments,
  silence, reactions, harness auto-approval, and allow-all modes are not user
  authorization.
- Bind authorization to both the action set and the inspected state. Re-scope
  if either changes materially.

If explicit invocation includes a named prerequisite such as fetch, pull,
merge, rebase, cherry-pick, conflict resolution, or branch creation, perform
that named stage without inferring additional Git operations. These operations
do not trigger this skill implicitly on their own.

## Compose the requested stages

Select only the stages the user requested:

1. create or switch branch
2. perform explicitly named synchronization prerequisites
3. choose and stage commit scope
4. create one or more commits
5. push or publish the branch
6. draft, create, or update a pull request

Do not force the request into one predefined flow. A dirty worktree does not
block push-only work when the commits being pushed are already clear and the
push will not touch those files.

Read [references/workflow.md](references/workflow.md) before executing any
state-changing stage. Read
[references/pull-requests.md](references/pull-requests.md) only when PR text or
PR mutation is requested. Read
[references/examples.md](references/examples.md) when drafting commit or PR
text, especially when repository conventions are unclear.

## Inspect before drafting or acting

Resolve the script from the skill directory, but run it against the user's
target repository without changing into the skill directory:

```bash
bash <resolved-skill-dir>/scripts/git-snapshot.sh <target-repo-path>
```

Resolve `<resolved-skill-dir>` from this `SKILL.md`; in Claude Code,
`${CLAUDE_SKILL_DIR}` is the same directory. If `<target-repo-path>` is
omitted, the script inspects the current repository. The script is read-only.
If Bash or the bundled script is unavailable, perform the equivalent read-only
Git inspection manually and preserve the same branch, `HEAD`, and exact staged
snapshot checks.

Use its output to establish:

- repository root, branch or detached state, `HEAD`, and upstream
- ahead and behind counts based on current remote-tracking refs
- merge, rebase, cherry-pick, revert, or bisect state
- staged, unstaged, and untracked paths
- a staged snapshot fingerprint bound to `HEAD`

The snapshot is a summary, not a substitute for inspection. Also inspect:

- the full staged diff for commits
- the full branch range and base diff for PRs
- relevant unstaged and untracked contents when deciding scope
- repository instructions and established verification commands
- recent non-merge commits for message conventions

Do not print secret values. Treat `.env*`, credentials, keys, tokens, signing
material, and unexpectedly large or generated artifacts as scope hazards.

## Draft and execute

Before a commit, identify the exact file or hunk scope and draft every commit
message. Before a PR mutation, draft the title and body. For an already
authorized end-to-end request, share the plan concisely and continue; do not
stop merely to repeat the approval gate.

Prefer explicit file paths when staging. Use `git add -A` only when the user
clearly requested all changes and inspection found no scope hazards. Preserve
unrelated staged, unstaged, and untracked work.

If the diff contains independent changes, propose or create multiple atomic
commits when the user requests multiple commits or when one message would hide
meaningful scope boundaries. Never force unrelated work into one commit.

Immediately before each commit:

1. run the repository's proportionate verification unless the user explicitly
   scoped it out
2. run `git diff --cached --check`
3. rerun the bundled `git-snapshot.sh`
4. confirm `branch`, `HEAD`, and `staged_snapshot` still match the approved
   proposal

If they do not match, stop and re-scope. After each commit, push, and PR
mutation, verify the resulting state from Git or GitHub rather than assuming
the command succeeded completely.

Immediately before pushing, recheck the branch, remote, upstream, and exact
commits to publish. Immediately before PR creation or update, recheck the head,
base, pushed state, and whether a matching open PR now exists.

## Safety boundaries

- Do not invent a commit when no meaningful commit scope exists.
- Do not stage a suspected secret without explicit confirmation.
- Do not bypass hooks with `--no-verify`, disable signing, rewrite published
  history, force-push, discard work, or delete branches unless the user
  explicitly requests that exact action after the risk is known.
- If a hook, signer, authentication provider, network, push, or PR command
  fails, preserve the verified scope, report the exact blocker, and continue
  only with safe actions already authorized.
- If a push is rejected as non-fast-forward, do not pull, rebase, merge, or
  force-push automatically. Inspect and request or use existing authorization
  for the specific recovery action.

## Text policy

Apply this precedence:

1. explicit user instructions
2. repository instructions and PR templates
3. a clear convention in recent history or merged PRs
4. the user defaults in [references/examples.md](references/examples.md)

Do not claim tests, checks, labels, assignees, pushes, or PR state that were not
verified.
