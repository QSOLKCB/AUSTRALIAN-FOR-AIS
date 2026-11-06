"""Regression tests for Qwen capture, large-file estimation and receipt publication."""

from contextlib import nullcontext
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from Toolkit.modules.contrast import estimate
from Toolkit.modules.qwen_capture import LocalQwenCapture
from Toolkit.modules.receipts import (MAX_CAPTURE_BYTES, MAX_CAPTURE_LINE_BYTES,
                                      MAX_CAPTURE_RECORDS, canonical_json, iter_jsonl)
from Toolkit.tools import capture, estimate as estimate_tool


STAMP = "a" * 64


class Tensor:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, key):
        assert key == (0, -1, slice(None))
        return self

    def detach(self):
        return self

    def float(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.values


class Tokens:
    shape = (1, 2)

    def to(self, device):
        return self


class Layer:
    def __init__(self):
        self.hooks = []

    def register_forward_hook(self, hook):
        self.hooks.append(hook)

        def remove():
            self.hooks.remove(hook)
        return SimpleNamespace(remove=remove)

    def forward(self, value):
        for hook in list(self.hooks):
            hook(self, (), (Tensor([value]),))


class FakeModel:
    def __init__(self, fail=False):
        self.model = SimpleNamespace(layers=[Layer(), Layer()])
        self.fail = fail

    def __call__(self, **kwargs):
        self.model.layers[0].forward(2.0)
        self.model.layers[1].forward(3.0)
        if self.fail:
            raise RuntimeError("forward failed")
        # A final, normalized hidden state would differ from the decoder output.
        return SimpleNamespace(hidden_states=[Tensor([0]), Tensor([2]), Tensor([99])])


class FakeCapture:
    def __init__(self, *args):
        self.checkpoint = {"checkpoint_manifest_sha256": STAMP, "file_sha256": {}}

    def capture(self, prompt):
        value = 2.0 if "positive" in prompt else 1.0
        return {"0": [value, 0.0], "1": [0.0, value]}


def input_file(folder):
    source = Path(folder) / "prompts.jsonl"
    source.write_bytes(canonical_json({"pair_id": "train-1", "split": "train",
                                       "positive_prompt": "positive",
                                       "negative_prompt": "negative"}))
    return source


class CaptureRegression(unittest.TestCase):
    def test_last_layer_is_pre_norm_and_hooks_are_removed(self):
        engine = LocalQwenCapture.__new__(LocalQwenCapture)
        engine.model = FakeModel()
        engine.torch = SimpleNamespace(inference_mode=nullcontext)
        engine.tokenizer = lambda prompt, return_tensors: {"input_ids": Tokens()}
        engine.max_tokens = 128
        engine.device = "cpu"
        self.assertEqual(engine.capture("hello"), {"0": [2.0], "1": [3.0]})
        self.assertTrue(all(not layer.hooks for layer in engine.model.model.layers))
        engine.model.fail = True
        with self.assertRaisesRegex(RuntimeError, "forward failed"):
            engine.capture("hello")
        self.assertTrue(all(not layer.hooks for layer in engine.model.model.layers))

    def test_existing_receipt_fails_before_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            source = input_file(folder)
            output = Path(folder) / "out.jsonl"
            receipt = Path(str(output) + ".receipt.json")
            receipt.write_text('{"old":true}')
            with patch("Toolkit.modules.qwen_capture.LocalQwenCapture",
                       side_effect=AssertionError("should never infer")):
                with self.assertRaises(SystemExit) as caught:
                    capture.main(["--input", str(source), "--output", str(output),
                                  "--model-dir", folder])
            self.assertEqual(caught.exception.code, 1)
            self.assertFalse(output.exists())
            self.assertEqual(receipt.read_text(), '{"old":true}')

    def test_failed_receipt_publish_rolls_back_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source = input_file(folder)
            output = Path(folder) / "out.jsonl"
            with (patch("Toolkit.modules.qwen_capture.LocalQwenCapture", FakeCapture),
                  patch("Toolkit.tools.capture.write_new", side_effect=OSError("receipt failed"))):
                with self.assertRaises(SystemExit) as caught:
                    capture.main(["--input", str(source), "--output", str(output),
                                  "--model-dir", folder])
            self.assertEqual(caught.exception.code, 1)
            self.assertFalse(output.exists())
            self.assertFalse(Path(str(output) + ".receipt.json").exists())
            self.assertFalse(list(Path(folder).glob(".au-capture-*")))

    def test_roundtrip_and_streaming_estimator(self):
        with tempfile.TemporaryDirectory() as folder:
            source = input_file(folder)
            output = Path(folder) / "out.jsonl"
            direction = Path(folder) / "direction.json"
            with patch("Toolkit.modules.qwen_capture.LocalQwenCapture", FakeCapture):
                self.assertEqual(capture.main(["--input", str(source), "--output",
                                                str(output), "--model-dir", folder]), 0)
            receipt = json.loads(Path(str(output) + ".receipt.json").read_text())
            self.assertEqual(receipt["capture_method"],
                             "qwen3-final-prompt-token-decoder-pre-norm-v2")
            self.assertEqual(estimate_tool.main(["--input", str(output), "--output",
                                                  str(direction), "--checkpoint-manifest", STAMP]), 0)
            vectors = json.loads(direction.read_text())
            self.assertEqual(vectors["pair_count"], 1)
            self.assertEqual(vectors["layers"]["0"]["direction"], [1.0, 0.0])
            self.assertEqual(vectors["layers"]["1"]["direction"], [0.0, 1.0])

    def test_oversized_capture_never_publishes(self):
        with tempfile.TemporaryDirectory() as folder:
            source = input_file(folder)
            output = Path(folder) / "out.jsonl"
            with (patch("Toolkit.modules.qwen_capture.LocalQwenCapture", FakeCapture),
                  patch("Toolkit.tools.capture.MAX_CAPTURE_BYTES", 5)):
                with self.assertRaises(SystemExit):
                    capture.main(["--input", str(source), "--output", str(output),
                                  "--model-dir", folder])
            self.assertFalse(output.exists())
            self.assertFalse(Path(str(output) + ".receipt.json").exists())
            self.assertFalse(list(Path(folder).glob(".au-capture-*")))

    def test_streamed_input_limit_matches_capture_producer(self):
        self.assertEqual(MAX_CAPTURE_BYTES, 1024 ** 3)
        self.assertEqual(MAX_CAPTURE_LINE_BYTES, 32 * 1024 * 1024)
        self.assertEqual(MAX_CAPTURE_RECORDS, 100)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "activations.jsonl"
            with path.open("wb") as stream:
                for index in range(27):
                    row = {"pair_id": str(index), "split": "train",
                           "checkpoint_manifest_sha256": STAMP,
                           "positive": {"0": [2.0]},
                           "negative": {"0": [1.0]},
                           "padding": "x" * 32}
                    stream.write(canonical_json(row))
            self.assertEqual(estimate(iter_jsonl(path, max_bytes=MAX_CAPTURE_BYTES,
                                                 max_records=MAX_CAPTURE_RECORDS))["pair_count"], 27)


if __name__ == "__main__":
    unittest.main()
