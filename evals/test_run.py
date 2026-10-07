"""Check that the evaluation grader rejects misleading success states."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from run import (assess_case, codex_metadata, codex_skill_overrides, execute, git, git_env, grade_case,
                 prepare_case, run_grade, toml_inline, unchanged_state, write_json)
import tomllib


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

    def test_preview_rejects_early_publication(self):
        directory, expected = self.prepare()
        self.assertTrue(all(unchanged_state(directory, expected).values()))
        self.publish(directory, expected)
        self.assertFalse(unchanged_state(directory, expected)["remote_refs_preserved"])

    def test_no_push_rejects_pr_created_from_old_head(self):
        directory, expected = self.prepare("pr-publish")
        write_json(directory / "pr.json", {"head": expected["branch"]})
        self.assertFalse(unchanged_state(directory, expected)["no_pr_created"])

    def test_simulator_reports_unpublished_head_without_creating_pr(self):
        directory, expected = self.prepare("pr-publish")
        git(directory / "repo", "push", "origin", "--delete", expected["branch"], env=git_env(directory))
        (directory / "body.md").write_text("summary\n")
        result = subprocess.run(
            [sys.executable, str(directory / "hosting.py"), "create", "--base", "main",
             "--head", expected["branch"], "--title", "add feature", "--body-file", str(directory / "body.md")],
            capture_output=True, text=True, env=git_env(directory))
        self.assertEqual(result.returncode, 2)
        self.assertIn("publish it first", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((directory / "pr.json").exists())


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skill-execution-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = SimpleNamespace(client="codex", model="gpt-6-astra", effort="low", timeout=10,
                                    skill_overrides=[], mode="writing")

    def test_metadata_uses_latest_turn_of_only_the_requested_session(self):
        day = self.root / "2026/09/06"
        day.mkdir(parents=True)
        (day / "rollout-unrelated.jsonl").write_text("invalid unrelated data")
        records = [{"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": effort}}
                   for effort in ("high", "low")]
        (day / "rollout-session-1.jsonl").write_text("\n".join(json.dumps(r) for r in records))
        result = codex_metadata([{"type": "thread.started", "thread_id": "session-1"}], self.root)
        self.assertEqual(result["model_observed"], "gpt-6-astra")
        self.assertEqual(result["effort_observed"], "low")
        self.assertIsNone(result["metadata_error"])

    def test_installed_skill_is_disabled_without_losing_existing_overrides(self):
        home, codex_home = self.root / "home", self.root / "codex"
        skill = home / ".agents/skills/write-like-me/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("A synthetic installed skill")
        codex_home.mkdir()
        (codex_home / "config.toml").write_text(
            '[[skills.config]]\npath = "/another/skill/SKILL.md"\nenabled = false\n')
        entries, disabled = codex_skill_overrides(home, codex_home)
        parsed = tomllib.loads("entries = " + toml_inline(entries))["entries"]
        self.assertIn({"path": "/another/skill/SKILL.md", "enabled": False}, parsed)
        self.assertIn({"path": str(skill), "enabled": False}, parsed)
        self.assertIn(str(skill), disabled)

    def test_native_skill_attachment_is_visible_in_metadata(self):
        day = self.root / "2026/09/06"
        day.mkdir(parents=True)
        record = {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": "<skill>\n<name>write-like-me</name>\n<path>/old/SKILL.md</path>\nbody"}]}}
        (day / "rollout-session-1.jsonl").write_text(json.dumps(record))
        result = codex_metadata([{"type": "thread.started", "thread_id": "session-1"}], self.root)
        self.assertEqual(result["loaded_skill_paths"], ["/old/SKILL.md"])

    def test_missing_metadata_is_unknown_not_the_requested_model(self):
        result = codex_metadata([{"type": "thread.started", "thread_id": "missing"}], self.root)
        self.assertIsNone(result["model_observed"])
        self.assertIsNone(result["effort_observed"])

    def test_successful_exit_without_response_is_execution_failure(self):
        (self.root / "stdout.txt").write_text('{"type":"turn.completed"}\n')
        with patch("run.capture", return_value={"returncode": 0, "seconds": 0}):
            outcome = execute(self.args, self.root, "Synthetic request", read_only=True)
        self.assertIn("error", outcome)
        self.assertIn("error", json.loads((self.root / "execution.json").read_text()))

    def test_observed_model_mismatch_does_not_pass_as_requested_model(self):
        (self.root / "stdout.txt").write_text('{"type":"turn.completed"}\n')
        (self.root / "final.txt").write_text("A completed response")
        with patch("run.capture", return_value={"returncode": 0, "seconds": 0}), patch(
            "run.codex_metadata", return_value={"model_observed": "different-model", "effort_observed": "low", "loaded_skill_paths": []}
        ):
            outcome = execute(self.args, self.root, "Synthetic request", read_only=True)
        self.assertIn("error", outcome)

    def test_installed_skill_contamination_fails_the_comparison(self):
        (self.root / "stdout.txt").write_text('{"type":"turn.completed"}\n')
        (self.root / "final.txt").write_text("A plausible response")
        with patch("run.capture", return_value={"returncode": 0, "seconds": 0}), patch(
            "run.codex_metadata", return_value={"model_observed": "gpt-6-astra", "effort_observed": "low",
                                               "loaded_skill_paths": ["/old/write-like-me/SKILL.md"]}
        ):
            outcome = execute(self.args, self.root, "Synthetic request", read_only=True)
        self.assertIn("error", outcome)


if __name__ == "__main__":
    unittest.main()
