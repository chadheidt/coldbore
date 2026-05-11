# tools/

Helper scripts that aren't part of the shipped Loadscope app, but are useful
for the project (regenerating landing-page images, etc.).

## Files

### `render_workbook.py`

Generates `docs/assets/workbook.png` — the Load Log hero image on the landing
page. Renders programmatically via Pillow rather than screen-capturing Excel,
which avoids macOS Screen Recording permission and Spaces issues. The 7 SAUM
ladder data and the composite scoring values are baked in.

```
python3 tools/render_workbook.py
cp ~/Desktop/workbook.png docs/assets/workbook.png
```

To update what's shown (different cartridge, different ladder, etc.), edit the
`rows` list inside `render_workbook.py` and re-run.

### `render_loadscope.py`

Generates `docs/assets/screenshot.png` — the Loadscope window mockup on the
landing page. Hand-painted reticle + MOA grid + center spotlight + title/
subtitle in the drop zone, plus workbook picker and activity log. Matches the
production drop zone's visual design (see `app/main.py:DropZone.paintEvent`).

```
python3 tools/render_loadscope.py
cp ~/Desktop/screenshot.png docs/assets/screenshot.png
```

If the in-app drop zone visual is changed in `app/main.py` or `app/theme.py`,
update this script in lockstep so the marketing image stays accurate.

## Dependencies

Both scripts need `Pillow` (PIL):
```
python3 -m pip install --user Pillow
```

## Why programmatic rendering instead of real screenshots?

The 2026-05-10 attempt to screencapture Excel and the Loadscope app from a
Bash tool subprocess hit three macOS hurdles in sequence: cross-Space windows
not visible to the capture, Screen Recording TCC permission for the calling
process, and focus bouncing back to the parent app between activate-and-capture
calls. Programmatic rendering bypasses all of that and produces deterministic,
re-runnable images that don't depend on Excel state or chrome.
