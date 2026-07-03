from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_launch_agent.sh"


class InstallLaunchAgentTests(unittest.TestCase):
    def test_staged_runtime_excludes_untracked_workspace_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            runtime_dir = temp_root / "runtime"
            stale_project = runtime_dir / "TOBI_OS"
            stale_project.mkdir(parents=True)
            (stale_project / "private.txt").write_text("remove me", encoding="utf-8")
            runtime_report = runtime_dir / "reports" / "latest_briefing.md"
            runtime_report.parent.mkdir(parents=True)
            runtime_report.write_text("preserve runtime state", encoding="utf-8")

            env = {
                **os.environ,
                "FORCE_STAGE_RUNTIME": "1",
                "RUNTIME_DIR": str(runtime_dir),
                "LAUNCH_AGENTS_DIR": str(temp_root / "launch-agents"),
            }
            completed = subprocess.run(
                [str(INSTALLER), "--print-only"],
                cwd=ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((runtime_dir / "main.py").exists())
            self.assertTrue((runtime_dir / "src" / "ai_signal_routine" / "cli.py").exists())
            self.assertFalse(stale_project.exists())
            self.assertFalse((runtime_dir / "career_system").exists())
            self.assertEqual(
                runtime_report.read_text(encoding="utf-8"), "preserve runtime state"
            )
            self.assertIn(str(runtime_dir / "scripts" / "run_daily.sh"), completed.stdout)


if __name__ == "__main__":
    unittest.main()
