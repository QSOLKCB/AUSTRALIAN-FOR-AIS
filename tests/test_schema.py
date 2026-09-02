"""Tests for JSON Schema validity, versioning, and packaged copies."""

import json
import pathlib
from importlib import resources

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
    def test_schema_files_exist(self):
        assert EXAMPLE_SCHEMA_PATH.exists()
        assert EVALUATION_SCHEMA_PATH.exists()

    def test_schemas_are_valid_draft_2020_12(self):
        jsonschema.Draft202012Validator.check_schema(load_schema(EXAMPLE_SCHEMA_PATH))
        jsonschema.Draft202012Validator.check_schema(load_schema(EVALUATION_SCHEMA_PATH))

    def test_project_schema_version_is_machine_readable(self):
        for path in (EXAMPLE_SCHEMA_PATH, EVALUATION_SCHEMA_PATH):
            schema = load_schema(path)
            assert schema["x-project-schema-version"] == "0.1.0"
            assert "/v0.1.0/" in schema["$id"]

    def test_evaluation_schema_requires_all_advertised_dimensions(self):
        required = set(load_schema(EVALUATION_SCHEMA_PATH)["required"])
        assert {
            "example_id",
            "predicted_literal",
            "predicted_pragmatic",
            "predicted_hostility",
            "predicted_social_valence",
            "predicted_ambiguity",
            "model_confidence",
        } <= required

    def test_packaged_schemas_match_root_contracts(self):
        package_dir = resources.files("australian_for_ais").joinpath("schemas")
        packaged_example = json.loads(
            package_dir.joinpath("example.schema.json").read_text(encoding="utf-8")
        )
        packaged_evaluation = json.loads(
            package_dir.joinpath("evaluation.schema.json").read_text(encoding="utf-8")
        )
        assert packaged_example == load_schema(EXAMPLE_SCHEMA_PATH)
        assert packaged_evaluation == load_schema(EVALUATION_SCHEMA_PATH)


class TestStarterDataAgainstSchema:
    def _load_examples(self):
        records = []
        with DATA_PATH.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if line:
                    records.append((lineno, json.loads(line)))
        return records

    def test_all_records_valid(self):
        schema = load_schema(EXAMPLE_SCHEMA_PATH)
        records = self._load_examples()
        assert len(records) == 15
        for lineno, record in records:
            try:
                jsonschema.validate(record, schema)
            except jsonschema.ValidationError as exc:
                pytest.fail(f"Line {lineno} (id={record.get('id', '?')}): {exc.message}")

    def test_ids_are_unique(self):
        records = self._load_examples()
        ids = [record["id"] for _, record in records]
        assert len(ids) == len(set(ids))

    def test_primary_interpretations_are_scorable_or_insufficient(self):
        for _, record in self._load_examples():
            primary = record["primary_pragmatic_interpretation"]
            assert primary == "insufficient_context" or primary in record["pragmatic_interpretations"]

    def test_context_swap_pairs_exist(self):
        groups: dict[str, list[str]] = {}
        for _, record in self._load_examples():
            group = record.get("context_swap_group")
            if group:
                groups.setdefault(group, []).append(record["id"])
        assert any(len(ids) >= 2 for ids in groups.values())
