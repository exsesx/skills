---
name: finish-branch
description: Wrap up branch work safely — draft and execute commit messages, commits, pushes, and pull requests with approval gates. Use when the user asks to write a commit message, commit changes, push a branch, create a PR, or finish a branch.
allowed-tools: Bash(git *) Bash(gh *) Read Grep Glob
argument-hint: "[commit|push|pr|finish]"
---

# Finish Branch

## Current state

```!
git status --short --branch 2>/dev/null || echo "not a git repo"
```

```!
git log --oneline -5 2>/dev/null || true
```

## Step 1 — Inspect

Before drafting anything, gather the full picture:

- Run `git status` to see staged, unstaged, and untracked files.
- Run `git diff --stat` (unstaged) and `git diff --cached --stat` (staged) to understand the scope.
- Identify the current branch and its upstream (`git rev-parse --abbrev-ref @{u}`).
- If preparing a PR, run `git log --oneline main..HEAD` (or the appropriate base) to see all commits.

Do not start writing a commit message or PR text without completing inspection.

## Step 2 — Infer the requested flow

Map the user's request to exactly one of these flows:

| Flow | Trigger examples |
|------|-----------------|
| **commit message only** | "write a commit message", "what should the message be?" |
| **commit** | "commit these changes" |
| **commit + push** | "commit and push" |
| **PR draft only** | "draft a PR", "write the PR title and body" |
| **PR draft + creation** | "create the PR after I approve" |
| **full finish-branch** | "finish this branch", "wrap this up" |

Rules:
- If the request is narrow (e.g., "write a commit message"), stay narrow — do not propose a PR.
- If the request is vague (e.g., "wrap this up"), propose the relevant next steps based on repo state.
- Never assume a push is wanted unless the user says so.
- Never assume a PR is wanted unless the user says so.

## Step 3 — Draft before acting

Draft all text artifacts before any irreversible action.

**Safe (no approval needed):**
- Inspecting repo state and diffs
- Drafting commit messages
- Drafting PR title and body
- Summarizing the proposed next action

**Irreversible (approval required before each):**
- `git commit`
- `git push`
- PR creation via `gh pr create`
- Merge
- Branch deletion

Present the draft text and state the exact next action. Then stop and wait for approval.

Approval is scoped — "approve the commit" does not mean "also push and create a PR."

## Step 4 — Execute the approved scope

After approval, execute only what was approved. Report concisely:

- What was done (committed, pushed, PR created)
- Branch name
- Upstream branch if relevant
- PR URL if created

## Commit message policy

- Imperative mood ("add", "fix", "refactor")
- Describe what changed, not how
- Lowercase except proper names, acronyms, identifiers
- No trailing period, no filler
- Subject line: prefer under 72 characters, prioritize clarity
- Body only when: (a) the reason is non-obvious, (b) breaking change, (c) multiple tightly related subchanges need itemization
- Body lines ≤ 72 characters, lowercase, "- " bullets for lists
- Reference ticket/issue IDs when available

## Pull request policy

- Concise title, same style as commit subject lines
- Always include `## Summary` with bullet points
- Include `## Test plan` only when it adds real value
- Do not create the PR until the user approves the drafted text

## When to refuse or pause

- **No meaningful changes** — do not invent a commit or PR.
- **Unrelated work mixed in one diff** — recommend splitting before forcing one message.
- **Ambiguous repo state** — explain what you see before proposing destructive actions.
- **No upstream branch** — adapt the push/PR path and tell the user.
- **Backend unavailable** — still draft the text, state the blocker, stop before the blocked action.

## References

- Read [references/workflow.md](references/workflow.md) for edge-case handling and detailed refusal/recovery policy.
- Read [references/examples.md](references/examples.md) for trigger examples and sample outputs.
