"""
Update checker.

On launch (and on demand from a menu item), the app fetches a small JSON
manifest from a URL specified in config.json. If the manifest's app_version
is newer than this build, the main window shows a dismissable banner with a
button to open the download URL in the user's browser.

Manifest format (host this anywhere — GitHub Releases, Dropbox, S3, etc.):

    {
        "app_version": "0.5.0",
        "app_download_url": "https://github.com/.../releases/download/v0.6.0/ColdBore.zip",
        "app_release_notes": "Added charge weight scaling. Fixed bug X.",
        "template_version": "1.1",
        "template_download_url": "https://...",
        "template_release_notes": "Added new column on Load Log."
    }

The check runs in a QThread so it can't block the UI on slow networks or
unreachable hosts. Failures are silent — we don't pester the user about a
network glitch.
"""

import json
import urllib.request
import urllib.error

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from version import APP_VERSION, TEMPLATE_VERSION, is_newer


REQUEST_TIMEOUT_SECONDS = 8

# Default manifest URL — baked in so update-checking works out of the box for
# everyone (Chad and friends), no per-user config required. Users can still
# override this by setting "update_manifest_url" in their config.json.
DEFAULT_MANIFEST_URL = (
    "https://raw.githubusercontent.com/chadheidt/coldbore/main/manifest.json"
)


class UpdateChecker(QThread):
    """Background thread that fetches the manifest and signals the result.

    Signals:
        finished_with_result(dict): emitted on every check, with keys:
            ok (bool)
            error (str or None)
            manifest (dict or None)
            app_update (bool) — True if a newer app is available
            template_update (bool) — True if a newer template is available
    """

    finished_with_result = pyqtSignal(dict)

    def __init__(self, manifest_url, parent=None):
        super().__init__(parent)
        self.manifest_url = manifest_url

    def run(self):
        result = {
            "ok": False,
            "error": None,
            "manifest": None,
            "app_update": False,
            "template_update": False,
        }

        if not self.manifest_url:
            result["error"] = "No manifest URL configured"
            self.finished_with_result.emit(result)
            return

        try:
            req = urllib.request.Request(
                self.manifest_url,
                headers={"User-Agent": f"ColdBore/{APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                raw_bytes = resp.read()
            # utf-8-sig strips a leading BOM if present (some web hosts add one)
            raw = raw_bytes.decode("utf-8-sig").strip()
            if not raw:
                result["error"] = "Manifest URL returned empty response"
                self.finished_with_result.emit(result)
                return
            # Quick sanity check — if response starts with HTML, the URL is
            # probably wrong (e.g., a 404 page or a GitHub blob view instead
            # of the raw file). Give a clearer error.
            if raw.lstrip().startswith(("<", "<!")):
                result["error"] = (
                    "Manifest URL returned HTML, not JSON. "
                    "The URL may be wrong (use the raw.githubusercontent.com URL, "
                    "not the github.com/.../blob/... one)."
                )
                self.finished_with_result.emit(result)
                return
            manifest = json.loads(raw)
        except urllib.error.URLError as e:
            result["error"] = f"Network error: {e.reason}"
            self.finished_with_result.emit(result)
            return
        except (json.JSONDecodeError, OSError) as e:
            result["error"] = f"Couldn't parse manifest: {e}"
            self.finished_with_result.emit(result)
            return

        result["ok"] = True
        result["manifest"] = manifest
        result["app_update"] = is_newer(manifest.get("app_version"), APP_VERSION)
        result["template_update"] = is_newer(
            manifest.get("template_version"), TEMPLATE_VERSION
        )
        self.finished_with_result.emit(result)
