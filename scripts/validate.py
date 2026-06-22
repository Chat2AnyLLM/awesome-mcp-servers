#!/usr/bin/env python3
"""Validate all server YAML files and source YAML files against their schemas."""

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_SCHEMA_PATH = REPO_ROOT / "schema" / "mcp-server.schema.json"
SOURCE_SCHEMA_PATH = REPO_ROOT / "schema" / "source.schema.json"
SERVERS_DIR = REPO_ROOT / "servers"
SOURCES_DIR = REPO_ROOT / "sources"


def load_schema(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def validate_file(file_path: Path, schema: dict) -> list[str]:
    """Validate a single YAML file against a schema. Returns list of error messages."""
    errors = []
    try:
        with open(file_path, encoding="utf-8") as f:
            if file_path.suffix == ".json":
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]
    except json.JSONDecodeError as e:
        return [f"JSON parse error: {e}"]

    if data is None:
        return ["File is empty"]

    # Validate against schema
    validator = Draft202012Validator(schema)
    for error in validator.iter_errors(data):
        errors.append(f"  {error.json_path}: {error.message}")

    # Check identifier matches filename
    expected_slug = file_path.stem
    identifier = data.get("slug") or data.get("name")
    if data.get("slug") and identifier != expected_slug:
        errors.append(
            f"  identifier '{identifier}' does not match filename '{expected_slug}'"
        )

    return errors


def validate_directory(directory: Path, schema: dict, label: str) -> int:
    """Validate all YAML files in a directory. Returns error count."""
    yaml_files = sorted(directory.rglob("*.yaml")) + sorted(directory.rglob("*.json"))

    if not yaml_files:
        print(f"  (no {label} files found)")
        return 0

    total_errors = 0
    for file_path in yaml_files:
        errors = validate_file(file_path, schema)
        if errors:
            print(f"FAIL: {file_path.name}")
            for err in errors:
                print(err)
            total_errors += len(errors)
        else:
            print(f"  OK: {file_path.name}")

    return total_errors


def main() -> int:
    server_schema = load_schema(SERVER_SCHEMA_PATH)
    source_schema = load_schema(SOURCE_SCHEMA_PATH)

    print("=== Validating servers/ ===")
    server_errors = validate_directory(SERVERS_DIR, server_schema, "server")

    print("\n=== Validating sources/ ===")
    source_errors = validate_directory(SOURCES_DIR, source_schema, "source")

    total_errors = server_errors + source_errors
    if total_errors:
        print(f"\n{total_errors} error(s) found.")
        return 1

    server_count = len(list(SERVERS_DIR.rglob("*.yaml"))) + len(list(SERVERS_DIR.rglob("*.json")))
    source_count = len(list(SOURCES_DIR.glob("*.yaml")))
    print(f"\nAll valid: {server_count} server(s), {source_count} source(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
