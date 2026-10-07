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
  Scoped authorization carries across turns while the action, scope, and
  destination still match. Local commits do not require remote lookups.

  ```bash
  npx skills@latest add exsesx/skills --skill git-fatality
  ```

- **write-like-me** — Draft or rewrite text in a natural personal voice using
  casual, polished, business, or formal registers. It activates only through
  explicit `$write-like-me` or `/write-like-me` invocation.
  Explicit requests override style and workflow defaults, including output
  format, explanations, and compatible companion skills.

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

`write-like-me` is explicit-only in both clients: `disable-model-invocation`
in its frontmatter covers Claude Code, and `agents/openai.yaml` covers Codex.
Claude Code accepts that frontmatter field, but claude.ai skill uploads and the
Skills API accept only the Agent Skills spec fields and reject the package. To
upload it there, remove the field first; it will then be model-invocable.

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
│   ├── test_run.py
│   └── test_skills.py
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

The small evaluation runner uses Python 3.11+'s standard library and installed
agent CLIs. Runs are opt-in and require a new output directory. Model calls
use your existing account and can incur usage. Nothing is installed.

Check the grader and the skill package format without making model calls:

```bash
python3 -m unittest discover -s evals
```

The format checks cover the Agent Skills frontmatter limits, matching
explicit-only policy between Claude Code and Codex metadata, resolvable
one-level references, the plugin manifest, and unique eval IDs.

Run the four Git cases through Codex with an explicit model and reasoning effort:

```bash
python3 evals/run.py git --model gpt-6-astra --effort low --output .eval-results/git-1
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

Generate blind writing comparisons through Codex:

```bash
python3 evals/run.py writing --model gpt-6-astra --effort low --output .eval-results/writing-1
```

This makes eight independent calls, one with and one without the writing
instructions for each register. Use `--case business` for a two-call smoke
check. Both arms use the same client, model, effort, and tool restrictions.
Codex runs read-only and both prompts request no tools. To use Claude, add
`--client claude` and supply a Claude model ID; it runs in safe mode with tools
disabled. Read `review.md`, choose A, B, tie, or neither, then open
`answer-key.json`. Judge factual fidelity, voice, and unnecessary changes;
no automatic preference score is claimed.

This comparison supplies only the main writing instructions. It does not inject
optional examples or test native discovery. Use the native checks for those:

```bash
python3 evals/run.py native --model gpt-6-astra --effort low --output .eval-results/native-1
```

Native mode copies both packages into a disposable workspace's `.agents/skills`
and resumes actual Codex sessions for multi-turn cases. The conversation files
cover prior Git authorization, an explicit push restriction, writing overrides,
an explicitly invoked synthetic companion skill, optional example loading,
non-invocation, and profile carryover. `--case write-like-me-C03` runs only the
override case; `native --help` lists all choices. Git cases use the same local
repositories and hosting simulator as the forward checks.

Read `review.md` and each turn's `stdout.txt` to grade behavior, including which
exact skill paths were loaded and whether unnecessary tools or pauses occurred.
Existing machine instructions and other installed skills remain available, so
these are integration checks. Temporary CLI overrides disable installed copies
of the two target skills while preserving existing skill overrides. Installed
files and configuration are not edited. Native attachments from outside the
evaluation workspace cause an execution failure. Exit status zero establishes
successful execution and any automated Git state checks; behavior stays
`pending` until reviewed. The larger
`evals.json` and `trigger_queries.json` files remain additional review
specifications, not claims of executed coverage.

All model calls require `--model` and `--effort`. Each run records the CLI
version, requested settings, and source hashes in `run.json`; each execution
records elapsed time, usage, native skill attachment paths, and available
observed model settings in `execution.json`. Missing observed settings remain
unknown. Codex sessions are retained locally for resuming conversations and
reading execution metadata;
Claude returns model usage but does not expose an observed effort here. No
statistical reliability or latency improvement is inferred from these small runs.

The [Astra verification](evals/results/2026-09-06.json) records the tested source
hashes, four Git runs, eight native scenarios, a paired writing comparison,
and evidence limits. The [earlier verification](evals/results/2026-09-04.json)
retains the original results and human voice calibration.
The second-pass instruction changes follow the
[Astra guidance on precedence, follow-through, and proportionate verification](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra).

## License

[MIT](./LICENSE)
