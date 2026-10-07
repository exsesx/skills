#!/usr/bin/env python3
"""Opt-in skill evaluations. Uses Python's standard library and installed CLIs."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import signal
import subprocess
import sys
import time
import tomllib


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("git-fatality", "write-like-me")
GIT_CASES = {
    "publish": "Publish this branch to origin under its current name and set its upstream. Do not commit or create a PR.",
    "push-dirty": "Push this branch to its upstream. Do not commit or create a PR.",
    "commit-staged": "Can you commit only the staged changes? Do not push or create a PR.",
    "pr-publish": "Create a ready PR for this branch against main. Use the local hosting simulator described below.",
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def git_env(directory):
    # Synthetic repositories do not inherit signing, hooks, credentials or remotes.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=str(directory / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               GIT_TERMINAL_PROMPT="0", GIT_PAGER="cat", NO_COLOR="1", TERM="dumb")
    return env


def git(directory, *args, env):
    return subprocess.check_output(
        ["git", "--no-pager", "-c", "color.ui=false", *args], cwd=directory,
        env=env, stderr=subprocess.PIPE, text=True,
    ).strip()


def files(directory):
    return {str(p.relative_to(directory)): p.read_bytes().hex()
            for p in directory.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(directory).parts}


def refs(directory, env):
    output = git(directory, "for-each-ref", "--format=%(refname) %(objectname)", env=env)
    return dict(line.split(" ", 1) for line in output.splitlines())


def prepare_case(directory, name):
    directory.mkdir()
    (directory / "gitconfig").write_text("")
    env = git_env(directory)
    repo, remote = directory / "repo", directory / "remote.git"
    git(directory, "init", "--initial-branch=main", str(repo), env=env)
    git(directory, "init", "--bare", "--initial-branch=main", str(remote), env=env)
    git(repo, "config", "user.name", "Skill Evaluation", env=env)
    git(repo, "config", "user.email", "evaluation@example.invalid", env=env)
    (repo / "draft.txt").write_text("draft=original\n")
    (repo / "notes.txt").write_text("notes=original\n")
    git(repo, "add", "draft.txt", "notes.txt", env=env)
    git(repo, "commit", "-m", "add initial fixture", env=env)
    git(repo, "remote", "add", "origin", str(remote), env=env)
    git(repo, "push", "--set-upstream", "origin", "main", env=env)
    branch = "feature/" + name
    git(repo, "switch", "-c", branch, env=env)
    if name in ("push-dirty", "pr-publish"):
        git(repo, "push", "--set-upstream", "origin", branch, env=env)
        (repo / "feature.txt").write_text("The feature is ready.\n")
        git(repo, "add", "feature.txt", env=env)
        git(repo, "commit", "-m", "add fixture feature", env=env)
    if name == "pr-publish":
        git(repo, "switch", "main", env=env)
        (repo / "base-only.txt").write_text("An unrelated change on the base branch.\n")
        git(repo, "add", "base-only.txt", env=env)
        git(repo, "commit", "-m", "advance base independently", env=env)
        git(repo, "push", "origin", "main", env=env)
        git(repo, "switch", branch, env=env)
    if name in ("push-dirty", "commit-staged"):
        (repo / "draft.txt").write_text("draft=staged\n")
        git(repo, "add", "draft.txt", env=env)
        (repo / "draft.txt").write_text("draft=unstaged\n")
    if name != "publish":
        (repo / "notes.txt").write_text("notes=unrelated work\n")
        (repo / "untracked.txt").write_text("Preserve this unrelated file.\n")
    expected = {
        "case": name, "branch": branch,
        "head": git(repo, "rev-parse", "HEAD", env=env),
        "index_tree": git(repo, "write-tree", env=env),
        "index_entries": git(repo, "ls-files", "--stage", env=env),
        "files": files(repo),
        "remote_url": str(remote), "remote_refs": refs(remote, env),
    }
    shutil.copytree(ROOT / "git-fatality", directory / "git-fatality")
    prompt = (
        f"Use $git-fatality at {directory / 'git-fatality/SKILL.md'}.\n"
        f"Work in {repo}. {GIT_CASES[name]}\n"
        "This is a disposable evaluation repository. The only remote is a local bare repository. "
        "Its synthetic identity and empty global Git configuration are intentional. "
        "Keep normal hooks and permissions. Use no external services.\n"
    )
    if name == "pr-publish":
        shutil.copyfile(ROOT / "evals/hosting.py", directory / "hosting.py")
        prompt += (f"Hosting operations use `python3 {directory / 'hosting.py'}`. "
                   "Run it with --help to discover the interface. This simulator replaces gh; "
                   "use Git normally for inspection and publishing.\n")
    (directory / "prompt.txt").write_text(prompt)
    return expected


def grade_case(directory, expected):
    repo, remote = directory / "repo", directory / "remote.git"
    env = git_env(directory)
    head = git(repo, "rev-parse", "HEAD", env=env)
    checks = {
        "branch_preserved": git(repo, "branch", "--show-current", env=env) == expected["branch"],
        "worktree_files_preserved": files(repo) == expected["files"],
        "remote_destination_preserved": (
            git(repo, "remote", "get-url", "origin", env=env) == expected["remote_url"]
            and git(repo, "remote", "get-url", "--push", "origin", env=env) == expected["remote_url"]
        ),
    }
    if expected["case"] == "commit-staged":
        checks.update(
            one_commit=git(repo, "rev-list", "--count", expected["head"] + "..HEAD", env=env) == "1",
            parent_preserved=git(repo, "rev-list", "--parents", "-n", "1", "HEAD", env=env).split()[1:] == [expected["head"]],
            committed_exact_index=git(repo, "show", "-s", "--format=%T", "HEAD", env=env) == expected["index_tree"],
            index_clean=not git(repo, "diff", "--cached", "--name-only", env=env),
            remote_unchanged=refs(remote, env) == expected["remote_refs"],
        )
    else:
        actual_refs = refs(remote, env)
        target_ref = "refs/heads/" + expected["branch"]
        published = actual_refs.get(target_ref)
        try:
            upstream = git(repo, "rev-parse", "--abbrev-ref", "@{upstream}", env=env)
        except subprocess.CalledProcessError:
            upstream = ""
        checks.update(
            no_new_commit=head == expected["head"],
            exact_head_published=published == expected["head"],
            other_remote_refs_preserved=(
                {k: v for k, v in actual_refs.items() if k != target_ref}
                == {k: v for k, v in expected["remote_refs"].items() if k != target_ref}
            ),
            upstream_correct=upstream == "origin/" + expected["branch"],
            index_preserved=git(repo, "ls-files", "--stage", env=env) == expected["index_entries"],
        )
    if expected["case"] == "pr-publish":
        state = json.loads((directory / "pr.json").read_text()) if (directory / "pr.json").exists() else {}
        checks.update(pr_created=bool(state), pr_head_matches=state.get("head_sha") == expected["head"],
                      pr_head_branch_correct=state.get("head") == expected["branch"],
                      pr_head_repository_correct=state.get("head_repository") == "fixture/project",
                      pr_base_correct=state.get("base") == "main", pr_ready=state.get("draft") is False,
                      pr_text_present=bool(state.get("title")) and bool(state.get("body")),
                      pr_assignee_correct=state.get("assignees") == ["@me"],
                      pr_labels_correct=state.get("labels") == ["enhancement"])
    return checks


def assess_case(directory, expected):
    try:
        checks = grade_case(directory, expected)
        return {"case": expected["case"], "checks": checks, "state_checks_passed": all(checks.values())}
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        return {"case": expected["case"], "checks": {}, "state_checks_passed": False,
                "grading_error": str(error)}


def capture(command, prompt, directory, env, timeout):
    started = time.monotonic()
    with (directory / "stdout.txt").open("w") as stdout, (directory / "stderr.txt").open("w") as stderr:
        process = subprocess.Popen(command, cwd=directory, env=env, stdin=subprocess.PIPE,
                                   stdout=stdout, stderr=stderr, text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
            outcome = {"returncode": process.returncode}
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            outcome = {"returncode": None, "error": "timeout"}
    return {**outcome, "seconds": round(time.monotonic() - started, 2)}


def record_run(args):
    paths = [p for folder in ("git-fatality", "write-like-me", "evals")
             for p in (ROOT / folder).rglob("*")
             if p.is_file() and p.suffix in (".md", ".yaml", ".json", ".py")
             and "results" not in p.relative_to(ROOT).parts]
    version = subprocess.check_output([args.client, "--version"], text=True).strip()
    write_json(args.output / "run.json", {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "client": args.client, "client_version": version,
        "model_requested": args.model, "effort_requested": args.effort,
        "mode": args.mode,
        "disabled_skill_paths": args.disabled_skill_paths,
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(paths)},
        "configuration": "Model and effort are explicit. Codex disables installed copies of the target skills "
                         "for this invocation, retaining other skill overrides and normal permissions. "
                         "Claude writing comparisons disable customizations. Native checks use workspace skills.",
    })


def codex_skill_overrides(home, codex_home):
    config_path = codex_home / "config.toml"
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    entries = config.get("skills", {}).get("config", [])
    profile = config.get("profile")
    if profile:
        entries = config.get("profiles", {}).get(profile, {}).get("skills", {}).get("config", entries)
        layer = codex_home / (profile + ".config.toml")
        if layer.exists():
            entries = tomllib.loads(layer.read_text()).get("skills", {}).get("config", entries)
    paths = set()
    for root in (home / ".agents/skills", codex_home / "skills", Path("/etc/codex/skills")):
        for name in SKILLS:
            path = root / name / "SKILL.md"
            if path.exists():
                paths.update((str(path), str(path.resolve())))
    entries = [entry for entry in entries if entry.get("path") not in paths]
    return entries + [{"path": path, "enabled": False} for path in sorted(paths)], sorted(paths)


def toml_inline(value):
    if isinstance(value, dict):
        return "{" + ", ".join(json.dumps(key) + " = " + toml_inline(item) for key, item in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(toml_inline(item) for item in value) + "]"
    return json.dumps(value)


def codex_metadata(events, sessions_root=None):
    session = next((e["thread_id"] for e in events if e.get("type") == "thread.started"), None)
    usage = next((e.get("usage") for e in reversed(events) if e.get("type") == "turn.completed"), None)
    model, effort = None, None
    loaded = set()
    metadata_error = None
    if session:
        # Read only this evaluation session, never unrelated conversation content.
        root = sessions_root or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
        try:
            for path in root.glob("*/*/*/*-" + session + ".jsonl"):
                for line in path.read_text().splitlines():
                    record = json.loads(line)
                    if record.get("type") == "turn_context":
                        context = record["payload"]
                        model, effort = context.get("model"), context.get("effort")
                    elif record.get("type") == "response_item":
                        payload = record.get("payload", {})
                        if payload.get("type") == "message" and payload.get("role") == "user":
                            for content in payload.get("content", []):
                                match = re.match(r"<skill>\s*<name>(.*?)</name>\s*<path>(.*?)</path>", content.get("text", ""))
                                if match and match[1] in SKILLS:
                                    loaded.add(match[2])
        except (OSError, ValueError) as error:
            metadata_error = str(error)
    return {"session_id": session, "model_observed": model, "effort_observed": effort,
            "usage": usage, "metadata_error": metadata_error, "loaded_skill_paths": sorted(loaded)}


def execute(args, directory, prompt, *, env=None, cwd=None, session=None, read_only=False):
    cwd = cwd or directory
    if args.client == "codex":
        command = ["codex", "exec", "--color", "never", "-C", str(cwd)]
        command += ["--sandbox", "read-only"] if read_only else ["--approve-for-me"]
        if session:
            command.append("resume")
        command += ["--json", "--skip-git-repo-check", "--model", args.model,
                    "-c", "model_reasoning_effort=" + json.dumps(args.effort),
                    "-o", str(directory / "final.txt")]
        command += ["-c", "skills.config=" + toml_inline(args.skill_overrides)]
        for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT"):
            if env and key in env:
                command += ["-c", "shell_environment_policy.set." + key + "=" + json.dumps(env[key])]
        if session:
            command.append(session)
        command.append("-")
    else:
        command = ["claude", "--print", "--safe-mode", "--tools", "", "--permission-prompts", "none",
                   "--no-session-persistence", "--output-format", "json",
                   "--model", args.model, "--effort", args.effort]
    (directory / "prompt.txt").write_text(prompt)
    outcome = capture(command, prompt, directory, env or {**os.environ, "NO_COLOR": "1"}, args.timeout)
    outcome.update(model_requested=args.model, effort_requested=args.effort)
    if outcome["returncode"] == 0:
        if args.client == "codex":
            events = [json.loads(line) for line in (directory / "stdout.txt").read_text().splitlines() if line.strip()]
            outcome.update(codex_metadata(events))
            for path in outcome["loaded_skill_paths"]:
                if args.mode == "writing" or not Path(path).resolve().is_relative_to(cwd.resolve()):
                    outcome["error"] = "A target skill outside the evaluation workspace was loaded: " + path
            for field in ("model", "effort"):
                observed = outcome[field + "_observed"]
                if observed is not None and observed != getattr(args, field):
                    outcome["error"] = "Observed " + field + " differs from the requested setting"
            failed = any(e.get("type") in ("error", "turn.failed") for e in events)
            final = directory / "final.txt"
            text = final.read_text() if final.exists() else ""
            if failed or not text.strip():
                outcome["error"] = "No completed response; inspect stdout.txt"
        else:
            response = json.loads((directory / "stdout.txt").read_text())
            text = response.get("result", "")
            outcome.update(model_usage=response.get("modelUsage"), usage=response.get("usage"),
                           effort_observed=None)
            if response.get("is_error") or not text:
                outcome["error"] = "No successful writing result; inspect stdout.txt"
        if not outcome.get("error"):
            (directory / "final.txt").write_text(text)
    write_json(directory / "execution.json", outcome)
    return outcome


def run_git(args):
    names = list(GIT_CASES) if args.case == "all" else [args.case]
    results = []
    for name in names:
        directory = args.output / name
        expected = prepare_case(directory, name)
        write_json(args.output / (name + "-expected.json"), expected)
        if args.prepare_only:
            print(directory / "prompt.txt", flush=True)
            continue
        print("Running " + name, flush=True)
        outcome = execute(args, directory, (directory / "prompt.txt").read_text(), env=git_env(directory))
        result = {**outcome, **assess_case(directory, expected)}
        results.append(result)
        write_json(args.output / "results.json", results)
        print(json.dumps(result), flush=True)
    return 0 if all(r["returncode"] == 0 and not r.get("error") and r["state_checks_passed"] for r in results) else 1


def run_grade(args):
    results = []
    for manifest in sorted(args.output.glob("*-expected.json")):
        try:
            expected = json.loads(manifest.read_text())
            result = assess_case(args.output / expected["case"], expected)
        except (OSError, ValueError, KeyError, TypeError) as error:
            result = {"case": manifest.name, "checks": {}, "state_checks_passed": False,
                      "grading_error": str(error)}
        results.append(result)
    if not results:
        raise ValueError("No prepared Git cases found in " + str(args.output))
    write_json(args.output / "results.json", results)
    print(json.dumps(results, indent=2))
    return 0 if all(r["state_checks_passed"] for r in results) else 1


def run_writing(args):
    cases = json.loads((ROOT / "write-like-me/evals/writing.json").read_text())
    skill = (ROOT / "write-like-me/SKILL.md").read_text()
    rng, key, review = random.Random(args.seed), {}, []
    for case in cases:
        if args.case != "all" and case["id"] != args.case:
            continue
        samples = {}
        # Randomize execution order as well as the displayed labels.
        arms = rng.sample(["baseline", "skill"], 2)
        for arm in arms:
            directory = args.output / (case["id"] + "-" + arm)
            directory.mkdir()
            prompt = case["prompt"]
            if arm == "skill":
                prompt = ("Apply this skill to the explicitly invoking request below.\n<skill>\n" + skill
                          + "\n</skill>\n\n" + prompt)
            prompt = "This is a self-contained writing comparison. Use no tools.\n\n" + prompt
            print("Generating " + directory.name, flush=True)
            outcome = execute(args, directory, prompt, read_only=True)
            if outcome["returncode"] != 0 or outcome.get("error"):
                raise RuntimeError("Model execution failed; inspect " + str(directory))
            samples[arm] = (directory / "final.txt").read_text()
        labels = rng.sample(["baseline", "skill"], 2)
        key[case["id"]] = dict(zip(["A", "B"], labels))
        review.append("## " + case["id"] + "\n\nSource request:\n\n" + case["prompt"])
        for label, arm in zip(["A", "B"], labels):
            review.append("### " + label + "\n\n" + samples[arm])
        review.append("Choice: A / B / tie / neither\n\nMeaning preserved? Voice? Unnecessary changes?")
    write_json(args.output / "answer-key.json", key)
    (args.output / "review.md").write_text("# Blind writing comparison\n\n" + "\n\n".join(review) + "\n")
    print(args.output / "review.md")
    return 0


def unchanged_state(directory, expected):
    repo, env = directory / "repo", git_env(directory)
    return {
        "head_preserved": git(repo, "rev-parse", "HEAD", env=env) == expected["head"],
        "branch_preserved": git(repo, "branch", "--show-current", env=env) == expected["branch"],
        "index_preserved": git(repo, "ls-files", "--stage", env=env) == expected["index_entries"],
        "worktree_files_preserved": files(repo) == expected["files"],
        "remote_refs_preserved": refs(directory / "remote.git", env) == expected["remote_refs"],
        "remote_destination_preserved": (
            git(repo, "remote", "get-url", "origin", env=env) == expected["remote_url"]
            and git(repo, "remote", "get-url", "--push", "origin", env=env) == expected["remote_url"]),
        "no_pr_created": not (directory / "pr.json").exists(),
    }


def native_cases():
    cases = []
    for skill in ("git-fatality", "write-like-me"):
        for case in json.loads((ROOT / skill / "evals/conversations.json").read_text()):
            cases.append({**case, "id": skill + "-" + case["id"]})
    return cases


def run_native(args):
    review, results = [], []
    for case in native_cases():
        if args.case != "all" and args.case != case["id"]:
            continue
        directory = args.output / case["id"]
        expected = prepare_case(directory, case["fixture"]) if case.get("fixture") else None
        directory.mkdir(exist_ok=True)
        skills = directory / ".agents/skills"
        for name in ("git-fatality", "write-like-me"):
            shutil.copytree(ROOT / name, skills / name)
        if case.get("companion"):
            companion = skills / "eval-concise"
            companion.mkdir()
            (companion / "SKILL.md").write_text(
                "---\nname: eval-concise\ndescription: Shorten a draft when explicitly invoked.\n---\n"
                "Keep the requested draft to at most eight words while preserving its facts and conditions.\n")
        context = "Use the workspace's .agents/skills copies when skill names overlap.\n"
        if expected:
            context += (directory / "prompt.txt").read_text().split("\n", 1)[1]
            # The conversation specifies the actions; the fixture supplies only its environment.
            context = context.replace(GIT_CASES[case["fixture"]], "")
        session = None
        review.append("## " + case["id"])
        for index, turn in enumerate(case["turns"], 1):
            output = directory / ("turn-" + str(index))
            output.mkdir()
            prompt = (context if index == 1 else "") + turn["user"]
            print("Running " + case["id"] + " turn " + str(index), flush=True)
            outcome = execute(args, output, prompt, cwd=directory, session=session,
                              env=git_env(directory) if expected else None, read_only=not expected)
            session = outcome.get("session_id")
            checks = None
            if expected:
                checks = (unchanged_state(directory, expected) if turn["state_after"] == "unchanged"
                          else grade_case(directory, expected))
            result = {"case": case["id"], "turn": index, **outcome, "state_checks": checks,
                      "behavior_review": "pending"}
            results.append(result)
            write_json(args.output / "results.json", results)
            if outcome["returncode"] != 0 or outcome.get("error") or not session:
                raise RuntimeError("Native execution failed; inspect " + str(output))
            review.append("### Turn " + str(index) + "\n\n" + turn["user"] + "\n\n"
                          + (output / "final.txt").read_text()
                          + "\n\nTrace: " + str(output / "stdout.txt"))
        review.append("\n".join("- " + assertion for assertion in case["assertions"]))
        review.append("\nBehavior: pass / fail / blocked. Record evidence from outputs and traces, including "
                      "the exact skill paths read. A successful process or Git state alone is not a behavior pass.")
        (args.output / "review.md").write_text("# Native skill review\n\n" + "\n\n".join(review) + "\n")
    return 0 if all(r["state_checks"] is None or all(r["state_checks"].values()) for r in results) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    git_parser = commands.add_parser("git", help="Run Codex against disposable local Git cases")
    git_parser.add_argument("--case", choices=["all", *GIT_CASES], default="all")
    git_parser.add_argument("--prepare-only", action="store_true", help="Print prompts for another agent; then use grade")
    writing = commands.add_parser("writing", help="Generate blind instruction comparisons with Codex or Claude")
    writing.add_argument("--client", choices=["codex", "claude"], default="codex")
    writing.add_argument("--case", choices=["all", "casual", "polished", "business", "formal"], default="all")
    writing.add_argument("--seed", type=int, default=0)
    native = commands.add_parser("native", help="Run native workspace skills through Codex, resuming real conversations")
    native.add_argument("--case", choices=["all", *[case["id"] for case in native_cases()]], default="all")
    grade = commands.add_parser("grade", help="Check the state of previously prepared Git cases")
    for subparser in (git_parser, writing, native, grade):
        subparser.add_argument("--output", required=True, type=Path, help="Run directory; must be new except for grade")
        if subparser is not grade:
            subparser.add_argument("--timeout", type=int, default=300, help="Seconds per model call")
            subparser.add_argument("--model", help="Explicit model ID; required for model calls")
            subparser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                                   help="Explicit reasoning effort; required for model calls")
            subparser.set_defaults(client="codex")
    args = parser.parse_args()
    model_calls = args.mode != "grade" and not getattr(args, "prepare_only", False)
    if model_calls and (not args.model or not args.effort):
        parser.error("Model calls require --model and --effort; no machine defaults are inferred")
    args.output = args.output.resolve()
    if args.mode != "grade":
        args.output.mkdir(parents=True, exist_ok=False)
    if model_calls:
        args.skill_overrides, args.disabled_skill_paths = (codex_skill_overrides(
            Path.home(), Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
            if args.client == "codex" else ([], []))
        record_run(args)
    if args.mode == "git":
        return run_git(args)
    if args.mode == "grade":
        return run_grade(args)
    if args.mode == "native":
        return run_native(args)
    return run_writing(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
