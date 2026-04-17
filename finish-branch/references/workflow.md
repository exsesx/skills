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
