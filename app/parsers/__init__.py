"""
Parser registry for Loadscope.

Each parser is a Python module in this folder that exports:
    KIND          : "chronograph" or "group"
    NAME          : display name shown in the UI (e.g., "Garmin Xero")
    KEY           : short stable identifier (e.g., "garmin")
    IMPORT_FOLDER : folder name (relative to project root) where its CSVs live
    detect(path)  : returns True if this parser can handle the file
    parse(path)   : returns a record dict (chronograph) or list[dict] (group)

To add a new chronograph or target-analysis app:
    1. Drop a new module in this folder (see garmin_xero.py for a template).
    2. Add it to ALL_PARSERS below.
    3. Done. The rest of the app picks it up automatically — drop a CSV in
       the window and the new parser's detect() gets a chance to claim it.

Order of ALL_PARSERS matters when files could be ambiguous — earlier parsers
get tried first.
"""

from . import ballisticx, garmin_xero


ALL_PARSERS = [
    garmin_xero,
    ballisticx,
]


def detect_parser(path):
    """Return the parser module that handles this file, or None."""
    for parser in ALL_PARSERS:
        try:
            if parser.detect(path):
                return parser
        except Exception:
            continue
    return None


def parser_by_key(key):
    """Look up a parser by its stable KEY string."""
    for parser in ALL_PARSERS:
        if parser.KEY == key:
            return parser
    return None


def chronograph_parsers():
    return [p for p in ALL_PARSERS if p.KIND == "chronograph"]


def group_parsers():
    return [p for p in ALL_PARSERS if p.KIND == "group"]
