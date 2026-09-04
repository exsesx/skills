#!/usr/bin/env python3
"""Opt-in skill evaluations. Uses Python's standard library and installed CLIs."""

import argparse
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
GIT_CASES = {
    "publish": "Publish this branch to origin under its current name and set its upstream. Do not commit or create a PR.",
    "push-dirty": "Push this branch to its upstream. Do not commit or create a PR.",
    "commit-staged": "Commit only the staged changes. Do not push or create a PR.",
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
        command = ["codex", "exec", "--approve-for-me", "--ephemeral", "--color", "never",
                   "--json", "--skip-git-repo-check", "-C", str(directory),
                   "-o", str(directory / "final.txt")]
        # Keep fixture Git configuration in subprocess tools as well as setup.
        for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT"):
            command.extend(["-c", "shell_environment_policy.set." + key + "=" + json.dumps(git_env(directory)[key])])
        command.append("-")
        print("Running " + name, flush=True)
        outcome = capture(command, (directory / "prompt.txt").read_text(), directory,
                          git_env(directory), args.timeout)
        write_json(directory / "execution.json", outcome)
        result = {**outcome, **assess_case(directory, expected)}
        results.append(result)
        write_json(args.output / "results.json", results)
        print(json.dumps(result), flush=True)
    return 0 if all(r["returncode"] == 0 and r["state_checks_passed"] for r in results) else 1


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
    examples = (ROOT / "write-like-me/references/examples.md").read_text()
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
                          + "\n<reference>\n" + examples + "\n</reference>\n</skill>\n\n$write-like-me " + prompt)
            command = ["claude", "--print", "--safe-mode", "--tools", "", "--permission-prompts", "none",
                       "--no-session-persistence", "--output-format", "json"]
            (directory / "prompt.txt").write_text(prompt)
            print("Generating " + directory.name, flush=True)
            outcome = capture(command, prompt, directory, {**os.environ, "NO_COLOR": "1"}, args.timeout)
            write_json(directory / "execution.json", outcome)
            if outcome["returncode"] != 0:
                raise RuntimeError("Model execution failed; inspect " + str(directory))
            response = json.loads((directory / "stdout.txt").read_text())
            if response.get("is_error") or not response.get("result"):
                raise RuntimeError("No successful writing result; inspect " + str(directory))
            samples[arm] = response["result"]
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    git_parser = commands.add_parser("git", help="Run Codex against disposable local Git cases")
    git_parser.add_argument("--case", choices=["all", *GIT_CASES], default="all")
    git_parser.add_argument("--prepare-only", action="store_true", help="Print prompts for another agent; then use grade")
    writing = commands.add_parser("writing", help="Generate blind instruction comparisons with Claude; no tools or customizations")
    writing.add_argument("--case", choices=["all", "casual", "polished", "business", "formal"], default="all")
    writing.add_argument("--seed", type=int, default=0)
    grade = commands.add_parser("grade", help="Check the state of previously prepared Git cases")
    for subparser in (git_parser, writing, grade):
        subparser.add_argument("--output", required=True, type=Path, help="Run directory; must be new except for grade")
        if subparser is not grade:
            subparser.add_argument("--timeout", type=int, default=300, help="Seconds per model call")
    args = parser.parse_args()
    args.output = args.output.resolve()
    if args.mode != "grade":
        args.output.mkdir(parents=True, exist_ok=False)
    if args.mode == "git":
        return run_git(args)
    if args.mode == "grade":
        return run_grade(args)
    return run_writing(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
