---
name: git-fatality
description: Finalize Git branch work safely — inspect changes, draft commit and pull request text, and require approval before commits, pushes, or PR creation. Use when the user asks to write a commit message, commit changes, push a branch, create a PR, finish a branch, or run git fatality.
allowed-tools: Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git branch:*) Bash(git rev-parse:*) Bash(git remote:*) Bash(git add:*) Bash(gh pr list:*) Bash(gh pr view:*) Bash(gh pr edit:*) Bash(gh label list:*) Bash(ls:*) Read Grep Glob
argument-hint: "[commit|push|pr|finish]"
---

# Git Fatality

## Current state

```!
git status --short --branch 2>/dev/null || echo "not a git repo"
```

```!
git log --oneline -5 2>/dev/null || true
```

## Auto-mode is not approval

Harness auto-approval modes (Claude Code auto-accept, `codex --yolo`, any allow-all permission setting) grant *tool* permission. They do **not** grant *user* approval to commit, push, or open a PR.

- Never run `git commit`, `git push`, `gh pr create`, merges, or branch deletes until the user gives an explicit approval phrase in this conversation — e.g. "commit", "push", "open the PR", "yes, commit and push", "do it all".
- `"looks good"`, `"nice"`, `"thanks"`, silence, or a thumbs-up are **not** approval.
- If you're unsure whether a phrase counts as approval, treat it as not approval and ask.
- Approval is scoped to the phrase given — see [references/workflow.md](references/workflow.md) for scope rules.

## Step 1 — Inspect

Gather the full picture before drafting anything. Run only the commands you need for the requested flow.

**Repo state (always):**
- `git status` — staged, unstaged, untracked.
- `git diff --stat` and `git diff --cached --stat` — scope.
- `git rev-parse --abbrev-ref HEAD` and `git rev-parse --abbrev-ref @{u}` — branch and upstream.
- For a PR: `git log --oneline <base>..HEAD` for the full commit range.

**Convention signals (for commit/PR drafts):**
- `git log -20 --pretty=%s` — scan last 20 subjects for an existing convention: Conventional Commits (`type(scope): subject`), gitmoji prefix, ticket prefix (`PROJ-123:`), casing, semicolon-as-separator, body frequency. A pattern is "clear" at ≥60% of the 20 subjects.
- `ls .github/PULL_REQUEST_TEMPLATE.md .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE/ 2>/dev/null` — check both single-file and directory-form templates. The directory form (`.github/PULL_REQUEST_TEMPLATE/*.md`) lets a repo ship multiple templates; list its contents and pick the one matching the work type if present.
- If preparing a PR and `gh` is available: `gh pr list --state merged --limit 10 --json title,body` — sample recent merged PR style. Skip silently if `gh` isn't installed or authed.

Do not start drafting until inspection is complete. See [references/workflow.md](references/workflow.md) for detection heuristics.

## Step 2 — Infer the requested flow

Map the user's request to exactly one of these flows:

| Flow | Trigger examples |
|------|-----------------|
| **commit message only** | "write a commit message", "what should the message be?" |
| **commit** | "commit these changes" |
| **commit + push** | "commit and push" |
| **PR draft only** | "draft a PR", "write the PR title and body" |
| **PR draft + creation** | "create the PR after I approve" |
| **full git-fatality** | "finish this branch", "wrap this up", "git fatality" |

Rules:
- If the request is narrow (e.g., "write a commit message"), stay narrow — do not propose a PR.
- If the request is vague (e.g., "wrap this up"), propose the relevant next steps based on repo state.
- Never assume a push is wanted unless the user says so.
- Never assume a PR is wanted unless the user says so.

## Step 3 — Draft before acting

Draft all text artifacts before any irreversible action.

**Safe (no approval needed):**
- Inspecting repo state, diffs, git log, PR templates, recent merged PRs.
- Drafting commit messages and PR text.
- Summarizing the proposed next action.

**Irreversible (explicit approval required before each):**
- `git commit`
- `git push`
- `gh pr create`
- Merge
- Branch deletion

Present the draft text, state the exact next action, then stop and wait for approval. Approval is scoped — "approve the commit" does not mean "also push and create a PR."

## Step 4 — Execute the approved scope

