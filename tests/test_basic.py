"""Basic smoke tests for the application shell."""

from pathlib import Path


def test_project_layout() -> None:
    """Ensure the main application directories exist."""
    root = Path(__file__).resolve().parents[1]
    assert (root / "main.py").exists()
    assert (root / "core").is_dir()
    assert (root / "plugins").is_dir()
