"""Tests for app/installer.py — the in-app self-installer helper script
generator and lifecycle helpers.

The installer module is intentionally PyQt-free so it can be unit-tested
without a display server. We don't actually exec the helper script during
tests (that would replace the running app), but we can verify:

  - The bash it generates is well-formed and contains the right commands
  - can_self_install() correctly returns False when we're not in a .app
  - consume_last_install_error() reads and removes the log file as expected
  - launch_install_swap() declines gracefully when there's no zip / no .app
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Make app/ importable
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app"))

import installer  # noqa: E402


def test_can_self_install_returns_false_in_dev_mode():
    """In a normal pytest run we're under /usr/bin/python3 or a venv, not
    inside a .app bundle, so can_self_install must return False so we
    don't accidentally try to swap a non-bundle."""
    assert installer.can_self_install() is False


def test_running_app_bundle_path_returns_none_in_dev_mode():
    """Same idea — _running_app_bundle_path walks up from sys.executable
    looking for a *.app parent. In dev there is none."""
    assert installer._running_app_bundle_path() is None


def test_build_helper_script_contains_required_steps():
    """The generated bash script should reference all the path arguments
    and key macOS commands (ditto, mv, xattr, open). We're not running it
    in tests — just smoke-checking the structure."""
    script = installer._build_helper_script(
        zip_path="/tmp/Loadscope.zip",
        app_bundle_path="/Applications/Loadscope.app",
        error_log_path="/Users/x/Library/Application Support/Loadscope/last_install_error.log",
    )

    # Sanity: bash shebang and exit on undef vars
    assert script.startswith("#!/bin/bash")
    assert "set -u" in script

    # Each path got embedded in the script (via single-quote shell escaping)
    assert "/tmp/Loadscope.zip" in script
    assert "Loadscope.app" in script
    assert "last_install_error.log" in script

    # Critical operations are present
    assert "/usr/bin/ditto" in script
    assert "xattr" in script
    assert "/usr/bin/open" in script
    assert "mv " in script
    assert "sleep " in script  # parent-quit grace period


def test_build_helper_script_handles_paths_with_spaces():
    """The breadcrumb format 'Loadscope.app' contains a space — verify
    our shell quoting wraps each path in single quotes so bash treats it
    as a single argument."""
    script = installer._build_helper_script(
        zip_path="/tmp/foo bar.zip",
        app_bundle_path="/Applications/Loadscope.app",
        error_log_path="/tmp/error.log",
    )
    # If quoting failed, 'foo bar.zip' would split into 'foo' and 'bar.zip'.
    # Verify the literal "'/tmp/foo bar.zip'" appears in the script.
    assert "'/tmp/foo bar.zip'" in script
    assert "'/Applications/Loadscope.app'" in script


def test_consume_last_install_error_reads_and_deletes(tmp_path, monkeypatch):
    """After reading the error log, the file should be removed so the
    user isn't nagged about the same failure on every launch."""
    fake_cfg_dir = tmp_path / "ColdBore"
    fake_cfg_dir.mkdir()
    log_path = fake_cfg_dir / installer.ERROR_LOG_NAME
    log_path.write_text("Couldn't move new app into place\n")

    monkeypatch.setattr(installer, "_config_support_dir", lambda: fake_cfg_dir)

    msg = installer.consume_last_install_error()
    assert msg is not None
    assert "Couldn't move new app into place" in msg
    assert not log_path.exists()  # consumed = deleted


def test_consume_last_install_error_returns_none_when_clean(tmp_path, monkeypatch):
    """No log file → no error to surface, returns None."""
    fake_cfg_dir = tmp_path / "ColdBore"
    fake_cfg_dir.mkdir()
    monkeypatch.setattr(installer, "_config_support_dir", lambda: fake_cfg_dir)

    assert installer.consume_last_install_error() is None


def test_launch_install_swap_returns_false_without_zip():
    """No zip path → can't install; caller should fall back to manual link."""
    assert installer.launch_install_swap("") is False
    assert installer.launch_install_swap("/nonexistent/file.zip") is False


def test_launch_install_swap_returns_false_in_dev_mode(tmp_path):
    """Even with a real zip, dev mode (no .app bundle) → False."""
    fake_zip = tmp_path / "fake.zip"
    fake_zip.write_bytes(b"not a real zip but exists")
    assert installer.launch_install_swap(str(fake_zip)) is False
