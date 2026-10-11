"""Bind the standalone worker compatibility fixture to the pinned request builder."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SharedEnvironmentContractTests(unittest.TestCase):
    def test_fixture_matches_actual_orchestrator_request_builder(self) -> None:
        fixture = json.loads((ROOT / "services/runtime-worker/tests/fixtures/orchestrator-shared-envelope.json").read_text())
        source = (ROOT / "services/orchestrator/src/adf_orchestrator/engine.py").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(source).hexdigest(), fixture["request_builder_source_sha256"])
        module = ast.parse(source)
        engine = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "WorkflowEngine")
        intent = next(node for node in engine.body if isinstance(node, ast.FunctionDef) and node.name == "intent")
        values = [ast.literal_eval(value) for node in ast.walk(intent) if isinstance(node, ast.Dict)
                  for key, value in zip(node.keys, node.values) if isinstance(key, ast.Constant) and key.value == "env_allowlist"]
        self.assertEqual(values, [fixture["request"]["env_allowlist"]])


if __name__ == "__main__":
    unittest.main()
