"""Regression tests for the loadscope:// URL handler.

The action-extraction logic is what routes clickable workbook hyperlinks
(Charts!A10, Seating Depth!A28) to in-app handlers. Keep it tight.
"""
import os
import sys
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from PyQt5.QtCore import QUrl
from main import parse_loadscope_action  # noqa: E402


@pytest.mark.parametrize("url_str,expected", [
    # Canonical shape: loadscope://action
    ("loadscope://reset-weights", "reset-weights"),
    # Path-style: scheme:///action (also valid)
    ("loadscope:///reset-weights", "reset-weights"),
    # Trailing slash tolerated
    ("loadscope://reset-weights/", "reset-weights"),
    # Case-insensitive (the dispatcher compares lowercase)
    ("loadscope://Reset-Weights", "reset-weights"),
    ("LOADSCOPE://reset-weights", "reset-weights"),
    # Empty action — caller should log + ignore
    ("loadscope://", ""),
])
def test_parse_loadscope_action(url_str, expected):
    assert parse_loadscope_action(QUrl(url_str)) == expected


@pytest.mark.parametrize("url_str", [
    "http://example.com/reset-weights",   # wrong scheme
    "file:///Users/x/foo.csv",            # file URL — not loadscope
    "",                                   # empty
])
def test_parse_loadscope_action_rejects_non_loadscope(url_str):
    assert parse_loadscope_action(QUrl(url_str)) == ""


def test_parse_loadscope_action_handles_none():
    assert parse_loadscope_action(None) == ""
