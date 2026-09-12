"""Basic smoke tests for the application shell."""

import json
from pathlib import Path


def test_project_layout() -> None:
    """Ensure the main application directories exist."""
    root = Path(__file__).resolve().parents[1]
    assert (root / "main.py").exists()
    assert (root / "core").is_dir()
    assert (root / "plugins").is_dir()


def test_v014_effect_defaults() -> None:
    """Ensure the checked-in configuration contains the visual controls."""
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "data" / "config.json").read_text(encoding="utf-8"))
    assert config["effects"]["window_effect"] == "mica"
    assert 50 <= config["effects"]["panel_opacity"] <= 100


def test_file_manager_module_layout() -> None:
    """Ensure all file management tools are present for plugin loading."""
    root = Path(__file__).resolve().parents[1]
    module = root / "plugins" / "file_manager"
    expected = {
        "__init__.py",
        "widget.py",
        "styles.py",
        "utils.py",
        "smart_organizer.py",
        "duplicate_finder.py",
        "bulk_rename.py",
        "space_analyzer.py",
        "file_search.py",
    }
    assert expected.issubset({path.name for path in module.iterdir()})
