"""Matched-pair activation contrasts. No model inference or external dependencies.

These are statistical directions, not discovered neurons, causal explanations,
or evidence that an Australian-language feature exists.
"""

import math


class ContrastError(ValueError):
    """Invalid or non-identifiable contrast input."""


def _vector(value, description):
    if not isinstance(value, list) or not value or len(value) > 16384:
        raise ContrastError(f"{description}: expected a non-empty, bounded vector")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
        raise ContrastError(f"{description}: vector must contain finite numbers only")
    return [float(v) for v in value]


def _layers(value, description):
    if not isinstance(value, dict) or not value:
        raise ContrastError(f"{description}: expected a layer-to-vector object")
    if any(type(k) is not str or not k.isdecimal() or str(int(k)) != k for k in value):
        raise ContrastError(f"{description}: layer keys must be canonical non-negative integers")
    return {k: _vector(v, f"{description} layer {k}") for k, v in value.items()}


def estimate(pairs):
    """Return unit vectors of the paired mean differences, sorted by pair ID.

    Inputs: [{pair_id, split:'train', positive:{layer:[...]},
              negative:{layer:[...]}}]. A held-out record is never admitted.
    A nonzero direction is a descriptive contrast, not a causal effect.
    """
    if not isinstance(pairs, list) or not pairs:
        raise ContrastError("at least one training pair is required")
    seen = set()
    validated = []
    layout = None
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            raise ContrastError(f"pair {index}: expected an object")
        pair_id = pair.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id.strip() or len(pair_id) > 256:
            raise ContrastError(f"pair {index}: invalid pair_id")
        if pair_id in seen:
            raise ContrastError(f"duplicate pair_id: {pair_id}")
        seen.add(pair_id)
        if pair.get("split") != "train":
            raise ContrastError(f"{pair_id}: estimation accepts training split only")
        positive = _layers(pair.get("positive"), f"{pair_id} positive")
        negative = _layers(pair.get("negative"), f"{pair_id} negative")
        shape = {k: len(v) for k, v in positive.items()}
        if shape != {k: len(v) for k, v in negative.items()}:
            raise ContrastError(f"{pair_id}: mismatched positive/negative shapes")
        if layout is None:
            layout = shape
        elif shape != layout:
            raise ContrastError(f"{pair_id}: inconsistent layer shape")
        validated.append((pair_id, positive, negative))

    validated.sort(key=lambda item: item[0])
    results = {}
    for layer in sorted(layout, key=int):
        width = layout[layer]
        delta = [
            math.fsum(pos[layer][j] - neg[layer][j] for _, pos, neg in validated) / len(validated)
            for j in range(width)
        ]
        if any(not math.isfinite(x) for x in delta):
            raise ContrastError(f"layer {layer}: non-finite mean difference")
        magnitude = math.hypot(*delta)
        if magnitude == 0.0 or not math.isfinite(magnitude):
            raise ContrastError(f"layer {layer}: zero or invalid contrast magnitude")
        results[layer] = {"direction": [x / magnitude for x in delta],
                          "mean_delta_l2": magnitude, "width": width}
    return {"method": "paired-mean-difference-l2-v1",
            "pair_count": len(validated), "layers": results}


def steer_vector(hidden, direction, strength):
    """Pure functional vector addition for deterministic unit tests; no model hook."""
    base = _vector(hidden, "hidden")
    vec = _vector(direction, "direction")
    if len(base) != len(vec):
        raise ContrastError("hidden state and steering direction widths differ")
    if type(strength) not in (int, float) or not math.isfinite(strength):
        raise ContrastError("strength must be a finite number")
    result = [a + float(strength) * b for a, b in zip(base, vec)]
    if any(not math.isfinite(x) for x in result):
        raise ContrastError("steering produced non-finite values")
    return result
