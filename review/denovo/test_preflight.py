"""Regression checks for candidate/receipt mix-ups at the sequence handoff."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from preflight import assess, pair_hash

HERE = Path(__file__).resolve().parent
SPR = HERE.parents[1] / "data/her2-trastuzumab/trastuzumab_her2_spr_all_768.csv"


class PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with SPR.open(newline="") as handle:
            cls.parent = next(r for r in csv.DictReader(handle) if r["cdrh3"] == "WGGDGFYAMD")

    def row(self):
        return dict(query="reference", format="Fab", heavy_variable=self.parent["vh_sequence"],
                    light_variable=self.parent["vl_sequence"])

    def test_imported_claim_cannot_assign_track_or_official_acceptance(self):
        row = {**self.row(), "assigned_track": "de_novo", "official_eligibility": "ACCEPTED"}
        result = assess(row, self.parent)
        self.assertEqual(result["local_status"], "PASS_LOCAL")
        self.assertIsNone(result["assigned_track"])
        self.assertEqual(result["official_eligibility"], "UNVERIFIED")
        self.assertEqual(result["aligned_identity_to_trastuzumab_pair_diagnostic"], 1.)
        self.assertEqual(len(result["numbering"]["heavy"]["cdr3_imgt"]), 13)
        self.assertEqual(len(row["heavy_variable"][98:108]), 10)

    def test_changed_sequence_cannot_reuse_reference_hash(self):
        row = self.row()
        row["pair_sha256"] = pair_hash(row["heavy_variable"], row["light_variable"])
        row["heavy_variable"] = "A" + row["heavy_variable"][1:]
        result = assess(row, self.parent)
        self.assertEqual(result["local_status"], "FAIL_LOCAL")
        self.assertIn("sequence_hash_mismatch", result["errors"])

    def test_vhh_label_cannot_disguise_a_generated_light_chain(self):
        # Actual hosted nanobody-protocol output, detected as lambda.
        sequence = "EVYLTQPGSGSGSVGETLTISASGSSSNVGSNYVAWYQQKPGQARKLLIYYDSNRASGVPSRFSGSKDTSKNTAYLTISSLQTEDTAVYYAASWDTSNGWQLVFGGGTKVTVS"
        result = assess(dict(query="light_as_vhh",format="VHH",heavy_variable=sequence,
                             light_variable=""),self.parent)
        self.assertEqual(result["local_status"], "FAIL_LOCAL")
        self.assertIn("heavy_detected_as_light_chain",result["errors"])

    def test_csv_duplicates_and_format_mismatch_are_not_silent(self):
        row = self.row()
        bad = {**row, "query": "missing_light", "light_variable": ""}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.csv"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerows([row, row, bad])
            output = subprocess.check_output([sys.executable, str(HERE / "preflight.py"), str(path),
                                              "--parent-spr", str(SPR)], text=True)
        results = json.loads(output)
        self.assertEqual(results["counts"], {"FAIL_LOCAL": 3})
        self.assertIn("duplicate_query", results["rows"][0]["errors"])
        self.assertIn("duplicate_sequence_pair", results["rows"][1]["errors"])
        self.assertIn("format_chain_count_mismatch", results["rows"][2]["errors"])


if __name__ == "__main__":
    unittest.main()
