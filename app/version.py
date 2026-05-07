"""Single source of truth for the app version.

Bump APP_VERSION whenever you ship a new build. The updater compares this
against the version field in the remote manifest to decide if there's an
update to offer.

TEMPLATE_VERSION is independent — the .xltx template can be updated separately
from the app itself (e.g., a workbook tweak doesn't require rebuilding the .app).
"""

# App branding — one source of truth for display name + version
APP_NAME = "Cold Bore"
LEGACY_APP_NAMES = ("Rifle Load Importer",)  # for config migration on first launch
APP_VERSION = "0.6.0"
TEMPLATE_VERSION = "1.0"

# Disclaimer version — bump this if the disclaimer text changes substantively.
# When this number is newer than what the user has accepted (config field
# disclaimer_accepted_version), they get re-prompted on next launch.
DISCLAIMER_VERSION = 1


DISCLAIMER_TEXT = """\
Cold Bore is a tool for organizing and analyzing data you collect during \
precision rifle load development. It is NOT a source of load data and does \
not recommend specific charge weights, bullet types, or seating depths to \
use in your firearm.

By using this app, you acknowledge that:

1. Reloading ammunition is inherently dangerous. Improper handling of \
gunpowder, primers, and components can result in severe injury, death, \
and property damage.

2. Cold Bore analyzes data you provide, but is not a substitute for safe \
handloading practice. Always cross-reference loads against published \
reloading manuals from powder, bullet, and cartridge manufacturers. Watch \
for pressure signs. Start below maximum loads and work up.

3. No warranty is provided. Cold Bore is provided "as is" without any \
warranty of accuracy, fitness for a particular purpose, or freedom from \
defects. Computed scores and rankings are statistical analyses of your \
inputs, not load recommendations.

4. The developer is not liable for any damage, injury, or loss resulting \
from use of this app or actions taken based on its analyses.

5. You assume all risk associated with handloading and shooting.

If you do not agree with these terms, do not use this app."""


def parse_version(s):
    """Parse 'x.y.z' into a tuple of ints. Tolerates extra suffixes like '0.4.0-beta'.
    Returns (0,) on failure so unknown versions sort lowest."""
    if not s:
        return (0,)
    main = str(s).split("-")[0].strip()
    parts = []
    for p in main.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts) if parts else (0,)


def is_newer(remote, local):
    """Return True if remote version is strictly newer than local version."""
    return parse_version(remote) > parse_version(local)
