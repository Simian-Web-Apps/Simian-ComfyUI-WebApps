"""Test the CLI."""

import glob
import importlib
import os
import shutil
import sys

import pytest


# Helper to import the module with a custom sys.argv
def import_main(argv):
    sys.argv = argv
    importlib.invalidate_caches()
    return importlib.reload(importlib.import_module("simian.comfy.__main__"))


@pytest.fixture
def tmp_folder(tmp_path):
    return tmp_path


def get_file_list(folder: str) -> list[str]:
    return glob.glob(os.path.join(folder, "**", "*.*"), recursive=True)


def test_new_command_creates_folder(tmp_folder):
    """Test the create from template command."""
    folder = str(tmp_folder / "new_app")

    # Run the CLI
    sys.argv = ["prog", "new", folder]
    importlib.import_module("simian.comfy.__main__")

    # Get the template and copied files lists.
    mod = importlib.import_module("simian.comfy.template.comfy_webapp")
    template_files = get_file_list(os.path.dirname(mod.__file__))
    copied_files = get_file_list(folder)

    shutil.rmtree(tmp_folder, ignore_errors=True)

    # Verify that the folder was created and the template copied
    assert len(template_files) == len(copied_files)


def test_new_command_raises_on_non_empty():
    """Verify that you cannot create a new app in a folder with contents."""
    folder = os.path.dirname(__file__)

    with pytest.raises(ValueError):
        import_main(["prog", "new", folder])


def test_start_example_calls_run(monkeypatch):
    """Test the start_example command."""
    # Mock simian.local.run, as it would block the test process.
    run_calls = []

    def fake_run(app_name):
        run_calls.append(app_name)

    monkeypatch.setattr("simian.local.run", fake_run)

    import_main(["prog", "start_example"])

    assert run_calls == ["simian.comfy.examples.compositemasked.comfy_app"]


def test_help_command_prints_help(capsys):
    """Test the help command."""
    import_main(["prog", "help"])
    out, _ = capsys.readouterr()

    # The help output should list the available commands
    assert "new" in out
    assert "start_example" in out
    assert "help" in out
