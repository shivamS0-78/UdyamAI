"""Smoke tests for CLI wrapper scripts in scripts/data/.

Verifies that:
1. Each wrapper script imports successfully (defensive import guard works).
2. Each script exits cleanly with --help.
3. The import_all wrapper imports run_cli_all.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# scripts/data/ lives at the repo root, not inside backend/
_REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = _REPO_ROOT / "scripts" / "data"

WRAPPER_SCRIPTS = sorted(SCRIPTS_DIR.glob("import_*.py"))
# In Docker the scripts/ dir may not be mounted — skip the whole module.
skip_reason = f"Wrapper scripts not found at {SCRIPTS_DIR} (not mounted in container?)"
pytestmark = pytest.mark.skipif(not WRAPPER_SCRIPTS, reason=skip_reason)


@pytest.mark.parametrize(
    "script",
    WRAPPER_SCRIPTS,
    ids=[s.stem for s in WRAPPER_SCRIPTS],
)
def test_wrapper_imports_without_crashing(script: Path):
    """Run each wrapper script with --help; it should exit 0 (import succeeded)."""
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=10,
    )
    # The ingestion CLI uses argparse, so --help exits 0.
    # If the import guard triggers, we'd get exit code 1 with the error message.
    assert result.returncode == 0, (
        f"{script.name} failed to import:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_defensive_import_structure():
    """All wrapper scripts contain a try/except ImportError guard."""
    for script in WRAPPER_SCRIPTS:
        source = script.read_text()
        assert "try:" in source, f"{script.name} missing try/except guard"
        assert "except ImportError" in source, f"{script.name} missing ImportError handler"
        assert "sys.exit(1)" in source, f"{script.name} doesn't exit 1 on import failure"
        # Verify the friendly message is present
        assert "Failed to import ingestion pipeline" in source, (
            f"{script.name} missing friendly error message"
        )


def test_import_all_uses_run_cli_all():
    """import_all.py imports run_cli_all, not run_cli."""
    script = SCRIPTS_DIR / "import_all.py"
    source = script.read_text()
    assert "run_cli_all" in source
    assert "from app.ingestion.cli import run_cli_all" in source
