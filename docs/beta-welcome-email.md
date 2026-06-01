# Beta welcome email — copy template

**Use this as the body of a personal email when inviting a friend to the Loadscope beta.** Fill in the four `{{ }}` placeholders, paste into Gmail / Mail.app, send.

---

## Subject line options (pick one)

- `Loadscope beta — access code inside`
- `{{ FRIEND_FIRST_NAME }}, your Loadscope beta code`
- `Try Loadscope — your beta access (Mac or Windows)`

---

## Email body

Hey {{ FRIEND_FIRST_NAME }},

You're in. Here's your Loadscope beta access code:

**`{{ ACCESS_CODE }}`**

It unlocks both the download and the app itself.

**To install:**

1. Open [loadscope.app](https://loadscope.app) on your Mac or Windows PC.
2. Click the orange **Download** button at the top.
3. Click **I have a code**, paste the code above. The installer for your platform will download — `Loadscope.dmg` on Mac (~80 MB) or `Loadscope-Setup.exe` on Windows (~40 MB).
4. **Mac:** open the disk image, drag **Loadscope** onto the Applications shortcut, eject the disk image. Open Loadscope from your Applications folder — macOS opens it without any warning (signed and notarized by Apple).
   **Windows:** double-click `Loadscope-Setup.exe`. On the first launch, Windows SmartScreen will show a blue warning — click **More info → Run anyway**. (Windows code-signing is in progress; the warning goes away once the certificate lands.) Click **Next** through the wizard.
5. On first launch, paste your code one more time in the license dialog. Click through the disclaimer, accept the default folder, and you'll land on the Rifle & Setup screen.

**Quick orientation:**

The welcome tour that auto-runs is the fastest way to see the workflow. About 90 seconds. The Help (?) link bottom-left of the sidebar opens the illustrated User Guide PDF if you want a deeper walkthrough later.

**What I want from you as a beta tester:**

- **Use it on a real load development cycle.** Drop your Garmin Xero / LabRadar / BallisticX / OnTarget / Silver Mountain / ShotMarker CSVs, run the import, look at the Results panel. Save a winning load to Library. Print a Load Card.
- **If you shoot a MagnetoSpeed or Athlon Rangecraft, I especially want to hear from you.** Those two are brand-new and marked **experimental** in the app — they import, but I haven't confirmed them against a real file yet. Run your export through, then reply and tell me whether the velocities and stats matched what the device showed — and attach the file if you can. That's the last step to take the "experimental" tag off.
- **Tell me what's confusing.** Wording, layout, anything that made you pause. I want the rough edges before this opens up.
- **Tell me what's missing.** Different chronograph? Different target app? Email a sample export to `support@loadscope.app` and I'll add support.
- **Bugs go to `support@loadscope.app`** with a quick description and (if it's a parse issue) the file that broke it.

**Heads-up:**

- **Mac:** macOS 10.13 or later. Runs natively on Intel; via Rosetta 2 on Apple Silicon.
- **Windows:** Windows 10 or 11, 64-bit.
- Updates land as a banner at the top of the window — one click installs.
- Loadscope writes to a regular `.xlsx` file on your computer. No cloud, no account, no telemetry. Workbooks are yours; uninstall whenever, your data stays.
- It's free during beta.

Anything you need from me, just hit reply.

Thanks for jumping in,
Chad

---

## How to send (the mechanism)

When you have a list of friends to invite, the simplest path is **manual personal sends** — one email per friend, code per friend. It feels more like an invitation, less like a mailshot. Pace:

**Step 1. Pick the code for each friend.**

Open `app/license.py`. The hardcoded `VALID_KEYS` frozenset has 10 beta slots (excluding your own `CBORE-DDCX-AEGK-J2FR-2SIB`). Assign one slot per friend and note who got which — that's how you'll know whose install is whose if a bug report comes in. I recommend adding the friend's first name as a comment next to the slot, like:

```python
"CBORE-4O4I-YXZR-3VZL-XE74",  # beta slot 1 — assigned to Mike (2026-05-28)
```

If you want more than 10 slots, ask me — generating new keys + adding them to `VALID_KEYS` is a one-line change + a quick local rebuild + a v0.16.x bump.

**Step 2. Send the email.**

Open Gmail (or Apple Mail). New compose. Fill in the placeholders from the template above. Send.

That's it. The friend pastes the code at loadscope.app, downloads, installs, runs.

**If you want to send a batch automatically** (10+ friends, all at once), let me know and I'll write a small Python script that:
1. Reads a CSV of `(first_name, email, beta_slot_index)`
2. Sends the welcome email to each via the Cloudflare Worker's Resend integration (the same one used by `/approve`)
3. Logs each assignment to a local file so you have a record

For now, manual sends are cleaner — beta is a small list and personal touch matters.

---

## After the friend installs

Their first launch hits the app's `/verify` Worker endpoint to check the code is active. If the code's in `VALID_KEYS`, validation is instant + offline. If you ever need to **revoke** a key (returned the app, beta ended, problem user), edit `app/license.py` to remove it from `VALID_KEYS`, ship the next version, and the next time the app starts the friend will see a "license invalid" message. (Until they update they'll keep working — the local cache only re-checks on next launch after the new version installs.)
