"""
Update checker + downloader.

Two responsibilities, two QThread classes:

  - UpdateChecker fetches a small JSON manifest from a URL specified in
    config.json (or the default), parses it, compares versions, signals
    whether a newer app/template is available. Cheap and runs at launch.

  - UpdateDownloader downloads the .zip referenced by the manifest's
    app_download_url to a temp file, with progress signals. Runs only when
    the user clicks "Install Update" in the banner.

Both run in QThreads so they can't block the UI on slow networks.
UpdateChecker failures are silent (no toast on a network glitch).
UpdateDownloader failures surface via signals so the banner can show
fallback text + a manual download link.

Manifest format (host this anywhere — GitHub Releases, Dropbox, S3, etc.):

    {
        "app_version": "0.5.0",
        "app_download_url": "https://github.com/.../releases/download/v0.6.0/ColdBore.zip",
        "app_release_notes": "Added charge weight scaling. Fixed bug X.",
        "template_version": "1.1",
        "template_download_url": "https://...",
        "template_release_notes": "Added new column on Load Log."
    }
"""

import json
import os
import tempfile
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


def resolve_download_url(manifest):
    """Given a parsed manifest dict, return the URL to download the update zip from.

    Two manifest formats are supported:

    1. **Gated (v0.11.0+):** the manifest contains `app_download_endpoint` and
       `app_download_file`. We POST the user's saved license key to the endpoint
       and the server (a Cloudflare Worker) returns a short-lived signed URL
       pointing at the file in R2.

    2. **Direct (legacy):** the manifest contains `app_download_url` — a plain
       public URL we download from directly.

    Returns the URL on success, or None on failure (no key stored, network error,
    server rejected the key).
    """
    endpoint = manifest.get("app_download_endpoint")
    if endpoint:
        file_name = manifest.get("app_download_file") or "Cold.Bore.zip"
        try:
            # Imported lazily so updater.py stays usable in environments where
            # config / file system access might not be set up yet.
            import config as app_config
            cfg = app_config.load_config()
        except Exception:
            return None

        license_key = cfg.get("license_key", "")
        if not license_key:
            return None

        try:
            payload = json.dumps({"code": license_key, "file": file_name}).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"ColdBore/{APP_VERSION}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            url = body.get("url")
            return url or None
        except Exception:
            return None

    # Legacy direct-URL manifest
    return manifest.get("app_download_url")


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


# Maximum size we'll download for an "update zip" before bailing out.
# A normal Cold Bore.zip is ~80 MB; 500 MB is a generous ceiling that catches
# misconfigured manifests pointing at runaway downloads (e.g. a directory listing
# served as a stream).
MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024


class UpdateDownloader(QThread):
    """Background thread that downloads a release zip with progress signals.

    Signals:
        progress(int, int): bytes_downloaded, total_bytes. total_bytes can
            be 0 if the server didn't send Content-Length — caller should
            treat that as "indeterminate progress."
        finished_with_result(dict): emitted once, with keys:
            ok (bool)
            error (str or None)
            file_path (str or None) — local path to the downloaded zip
            url (str) — the original download URL (for fallback / display)
    """

    progress = pyqtSignal(int, int)
    finished_with_result = pyqtSignal(dict)

    # Flush progress signals at most this often (in bytes downloaded since
    # last flush). 256 KB is fast enough to feel live without flooding the
    # event loop on a fast network.
    PROGRESS_FLUSH_BYTES = 256 * 1024

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self._cancelled = False

    def cancel(self):
        """Request that the in-progress download abort. The thread will
        notice on its next read loop iteration and emit a cancelled result."""
        self._cancelled = True

    def run(self):
        result = {
            "ok": False,
            "error": None,
            "file_path": None,
            "url": self.url,
        }

        if not self.url:
            result["error"] = "No download URL"
            self.finished_with_result.emit(result)
            return

        # Stream to a temp file we OWN — caller is responsible for moving
        # or deleting it once the install completes.
        tmp_fd, tmp_path = tempfile.mkstemp(prefix="ColdBoreUpdate_", suffix=".zip")
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": f"ColdBore/{APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                downloaded = 0
                last_flush = 0

                with os.fdopen(tmp_fd, "wb") as out:
                    tmp_fd = None  # ownership transferred to context
                    while True:
                        if self._cancelled:
                            result["error"] = "Cancelled"
                            self.finished_with_result.emit(result)
                            return

                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            break

                        out.write(chunk)
                        downloaded += len(chunk)

                        if downloaded > MAX_DOWNLOAD_BYTES:
                            result["error"] = (
                                f"Download exceeded {MAX_DOWNLOAD_BYTES // (1024*1024)} MB — "
                                "aborting. The manifest URL may be wrong."
                            )
                            self.finished_with_result.emit(result)
                            return

                        # Throttle progress signals so we're not flooding
                        # the event loop on fast networks.
                        if downloaded - last_flush >= self.PROGRESS_FLUSH_BYTES:
                            self.progress.emit(downloaded, total)
                            last_flush = downloaded

                # Final progress emit so the UI sees 100%
                self.progress.emit(downloaded, total or downloaded)

        except urllib.error.URLError as e:
            result["error"] = f"Network error: {e.reason}"
            self.finished_with_result.emit(result)
            return
        except OSError as e:
            result["error"] = f"Disk error while downloading: {e}"
            self.finished_with_result.emit(result)
            return
        finally:
            # If we never reassigned tmp_fd to None, the descriptor is
            # still open — close it so the temp file isn't held hostage.
            if tmp_fd is not None:
                try:
                    os.close(tmp_fd)
                except OSError:
                    pass

        result["ok"] = True
        result["file_path"] = tmp_path
        self.finished_with_result.emit(result)
