"""Valida que los ejemplos de contracts/examples cumplan los esquemas de contracts/schemas.

Uso:  python contracts/validate_examples.py
Requiere: pip install jsonschema
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent
ok = True
for schema_path in sorted((ROOT / "schemas").glob("*.json")):
    example_path = ROOT / "examples" / schema_path.name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    example = json.loads(example_path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(example))
    if errors:
        ok = False
        print(f"FALLA  {schema_path.name}")
        for e in errors:
            print("   -", e.message)
    else:
        print(f"OK     {schema_path.name}")
sys.exit(0 if ok else 1)
