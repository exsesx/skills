# Oleh Vanin Skills

My personal collection of agent skills, installable through the
[`skills`](https://agentskills.io) CLI. The skills use the portable Agent
Skills format and are designed for both Codex and Claude Code.

## Skills

- **git-fatality** — Finalize Git work through an exact combination of branch
  creation, scoped commits, pushes, and pull requests. Routine commit and push
  commands execute after inspection without a redundant approval round or
  formal task list; preview-first requests still pause before mutation.
  Creating a PR includes pushing its inspected, already committed scope when
  needed. It never implies committing uncommitted changes, and an explicit
  "do not push" restriction takes precedence.

  ```bash
  npx skills@latest add exsesx/skills --skill git-fatality
  ```

- **write-like-me** — Draft or rewrite text in a natural personal voice using
  casual, polished, business, or formal registers. It activates only through
  explicit `$write-like-me` or `/write-like-me` invocation.

  ```bash
  npx skills@latest add exsesx/skills --skill write-like-me
  ```

`git-fatality` can activate implicitly for commit, push, PR, and explicit Git
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
├── evals/
│   ├── run.py
│   ├── hosting.py
│   └── test_run.py
├── git-fatality/
│   ├── SKILL.md
│   ├── agents/
│   ├── evals/
│   └── references/
├── write-like-me/
│   ├── SKILL.md
│   ├── agents/
│   ├── evals/
│   └── references/
└── LICENSE
```

## Evaluate changes

The small evaluation runner uses Python 3's standard library and installed
agent CLIs. Runs are opt-in and require a new output directory. Model calls
use your existing account and can incur usage. Nothing is installed.

Check the grader without making model calls:

```bash
python3 -m unittest discover -s evals
```

Run the four Git cases through Codex:

```bash
python3 evals/run.py git --output .eval-results/git-1
```

Cases cover publishing a new branch without new commits, pushing with dirty
files, committing only the index, and creating a PR from unpublished commits.
They use disposable repositories with empty global Git configuration and a
local bare remote. PR operations use a local simulator, not GitHub. Codex keeps
its sandbox and automatic approval review. A permission or authentication
failure is an execution blocker, not evidence that the skill made a bad choice.
Inspect the captured output alongside `results.json`; state checks cannot prove
that every inspection step happened or that a PR description is accurate.

To use another agent, prepare fixtures and give it one generated `prompt.txt`
at a time. Each fixture includes a copy of the skill under test:

```bash
python3 evals/run.py git --prepare-only --output .eval-results/manual-1
python3 evals/run.py grade --output .eval-results/manual-1
```

Generate blind writing comparisons through Claude:

```bash
python3 evals/run.py writing --output .eval-results/writing-1
```

This makes eight independent calls, one with and one without the writing
instructions for each register. Use `--case business` for a two-call smoke
check. Claude runs in safe mode with tools disabled. Read `review.md`, choose
A, B, tie, or neither, then open `answer-key.json`. Judge factual fidelity,
voice, and unnecessary changes; no automatic preference score is claimed.

The writing comparison tests supplied instructions, not native skill discovery.
The existing `evals.json`, `trigger_queries.json`, and conversation scenarios
remain broader review specifications. Trigger and conversation checks require
native client traces; prose-only classification does not validate activation.

The [recorded verification](evals/results/2026-09-04.json) includes the tested
source hashes, Git state checks, writing outputs, and limits of the evidence.

## License

[MIT](./LICENSE)
