"""Optional local Qwen hidden-state capture; imports ML dependencies lazily.

Captures residual-stream layer outputs at the final prompt token. This is NOT
a cross-layer transcoder, speech encoder, or activation-steering implementation.
"""

import hashlib
import os
from pathlib import Path

from .receipts import sha256_file


def checkpoint_receipt(directory):
    root = Path(directory)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("model must be an existing real local directory")
    paths = sorted(p for p in root.rglob("*") if p.is_file() or p.is_symlink())
    if len(paths) > 256 or not any(p.suffix == ".safetensors" for p in paths):
        raise ValueError("checkpoint must contain local safetensors files (max 256 files)")
    selected = {}
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"symlink not permitted in model checkpoint: {path}")
        if path.suffix in {".safetensors", ".json", ".model"} or path.name in {
                "tokenizer.json", "merges.txt", "vocab.txt", "vocab.json"}:
            selected[path.relative_to(root).as_posix()] = sha256_file(path)
    combined = hashlib.sha256(
        "".join(f"{name}:{sha}\n" for name, sha in sorted(selected.items())).encode("utf-8")
    ).hexdigest()
    return {"file_sha256": selected, "checkpoint_manifest_sha256": combined}


class LocalQwenCapture:
    def __init__(self, model_dir, device="cpu", max_tokens=128):
        if device not in {"cpu", "cuda"}:
            raise ValueError("device must be cpu or cuda")
        if type(max_tokens) is not int or not 1 <= max_tokens <= 1024:
            raise ValueError("max_tokens must be 1..1024")
        model_dir = Path(model_dir)
        self.checkpoint = checkpoint_receipt(model_dir)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("Qwen capture needs locally installed torch and transformers") from exc
        if device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA was requested but is unavailable")
        self.torch = torch
        self.device = device
        self.max_tokens = max_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(model_dir), local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            str(model_dir), local_files_only=True, trust_remote_code=False,
            use_safetensors=True, torch_dtype=torch.float16 if device == "cuda" else torch.float32)
        if self.model.config.model_type != "qwen3":
            raise ValueError("v1 capture adapter supports Qwen3 checkpoints only")
        self.model.to(device)
        self.model.eval()

    def capture(self, prompt):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be non-empty text")
        encoded = self.tokenizer(prompt, return_tensors="pt")
        if encoded["input_ids"].shape[1] > self.max_tokens:
            raise ValueError("prompt exceeds max_tokens; no truncation permitted")
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        # Qwen3 normalizes the final hidden state *after* its last decoder
        # layer. output_hidden_states[1:] therefore mixes activation sites.
        # Hooks provide the same pre-final-norm decoder output at every layer.
        layers = getattr(getattr(self.model, "model", None), "layers", None)
        if layers is None or not len(layers):
            raise RuntimeError("Qwen3 decoder layers are unavailable")
        captured = {}
        handles = []

        def capture_hook(index):
            def hook(_module, _inputs, output):
                hidden = output[0] if isinstance(output, (tuple, list)) else output
                captured[str(index)] = hidden[0, -1, :].detach().float().cpu().tolist()
            return hook

        try:
            for index, layer in enumerate(layers):
                handles.append(layer.register_forward_hook(capture_hook(index)))
            with self.torch.inference_mode():
                self.model(**encoded, use_cache=False)
        finally:
            for handle in handles:
                handle.remove()
        if len(captured) != len(layers):
            raise RuntimeError("a decoder layer did not produce an activation")
        return {str(index): captured[str(index)] for index in range(len(layers))}
