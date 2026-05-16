"""Single source of truth for the app version.

Bump APP_VERSION whenever you ship a new build. The updater compares this
against the version field in the remote manifest to decide if there's an
update to offer.

TEMPLATE_VERSION is independent — the .xltx template can be updated separately
from the app itself (e.g., a workbook tweak doesn't require rebuilding the .app).
"""

# App branding — one source of truth for display name + version
APP_NAME = "Loadscope"
LEGACY_APP_NAMES = ("True Zero", "Cold Bore", "Rifle Load Importer")  # for config migration on first launch
APP_VERSION = "0.15.0"
TEMPLATE_VERSION = "1.0"

# Disclaimer version — bump this if the disclaimer text changes substantively.
# When this number is newer than what the user has accepted (config field
# disclaimer_accepted_version), they get re-prompted on next launch.
DISCLAIMER_VERSION = 3


DISCLAIMER_TEXT = """\
Loadscope is a tool for organizing and analyzing data you collect during \
precision rifle load development. It is NOT a source of published load \
data - it does not supply start or maximum charges, cartridge overall \
lengths, or load recipes; obtain those only from current reloading \
manuals published by your powder, bullet, and cartridge makers.

Loadscope does highlight a "suggested" winning charge or seating depth. \
That is only a statistical ranking of the loads you personally tested \
and entered - not a safety-vetted recommendation of what is safe to \
load or fire.

By using this app, you acknowledge that:

1. Reloading ammunition is inherently dangerous. Improper handling of \
gunpowder, primers, and components can result in severe injury, death, \
and property damage.

2. Loadscope analyzes data you provide, but is not a substitute for safe \
handloading practice. Always cross-reference every load against current \
published reloading manuals from powder, bullet, and cartridge \
manufacturers. Watch for pressure signs. Start below maximum loads and \
work up.

3. We have no control over your components, equipment, measurements, or \
how you use this app, and assume no responsibility for results obtained \
through its use. Computed scores and rankings are statistical analyses \
of your inputs, not load recommendations. No warranty is provided; \
Loadscope is provided "as is" without any warranty of accuracy, fitness \
for a particular purpose, or freedom from defects.

4. Predicted ballistic data is an ESTIMATE, not a measurement. When \
Loadscope displays a predicted DOPE, come-up, or wind table, those \
values are calculated by a ballistic model from the bullet, muzzle \
velocity, and atmospheric data you enter. The output is only as \
accurate as those inputs and carries inherent modeling error. \
Predicted values MUST be confirmed by live fire at known distances \
before you rely on them for any shot. Do not take a shot that matters \
based on predicted values you have not verified at the range.

5. The developer is not liable for any damage, injury, or loss \
resulting from use of this app or actions taken based on its analyses. \
This includes reliance on a suggested load, and reliance on predicted \
ballistic values that were not verified at the range.

6. You assume all risk associated with handloading and shooting.

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
