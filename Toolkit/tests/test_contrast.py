"""Offline contract tests: no downloads, torch or local models required."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from Toolkit.modules.contrast import ContrastError, estimate, steer_vector
from Toolkit.modules.receipts import canonical_json, json_record, load_jsonl, write_new


def example(identifier="a"):
    return {"pair_id": identifier, "split": "train",
            "positive": {"0": [2.0, 3.0], "1": [0.0, 4.0]},
            "negative": {"0": [1.0, 3.0], "1": [0.0, 2.0]}}


class Contrasts(unittest.TestCase):
    def test_direction_and_strength(self):
        value = estimate([example()])
        self.assertEqual(value["pair_count"], 1)
        self.assertEqual(value["layers"]["0"]["direction"], [1.0, 0.0])
        self.assertEqual(value["layers"]["1"]["direction"], [0.0, 1.0])
        self.assertEqual(steer_vector([0, 5], [1, 0], 2), [2, 5])
        self.assertEqual(steer_vector([0, 5], [1, 0], 0), [0, 5])

    def test_independent_of_pair_order(self):
        a = example("a")
        b = example("b")
        b["positive"]["0"][0] = 5
        self.assertEqual(estimate([a, b]), estimate([b, a]))

    def test_no_holdout_leakage(self):
        row = example()
        row["split"] = "test"
        with self.assertRaisesRegex(ContrastError, "training split"):
            estimate([row])

    def test_duplicate_ids_rejected(self):
        with self.assertRaisesRegex(ContrastError, "duplicate"):
            estimate([example(), example()])

    def test_shape_and_non_finite_rejected(self):
        for replacement in ([1.0], [float("nan"), 1.0], [True, 1.0]):
            row = example()
            row["negative"]["0"] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(ContrastError):
                estimate([row])

    def test_zero_direction_rejected(self):
        row = example()
        row["positive"] = copy.deepcopy(row["negative"])
        with self.assertRaisesRegex(ContrastError, "zero"):
            estimate([row])

    def test_non_finite_strength_rejected(self):
        with self.assertRaises(ContrastError):
            steer_vector([1], [1], float("inf"))

    def test_strict_json_and_no_overwrite(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            json_record('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, "non-finite"):
            json_record('{"a":NaN}')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipt.jsonl"
            payload = canonical_json(example())
            write_new(path, payload)
            self.assertEqual(load_jsonl(path), [example()])
            with self.assertRaises(FileExistsError):
                write_new(path, b"overwrite")
            self.assertEqual(path.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
