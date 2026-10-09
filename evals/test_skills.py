"""Static checks that each skill package follows the Agent Skills format. Makes no model calls."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted(p.parent for p in ROOT.glob("*/SKILL.md"))
# Agent Skills spec fields plus the Claude Code field these skills rely on.
KNOWN_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools",
                "disable-model-invocation"}


def frontmatter(path):
    """Parse the flat frontmatter used here: plain scalars and folded (>-) blocks."""
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(str(path) + " must start with a --- frontmatter line")
    block, _, body = text[4:].partition("\n---\n")
    fields, key = {}, None
    for line in block.splitlines():
        if line[:1].isspace() and key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
        else:
            key, _, value = line.partition(":")
            value = value.strip()
            fields[key] = "" if value in (">", ">-", "|", "|-") else value.strip("\"'")
    return fields, body


class SkillPackageTests(unittest.TestCase):
    def test_skills_found(self):
        self.assertEqual([p.name for p in SKILLS], ["git-fatality", "rex", "write-like-me"])

    def test_frontmatter_follows_spec(self):
        for skill in SKILLS:
            with self.subTest(skill=skill.name):
                fields, body = frontmatter(skill / "SKILL.md")
                self.assertLessEqual(set(fields), KNOWN_FIELDS)
                self.assertEqual(fields["name"], skill.name)
                self.assertRegex(fields["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
                self.assertLessEqual(len(fields["name"]), 64)
                self.assertNotRegex(fields["name"], r"anthropic|claude")
                self.assertTrue(0 < len(fields["description"]) <= 1024)
                self.assertNotRegex(fields["description"], r"<[^>]+>")
                self.assertLess(len(body.splitlines()), 500)

    def test_invocation_policy_matches_across_clients(self):
        for skill in SKILLS:
            with self.subTest(skill=skill.name):
                fields, _ = frontmatter(skill / "SKILL.md")
                claude_explicit_only = fields.get("disable-model-invocation") == "true"
                policy = (skill / "agents/openai.yaml").read_text()
                match = re.search(r"^\s*allow_implicit_invocation:\s*(true|false)\s*$", policy, re.M)
                codex_explicit_only = bool(match) and match[1] == "false"
                self.assertEqual(claude_explicit_only, codex_explicit_only)

    def test_relative_links_resolve(self):
        for path in ROOT.glob("*/**/*.md"):
            for target in re.findall(r"\]\(([^)#\s]+)", path.read_text()):
                if not re.match(r"[a-z]+:", target):
                    with self.subTest(path=str(path.relative_to(ROOT)), target=target):
                        self.assertTrue((path.parent / target).exists())

    def test_references_are_one_level_deep(self):
        for skill in SKILLS:
            for path in skill.glob("references/*.md"):
                with self.subTest(path=str(path.relative_to(ROOT))):
                    self.assertNotRegex(path.read_text(), r"\]\((?![a-z]+:)[^)]*\.md")

    def test_plugin_manifest_lists_every_skill(self):
        manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(sorted(manifest["skills"]), ["./" + p.name for p in SKILLS])

    def test_eval_ids_are_unique(self):
        for path in ROOT.glob("*/evals/*.json"):
            data = json.loads(path.read_text())
            cases = data["evals"] if isinstance(data, dict) else data
            ids = [case["id"] for case in cases]
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
