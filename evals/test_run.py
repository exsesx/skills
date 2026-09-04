"""Check that the evaluation grader rejects misleading success states."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from run import assess_case, git, git_env, grade_case, prepare_case, run_grade, write_json


class GradingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skill-grader-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def prepare(self, name="publish"):
        directory = self.root / name
        return directory, prepare_case(directory, name)

    def publish(self, directory, expected):
        git(directory / "repo", "push", "--set-upstream", "origin", expected["branch"], env=git_env(directory))

    def test_missing_branch_is_not_complete(self):
        directory, expected = self.prepare()
        checks = grade_case(directory, expected)
        self.assertFalse(checks["exact_head_published"])
        self.assertFalse(checks["upstream_correct"])

    def test_correct_publication_passes(self):
        directory, expected = self.prepare()
        self.publish(directory, expected)
        self.assertTrue(assess_case(directory, expected)["state_checks_passed"])

    def test_repointed_origin_fails(self):
        directory, expected = self.prepare()
        self.publish(directory, expected)
        other = directory / "other.git"
        git(directory, "clone", "--bare", str(directory / "remote.git"), str(other), env=git_env(directory))
        git(directory / "repo", "remote", "set-url", "origin", str(other), env=git_env(directory))
        checks = grade_case(directory, expected)
        self.assertTrue(checks["exact_head_published"])
        self.assertFalse(checks["remote_destination_preserved"])

    def test_unrelated_remote_deletion_fails(self):
        directory, expected = self.prepare()
        self.publish(directory, expected)
        git(directory / "remote.git", "update-ref", "-d", "refs/heads/main", env=git_env(directory))
        self.assertFalse(grade_case(directory, expected)["other_remote_refs_preserved"])

    def test_pr_from_wrong_branch_fails_even_at_correct_commit(self):
        directory, expected = self.prepare("pr-publish")
        self.publish(directory, expected)
        write_json(directory / "pr.json", {
            "head_sha": expected["head"], "head": "feature/wrong", "head_repository": "fixture/project",
            "base": "main", "draft": False, "title": "add feature", "body": "add fixture feature",
            "assignees": ["@me"], "labels": ["enhancement"],
        })
        checks = grade_case(directory, expected)
        self.assertTrue(checks["pr_head_matches"])
        self.assertFalse(checks["pr_head_branch_correct"])

    def test_invalid_pr_state_is_reported(self):
        directory, expected = self.prepare("pr-publish")
        (directory / "pr.json").write_text("{")
        result = assess_case(directory, expected)
        self.assertFalse(result["state_checks_passed"])
        self.assertIn("grading_error", result)

    def test_invalid_manifest_does_not_hide_later_results(self):
        directory, expected = self.prepare()
        self.publish(directory, expected)
        (self.root / "broken-expected.json").write_text("{")
        write_json(self.root / "publish-expected.json", expected)
        with redirect_stdout(io.StringIO()):
            status = run_grade(SimpleNamespace(output=self.root))
        results = json.loads((self.root / "results.json").read_text())
        self.assertEqual(status, 1)
        self.assertEqual(len(results), 2)
        self.assertIn("grading_error", results[0])
        self.assertTrue(results[1]["state_checks_passed"])


if __name__ == "__main__":
    unittest.main()
