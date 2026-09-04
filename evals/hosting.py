#!/usr/bin/env python3
"""Local PR simulator for the pr-publish evaluation. Makes no network requests."""

import argparse
import json
from pathlib import Path
import subprocess


def main():
    root = Path(__file__).resolve().parent
    state = root / "pr.json"
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("info", "prs", "labels", "view"):
        commands.add_parser(name)
    create = commands.add_parser("create")
    for name in ("base", "head", "title", "body-file"):
        create.add_argument("--" + name, required=True)
    create.add_argument("--draft", action="store_true")
    create.add_argument("--assignee", action="append", default=[])
    create.add_argument("--label", action="append", default=[])
    args = parser.parse_args()
    if args.command == "info":
        result = {"repository": "fixture/project", "default_branch": "main", "templates": []}
    elif args.command == "labels":
        result = [{"name": "enhancement", "description": "New capability"}]
    elif args.command == "prs":
        result = [json.loads(state.read_text())] if state.exists() else []
    elif args.command == "view":
        if not state.exists():
            parser.error("No PR exists")
        result = json.loads(state.read_text())
    else:
        if state.exists():
            parser.error("A PR already exists")
        head_sha = subprocess.check_output(
            ["git", "--git-dir", str(root / "remote.git"), "rev-parse", "--verify", "refs/heads/" + args.head],
            text=True,
        ).strip()
        result = {"url": "https://example.invalid/fixture/project/pull/1", "base": args.base,
                  "head_repository": "fixture/project", "head": args.head, "head_sha": head_sha,
                  "title": args.title, "body": Path(args.body_file).read_text(), "draft": args.draft,
                  "assignees": args.assignee, "labels": args.label}
        state.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
