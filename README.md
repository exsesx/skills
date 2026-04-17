# Agent Skills

My personal collection of agent skills, installable via the [`skills`](https://agentskills.io) CLI. Works with Claude Code, Codex, and other agents that follow the Agent Skills standard.

## Skills

- **finish-branch** — Wrap up branch work safely. Drafts commit messages, commits, pushes, and PRs with explicit approval gates before any irreversible action.

  ```bash
  npx skills@latest add exsesx/skills/finish-branch
  ```

## Install

```bash
npx skills@latest add exsesx/skills/<skill-name>
```

The CLI detects your installed agents and prompts you for where to install (global vs. project-scoped, which agents to target).

### Install from a local path

```bash
npx skills@latest add /path/to/skills/<skill-name>
```

### Manage

```bash
npx skills list
npx skills update <skill-name>
npx skills remove <skill-name>
```

## Layout

Each skill lives in its own top-level directory and is independently installable:

```text
.
├── finish-branch/
│   ├── SKILL.md
│   ├── agents/
│   └── references/
└── LICENSE
```

## License

[MIT](./LICENSE)
