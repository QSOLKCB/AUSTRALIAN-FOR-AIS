"""Small canonical JSON and SHA-256 utilities for local research receipts."""

import hashlib
import json
from pathlib import Path


def canonical_json(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reject_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def json_record(line):
    return json.loads(line, object_pairs_hook=reject_duplicate_keys,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError(f"non-finite JSON constant: {value}")))


def load_jsonl(path, *, max_bytes=128 * 1024 * 1024, max_records=1000):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError("input is missing or exceeds the byte limit")
    records = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            if len(records) >= max_records:
                raise ValueError("input exceeds the record limit")
            try:
                records.append(json_record(line))
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid JSONL line {line_number}: {exc}") from exc
    if not records:
        raise ValueError("input has no records")
    return records


def write_new(path, data):
    """Never overwrite an existing receipt. Same-directory temp and atomic link."""
    import os
    import tempfile
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(str(path))
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".au-tmp-",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
