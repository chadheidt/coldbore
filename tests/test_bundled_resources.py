"""Regression tests for bundled-resource path resolution.

v0.14.3 bug: get_bundled_demo_workbook_path() (and the pocket-card /
splash logo lookups) resolved resources relative to __file__. In a
py2app .app, modules load from Contents/Resources/lib/pythonXX.zip, so
__file__-relative paths land INSIDE the zip and miss the real
Contents/Resources/ where DATA_FILES live -> "Pick a workbook first"
and a logo-less card/splash in the installed app.

These tests reproduce the py2app bundle layout (Contents/MacOS/<exe> +
Contents/Resources/<file>) and assert the sys.executable-based resolver
finds the file.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import demo_tour  # noqa: E402

DEMO_FNAME = "Loadscope - Demo Workbook.xlsx"


def test_dev_mode_finds_bundled_demo_workbook():
    # Running from the source tree: app/resources/<file> exists in repo.
    path = demo_tour.get_bundled_demo_workbook_path()
    assert path is not None, "dev-tree demo workbook should resolve"
    assert os.path.isfile(path)
    assert path.endswith(DEMO_FNAME)


def test_frozen_bundle_resolves_via_sys_executable(tmp_path, monkeypatch):
    # Reproduce the py2app .app layout that was broken:
    #   <App>/Contents/MacOS/Loadscope        <- sys.executable
    #   <App>/Contents/Resources/<DEMO_FNAME> <- DATA_FILES land here
    contents = tmp_path / "Loadscope.app" / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)
    fake_exe = macos / "Loadscope"
    fake_exe.write_text("#!/bin/sh\n")
    real_demo = resources / DEMO_FNAME
    real_demo.write_text("xlsx-stub")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    resolved = demo_tour.get_bundled_demo_workbook_path()
    assert resolved == str(real_demo), (
        f"frozen bundle should resolve via sys.executable; got {resolved!r}"
    )


def test_frozen_bundle_missing_file_does_not_crash(tmp_path, monkeypatch):
    # Frozen, but no Resources file at the executable-relative path: the
    # resolver must not raise (it may still find the repo dev copy, which
    # is fine — the contract is "never crash, return a path or None").
    macos = tmp_path / "Loadscope.app" / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    fake_exe = macos / "Loadscope"
    fake_exe.write_text("#!/bin/sh\n")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    # Must not raise; result is either a valid path or None.
    result = demo_tour.get_bundled_demo_workbook_path()
    assert result is None or os.path.isfile(result)
