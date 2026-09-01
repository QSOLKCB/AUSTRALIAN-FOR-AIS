"""
Tests for JSON Schema validity and structure.
"""

import json
import pathlib

import jsonschema
import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXAMPLE_SCHEMA_PATH = SCHEMAS_DIR / "example.schema.json"
EVALUATION_SCHEMA_PATH = SCHEMAS_DIR / "evaluation.schema.json"
DATA_PATH = REPO_ROOT / "data" / "starter" / "examples.jsonl"


def load_schema(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


class TestSchemaFiles:
    def test_example_schema_exists(self):
        assert EXAMPLE_SCHEMA_PATH.exists(), "schemas/example.schema.json must exist"

    def test_evaluation_schema_exists(self):
        assert EVALUATION_SCHEMA_PATH.exists(), "schemas/evaluation.schema.json must exist"

    def test_example_schema_is_valid_json(self):
        schema = load_schema(EXAMPLE_SCHEMA_PATH)
        assert isinstance(schema, dict)

    def test_evaluation_schema_is_valid_json(self):
        schema = load_schema(EVALUATION_SCHEMA_PATH)
        assert isinstance(schema, dict)

    def test_example_schema_has_required_fields(self):
        schema = load_schema(EXAMPLE_SCHEMA_PATH)
        assert "id" in schema["required"]
        assert "utterance" in schema["required"]
        assert "pragmatic_interpretations" in schema["required"]
        assert "confidence" in schema["required"]
        assert "ambiguity" in schema["required"]
        assert "hostility" in schema["required"]

    def test_evaluation_schema_has_required_fields(self):
        schema = load_schema(EVALUATION_SCHEMA_PATH)
        assert "example_id" in schema["required"]
        assert "predicted_pragmatic" in schema["required"]
        assert "model_confidence" in schema["required"]


class TestStarterDataAgainstSchema:
    """Each starter example must validate against the example schema."""

    def _load_examples(self):
        records = []
        with DATA_PATH.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if line:
                    records.append((lineno, json.loads(line)))
        return records

    def test_starter_data_exists(self):
        assert DATA_PATH.exists(), "data/starter/examples.jsonl must exist"

    def test_all_records_valid(self):
        schema = load_schema(EXAMPLE_SCHEMA_PATH)
        records = self._load_examples()
        assert len(records) > 0, "Starter dataset must be non-empty"
        for lineno, record in records:
            try:
                jsonschema.validate(record, schema)
            except jsonschema.ValidationError as exc:
                pytest.fail(
                    f"Line {lineno} (id={record.get('id', '?')}): {exc.message}"
                )

    def test_all_records_have_ids(self):
        records = self._load_examples()
        for lineno, record in records:
            assert record.get("id"), f"Line {lineno}: missing 'id'"

    def test_ids_are_unique(self):
        records = self._load_examples()
        ids = [r["id"] for _, r in records]
        assert len(ids) == len(set(ids)), "Example IDs must be unique"

    def test_context_swap_pairs_exist(self):
        records = self._load_examples()
        groups: dict[str, list] = {}
        for _, record in records:
            csg = record.get("context_swap_group")
            if csg:
                groups.setdefault(csg, []).append(record["id"])
        # At least one context-swap group with at least two members
        multi = {g: ids for g, ids in groups.items() if len(ids) >= 2}
        assert multi, "Starter data must include at least one context-swap pair"