After approval, execute only what was approved. When a PR is created, also run the post-creation steps in the [Pull request policy](#after-gh-pr-create) (self-assign + label) — they are part of PR creation, not a separate approval. Report concisely:

- What was done (committed, pushed, PR created)
- Branch name
- Upstream branch if relevant
- PR URL if created
- Assignee and any labels applied

## Commit message policy

Precedence:

1. **Match the detected convention.** If `git log -20` shows a clear pattern (≥60%), match it: prefix style (`feat:`, `fix(scope):`, gitmoji, ticket ID), casing, subject length habit, body frequency. Don't second-guess a consistent repo.
2. **Otherwise, user default:**
   - Subject is lowercase. One thought when possible; use `;` to join logically related changes that can't be expressed as one (e.g. `fix login redirect; update session expiry default`).
   - Body only when: the "why" is non-obvious, there's a breaking change, or multiple sub-changes need itemization.
   - Commit bodies are not regular sentence prose.
   - Use a compact semicolon-separated body only for two tightly related clauses.
   - Use `- ` bullets for distinct points, preservation lists, future-work notes, or anything that would otherwise become paragraph prose.
   - **Lowercase applies to subject AND body.** Exceptions only for proper names, acronyms, identifiers, and version/release tokens: `Node.js`, `LTS`, `PostgreSQL`, `useMemo`, `settings.json`, `JWT`, `UUID`.
   - **No sentence-ending periods anywhere — subject, bullets, or compact body.**
   - Lowercase-after-period reads broken; don't produce it. If you need punctuation between thoughts, use `;` or switch to bullets.
   - Imperative mood ("add", "fix", "refactor"). Describe what changed, not how. Lines ≤72 characters. Reference ticket/issue IDs when available.

See [references/examples.md](references/examples.md) for detection cues and good/bad samples.

## Pull request policy

Precedence:

1. **Fill the `.github` template if one exists.** Check both `.github/PULL_REQUEST_TEMPLATE.md` (single-file form) and `.github/PULL_REQUEST_TEMPLATE/*.md` (directory form — a repo may ship multiple templates per work type). Use the matching template verbatim as the skeleton. Fill its sections; do not invent extra ones, do not remove sections the template includes.
2. **Mirror recent merged PRs.** If `gh pr list --state merged` shows a consistent style (e.g. everyone uses `## What`/`## Why`, or no headings at all), match it. If a recent merged PR covers similar work, mirror its structure.
3. **Otherwise, user default:**
   - Title: same style as commit subject.
   - `## Summary` with bullet points.
   - **No `## Test plan` unless the user explicitly asked for one in this conversation.**

Title and body follow the same casing rules as commit messages.

### After `gh pr create`

Once the PR is created, complete it with two automatic steps (no separate approval needed — they are part of the approved PR creation). Both default to on; the user's words in this conversation override them.

1. **Assign to the current user.** Default: `gh pr edit <number> --add-assignee @me`. `@me` resolves to the authenticated GitHub account — never hardcode a username. Overrides:
   - Named assignee ("assign alice", "assign me and bob") → use those instead of `@me`.
   - Opt-out ("don't assign", "no assignee", "leave it unassigned") → skip assignment.
2. **Apply matching existing labels.** Default: fetch the repo's labels with `gh label list`, then apply only labels that clearly match the work via `gh pr edit <number> --add-label <label>`. Prefer the repo's equivalents of `enhancement` (feature work), `bug` (bugfixes), and `documentation` (docs), but use the repo's actual label names. Never create new labels. Omit labels entirely if none clearly fit. Overrides:
   - Named labels ("label it `bug`", "use `chore` and `docs`") → apply exactly those (still must exist in `gh label list`; never create).
   - Opt-out ("no labels", "skip labels", "don't label it") → skip labeling.

The override applies only to the action the user named — "don't assign" does not suppress labels, and "no labels" does not suppress the assignee.

## When to refuse or pause

- **No meaningful changes** — do not invent a commit or PR.
- **Unrelated work mixed in one diff** — recommend splitting before forcing one message.
- **Ambiguous repo state** — explain what you see before proposing destructive actions.
- **No upstream branch** — adapt the push/PR path and tell the user.
- **Backend unavailable** — still draft the text, state the blocker, stop before the blocked action.

## References

- Read [references/workflow.md](references/workflow.md) for approval scope, auto-mode details, convention-detection heuristics, and edge cases.
- Read [references/examples.md](references/examples.md) for trigger examples, convention-detection examples, and good/bad commit and PR samples.
