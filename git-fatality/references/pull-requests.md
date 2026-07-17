# Pull Request Workflow

Read this reference only when drafting, creating, or updating a pull request.

## Interpret PR intent

- "Write" or "draft PR text" means title and body only.
- "Create" or "open a PR" means a ready PR unless the user says draft.
- "Create/open a draft PR" means use the hosting platform's draft state.
- Never interpret the word "draft" in "draft the PR text" as authorization to
  create a remote draft PR.

## Inspect the branch and base

Choose the base in this order:

1. the user's explicit base
2. the current branch's configured GitHub merge base
3. the repository's default branch from GitHub
4. the remote `HEAD` symbolic ref when GitHub is unavailable

Inspect the complete `base...HEAD` diff and commit range. Do not summarize only
the latest commit on a multi-commit branch.

Before creating anything, check for an open PR with the same head branch. If
one exists, do not create a duplicate or overwrite it under creation-only
authorization. Report the existing PR and compare it with the prepared result.
Update it only when the user explicitly requested an update, or after they
approve the proposed changes to the existing PR.

## Find repository templates

Read templates from the repository's default branch, where GitHub sources them.
Check case-insensitively for supported `.md` or `.txt` files in:

- the repository root
- `docs/`
- `.github/`
- `PULL_REQUEST_TEMPLATE/` below any of those locations

For multiple templates, use the user's choice or the template matching the work
type. Use the chosen template verbatim as the skeleton: fill its sections,
preserve required sections, and do not invent new ones unless requested.

If no template exists, inspect recent merged PRs for a consistent structure.
Otherwise use the fallback in `references/examples.md`.

## Assignee and labels

Self-assign by default with `@me`. A named assignee replaces that default; an
explicit opt-out leaves the PR unassigned.

Fetch existing labels with enough result capacity to avoid the CLI's small
default page, for example:

```bash
gh label list --limit 200 --json name,description
```

Apply only labels that already exist and clearly match the work. Prefer the
repository's actual equivalents of feature, bug, documentation, maintenance,
or dependency work. Never create labels. An explicit label list overrides
inference; an explicit opt-out applies only to labels.

Whenever possible, pass assignees and labels directly to `gh pr create` with
`--assignee` and `--label`. Use `gh pr edit` for an existing PR or as a fallback
when creation succeeded but metadata application did not.

## Create safely

Use explicit `--base`, `--head`, `--title`, and `--body-file` arguments. Prefer
`--body-file` over shell-interpolated multiline text. Add `--draft` only for a
remote draft PR request.

After creation or update, verify with authoritative state, including:

```bash
gh pr view --json number,url,state,isDraft,baseRefName,headRefName,title,body,assignees,labels
```

Report the URL, ready or draft state, base and head branches, assignee, and
labels actually present. If metadata application fails after creation, report
the PR as created and the metadata step as incomplete rather than retrying PR
creation.
