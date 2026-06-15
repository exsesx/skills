# Extended Workflow Policy

This document covers edge cases and detailed policy beyond the core flow in SKILL.md.

## Approval scope details

Approval should be scoped to the immediate action set. Examples:

- "yes, commit" → commit only, do not push
- "commit and push" → commit + push, do not create PR
- "go ahead with the PR" → create PR, assumes commit and push are already done or approved in same request
- "do it all" → commit + push + create PR, but still show draft text first

If the user approves a narrow scope, do not widen it. If the user says "yes" without specifying, apply approval to the most recently proposed action set — do not escalate.

## Handling staged versus unstaged changes

- If there are staged changes and the user asks to commit, commit the staged changes.
- If there are only unstaged changes and the user asks to commit, ask whether to stage all or specific files. Do not silently `git add -A`.
- If there are both staged and unstaged changes, mention both and ask which set the user intends to commit.
- Never stage files that look like secrets (`.env`, credentials, tokens) without explicit confirmation.

## Handling missing upstream

When pushing to a branch with no upstream:

- Use `git push -u origin <branch>` to set the upstream.
- Tell the user what you are doing and why.
- If the remote does not exist or the push fails, report the error and stop.

## Handling branch creation

Create a branch only when the requested flow needs one, such as a detached worktree, work still on `main`, or an explicit request to branch out.

- If the current branch is already a suitable feature/fix/docs/chore branch, keep it.
- If the user gives a branch name, use that name unless it is invalid or unsafe.
- If creating a branch, draft the proposed branch name and wait for explicit approval before running `git switch -c <branch>`.
- Do not rename an existing branch unless the user explicitly asks.

## Handling PR base branch

- Default to `main` as the base branch.
- If the repo uses a different default branch (e.g., `master`, `develop`), detect it from `git remote show origin` or the repo's default branch setting.
- If the user specifies a base branch, use that.

## Multi-commit branches

When the branch has multiple commits ahead of base:

- For commit message drafting, work with the current staged/unstaged changes only.
- For PR drafting, consider the full commit range (`git log --oneline base..HEAD`).
- Summarize the branch's work, not just the latest commit.

## Recovering from tool failures

- If `git commit` fails (e.g., pre-commit hook), report the failure and the hook output. Do not retry with `--no-verify`.
- If `gh pr create` fails, report the error. Offer to retry or to output the PR text for manual creation.
- If `git push` is rejected (non-fast-forward), explain the situation. Do not force-push without explicit approval.

## Empty or trivial changes

- If `git diff` and `git diff --cached` are both empty and there are no untracked files, refuse to create a commit.
- If the only changes are whitespace or formatting, mention this and ask if the user still wants to proceed.

## Auto-mode and yolo modes

Harness auto-approval (Claude Code auto-accept, `codex --yolo`, `--dangerously-skip-permissions`, allow-all permission settings) grants *tool* permission, not *user* approval. The two are independent.

What counts as user approval to create a branch, commit, push, open a PR, merge, or delete a branch:

- An explicit verb from the user in this conversation: `"create the branch"`, `"branch out"`, `"commit"`, `"push"`, `"open the PR"`, `"create the PR"`, `"yes, commit and push"`, `"do it all"`, `"merge it"`, `"delete the branch"`.
- Scoped to the verb given: `"commit"` is not approval to push; `"push"` is not approval to PR; `"do it all"` covers the drafted set but not new destructive actions.

What does **not** count:

- Harness permission mode being permissive.
- `"looks good"`, `"nice"`, `"thanks"`, `"ok"`, `"sure"`, emoji reactions, silence — these mean the draft reads well, not that the action is approved.
- Approval of a previous action (earlier commit approval is not approval of a later push).

If unsure whether a phrase counts, treat it as not approval and ask.

## Convention detection signals

Run `git log -20 --pretty=%s` and look for a dominant pattern. A pattern is "clear" when ≥60% of the 20 subjects match it.

Signals to look for:

- **Conventional Commits:** `type(scope): subject` or `type: subject` where `type` is one of `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`, `revert`. Trailing `!` or `BREAKING CHANGE:` footer indicates breaking.
- **Gitmoji:** subjects start with an emoji (`:sparkles:`, `:bug:`, `✨`, `🐛`).
- **Ticket prefix:** `PROJ-123:`, `[PROJ-123]`, `#1234` at the start.
- **Casing habit:** all-lowercase vs Sentence case vs Title Case.
- **Length habit:** median subject length — don't drift far from it.
- **Semicolon separator:** frequent `;` inside subjects.
- **Body frequency:** run `git log -20 --pretty=%B` and count commits with a blank line + body. If most commits have bodies, include one; if almost none do, don't add one for a trivial change.

Fallback behavior:

- If no clear pattern: use the user default from SKILL.md.
- If patterns conflict (e.g. half Conventional, half not): note the ambiguity to the user, propose the user default, and offer to match Conventional instead.
- If `gh` is not installed or not authed: skip the merged-PR sampling step silently; the `.github` template check and defaults still apply.
- If `.github/PULL_REQUEST_TEMPLATE*` exists but is empty: treat as "no template".
- `.github/PULL_REQUEST_TEMPLATE/` (directory form) can contain several templates keyed to work type (e.g. `bugfix.md`, `feature.md`). List the directory and pick the best match; if none fits, use the default file `.github/PULL_REQUEST_TEMPLATE.md` if present, else fall back to the user default.

## Branch convention detection signals

Run `git branch --format='%(refname:short)'` and sample remote branches with `git branch -r --format='%(refname:short)'` when local history is too small. Prefer local active branch names over stale remote names.

Signals to look for:

- **Type prefix:** `feat/`, `fix/`, `docs/`, `chore/`, `feature/`, `bugfix/`, or repo-specific equivalents.
- **Ticket prefix:** `PROJ-123/short-topic`, `PROJ-123-short-topic`, or similar. Treat this as a repo convention only when branch samples clearly use it.
- **Separator style:** slash paths (`feat/login`), hyphen-only names (`feat-login`), or nested paths (`team/feat/login`).
- **Topic casing:** lowercase hyphenated topics, snake case, or sentence-like branch names.
- **Topic length:** short topic only versus longer descriptive phrases.

Fallback behavior:

- If no clear pattern exists: use `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, or `chore/<topic>`.
- In the fallback, `<topic>` is lowercase, hyphen-separated, and based on the actual diff or requested work.
- Do not include ticket IDs in fallback branch names.
- If patterns conflict, note the ambiguity, propose the fallback, and offer the closest detected alternative.
