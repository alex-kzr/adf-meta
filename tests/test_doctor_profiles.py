"""The umbrella diagnostic wrapper forwards trusted selectors without a shell."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("adf_doctor_profile_tests", ROOT / "scripts/doctor.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load the diagnostic wrapper")
doctor = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"grp": SimpleNamespace(getgrgid=lambda _: SimpleNamespace(gr_name="synthetic"))}):
    SPEC.loader.exec_module(doctor)


class DoctorProfileForwardingTests(unittest.TestCase):
    def test_explicit_profiles_node_and_paths_reach_worker_as_separate_argv(self):
        args = doctor.argument_parser().parse_args([
            "--worker", "/synthetic/worker", "--node", "/synthetic/node",
            "--codex", "/synthetic/codex", "--claude", "/synthetic/claude",
            "--codex-home", "/synthetic/home/profile codex", "--claude-config-dir", "/synthetic/home/profile claude"])
        expected = [str(args.worker), "doctor", "--root", str(Path("/synthetic/runtime")), "--node", str(args.node),
                    "--codex", "/synthetic/codex", "--claude", "/synthetic/claude",
                    "--codex-home", str(args.codex_home), "--claude-config-dir", str(args.claude_config_dir)]
        self.assertEqual(doctor.worker_doctor_argv(args, Path("/synthetic/runtime")), expected)

    def test_omitted_flags_do_not_inherit_shell_selectors(self):
        with patch.dict("os.environ", {"CODEX_HOME": "/unapproved", "CLAUDE_CONFIG_DIR": "/unapproved"}):
            args = doctor.argument_parser().parse_args(["--worker", "/synthetic/worker"])
        self.assertEqual(doctor.worker_doctor_argv(args, Path("/synthetic/runtime")),
                         [str(args.worker), "doctor", "--root", str(Path("/synthetic/runtime"))])

    def test_diagnose_uses_profile_flags_without_invoking_native_or_network(self):
        args = doctor.argument_parser().parse_args(["--root", "/synthetic/runtime", "--worker", "/synthetic/worker",
            "--node", "/synthetic/node", "--codex-home", "/synthetic/profile-codex", "--claude-config-dir", "/synthetic/profile-claude"])
        calls = []
        def command(argv, timeout=30):
            calls.append(argv)
            return {"ok": True, "value": json.dumps({"execution_capabilities_available": False})}
        with patch.object(doctor, "command", side_effect=command), patch.object(doctor.platform, "system", return_value="test"), \
             patch.object(doctor, "http_probe", return_value={"ok": False}), \
             patch.object(doctor, "container_bindings", return_value={"ok": False}):
            report = doctor.diagnose(args)
        expected = [str(args.worker), "doctor", "--root", str(args.root.resolve()), "--node", str(args.node),
                    "--codex-home", str(args.codex_home), "--claude-config-dir", str(args.claude_config_dir)]
        self.assertEqual(calls[0], expected)
        self.assertFalse(report["mvp_ready"])


if __name__ == "__main__":
    unittest.main()
