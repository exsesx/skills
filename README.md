# Oleh Vanin Skills

My personal collection of agent skills, installable via the [`skills`](https://agentskills.io) CLI. Works with Claude Code, Codex, and other agents that follow the Agent Skills standard.

## Skills

- **git-fatality** — Finalize Git branch work safely. Drafts commit messages, commits, pushes, and PRs with explicit approval gates before any irreversible action.

  ```bash
  npx skills@latest add exsesx/skills --skill git-fatality
  ```

## Install

```bash
npx skills@latest add exsesx/skills
```

The CLI detects your installed agents and prompts you for where to install (global vs. project-scoped, which agents to target).

To install one skill non-interactively:

```bash
npx skills@latest add exsesx/skills --skill git-fatality
```

### Install from a local path

```bash
npx skills@latest add /path/to/skills --skill git-fatality
```

### Manage

```bash
npx skills list
npx skills update <skill-name>
npx skills remove <skill-name>
```

## Layout

Each skill lives in its own top-level directory and is listed in the plugin manifest:

```text
.
├── .claude-plugin/
│   └── plugin.json
├── git-fatality/
│   ├── SKILL.md
│   ├── agents/
│   └── references/
└── LICENSE
```

## License

[MIT](./LICENSE)
