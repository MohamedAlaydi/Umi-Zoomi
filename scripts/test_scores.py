"""Regression checks for score provenance and portable published evidence."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scores


class ScoreEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "runs" / "001-test"
        self.module = self.run / "out" / "boltz2"
        self.module.mkdir(parents=True)
        self.config = self.module / "config.json"
        self.config.write_text(json.dumps({"weights": "test.ckpt", "seeds": [42]}))
        self.score = self.module / "query" / "seed_42" / "query_seed_42_sample_1_scores.json"
        self.score.parent.mkdir(parents=True)
        self.score.write_text(json.dumps({k: 0.8 for k in scores.STRUCTURE_KEYS}))
        self.result = self.module / "result.json"

    def result_appears(self):
        self.result.write_text(json.dumps({
            "provenance": {"module": {"name": "boltz", "version": "1"},
                           "resolved_config": {"weights": "test.ckpt", "seeds": [42]}}
        }))

    def environment(self):
        return patch.multiple(scores, REPO=self.root, RUNS_DIR=self.root / "runs")

    def test_config_provenance_stays_valid_when_result_appears(self):
        with self.environment():
            iso = scores.Isolation(self.run)
            before, _ = scores.load_provenance(iso, self.module, self.config)
            self.result_appears()
            after, _ = scores.load_provenance(iso, self.module, self.config)
            default, _ = scores.load_provenance(iso, self.module)
            self.assertEqual(before.model_cell, after.model_cell)
            self.assertNotEqual(after.model_cell, default.model_cell)

    def test_score_table_survives_missing_vm_output_and_detects_tampering(self):
        self.result_appears()
        table = self.root / "notes" / "SCORES.md"
        with self.environment(), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(scores.generate(table), 0)
            self.assertEqual(scores.check(table), 0)
            shutil.rmtree(self.run / "out")
            self.assertEqual(scores.check(table), 0)
            self.assertEqual(scores.generate(table), 0)
            self.assertEqual(scores.check(table), 0)
            archived = next((self.run / "score-evidence").rglob("*_scores.json"))
            doc = json.loads(archived.read_text())
            doc["interface_predicted_tm_score"] = 0.1
            archived.write_text(json.dumps(doc))
            self.assertEqual(scores.check(table), 1)

    def test_source_cannot_escape_its_run_via_symlink(self):
        outside = self.root / "other.json"
        outside.write_text("{}")
        link = self.run / "scores.json"
        link.symlink_to(outside)
        with self.assertRaises(AssertionError):
            scores.Isolation(self.run).read_json(link)

    def test_changed_machine_readable_export_is_detected(self):
        self.result_appears()
        table = self.root / "notes" / "SCORES.md"
        with self.environment(), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            scores.generate(table)
            self.assertEqual(scores.check(table), 0)
            table.with_suffix(".csv").write_text("wrong export\n")
            self.assertEqual(scores.check(table), 1)


if __name__ == "__main__":
    unittest.main()
