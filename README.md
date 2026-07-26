# Oleh Vanin Skills

My personal collection of agent skills, installable through the
[`skills`](https://agentskills.io) CLI. The skills use the portable Agent
Skills format and are designed for both Codex and Claude Code.

## Skills

- **git-fatality** — Finalize Git work through an exact combination of branch
  creation, scoped commits, pushes, and pull requests. Routine commit and push
  commands execute after inspection without a redundant approval round or
  formal task list; preview-first requests still pause before mutation.

  ```bash
  npx skills@latest add exsesx/skills --skill git-fatality
  ```

The skill can activate implicitly for commit, push, PR, and explicit Git
finalization requests. Pull, merge, rebase, conflict-resolution, and branch
management tasks do not activate it implicitly unless the same request also
contains a covered finalization action.

Personal commit, pull request, and branch conventions are the default and do
not require a history scan. Add `conventions: repo` or say `match repo style`
to use bounded repository evidence instead; unclear evidence falls back to the
personal conventions. These are plain-language prompt selectors, not a
configuration-file syntax.

Explicit invocation is always supported:

```text
# Codex
$git-fatality commit and push to this branch

# Claude Code
/git-fatality create a new branch, commit and push, then create a PR

# Either client, using repository conventions for this task
$git-fatality conventions: repo; commit and push
```

## Install

```bash
npx skills@latest add exsesx/skills
```

The CLI detects installed agents and prompts for global or project-scoped
installation and target clients.

Install one skill non-interactively:

```bash
npx skills@latest add exsesx/skills --skill git-fatality
```

Install from a local path:

```bash
npx skills@latest add /path/to/skills --skill git-fatality
```

Manage installed skills:

```bash
npx skills list
npx skills update <skill-name>
npx skills remove <skill-name>
```

## Layout

```text
.
├── .claude-plugin/
│   └── plugin.json
├── git-fatality/
│   ├── SKILL.md
│   ├── agents/
│   ├── evals/
│   └── references/
└── LICENSE
```

## License

[MIT](./LICENSE)
