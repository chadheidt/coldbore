# Handling Bug Reports

A reference for what to do when a user reports something is "off" with Cold Bore — but it didn't crash.

For actual crashes (with Python tracebacks emailed via the in-app reporter), see `Handling Crash Reports.md` instead.

---

## What "non-crash" bugs look like

Bug reports without a crash usually come in vaguer:

- "The number on the Load Log doesn't match my chronograph"
- "I dropped my CSVs in but nothing happened"
- "The suggested charge is wrong"
- "I can't find my workbook anymore"
- "Excel won't open after import"

These are harder than crashes because there's no traceback. You have to ask questions to figure out what's actually going on.

---

## What to do (the easy path: come back to Claude)

1. **Open Cowork** and re-engage with the project. Use the magic phrase from `Notes for next session.md`.
2. **Paste the user's complaint** into chat verbatim.
3. Say: *"User reported this. Help me figure out what's going on."*
4. Claude will probably ask you to ask the user some clarifying questions before suggesting a fix. Pass the questions on, get answers, paste them back.
5. Once we know what's actually wrong, Claude fixes the code, writes a test, suggests a release.

---

## Information to gather from the user

When a user reports a bug, ask for these in your reply:

1. **What version of Cold Bore are they on?** Tools → About → version number. (Common — they're on an old version where the bug is already fixed.)
2. **What were they trying to do?** "I was importing my P3 powder ladder data" is more useful than "Cold Bore is broken."
3. **What did they expect to happen vs. what actually happened?** "I expected the charge to show 45.5 grains. Instead it showed 0.45 grains." That kind of detail is gold.
4. **The activity log.** The dark log area at the bottom of the Cold Bore window shows what happened during the import. Have them copy and paste that text into the email reply. (They can select text in the log area with the mouse.)
5. **A sample of the CSV (if it's an import bug).** Have them email the offending CSV file as an attachment.
6. **A screenshot of the workbook** if the issue is "the number on screen looks wrong."
7. **macOS version** if they think it might be system-related. (Apple menu → About This Mac.)

If you ask for all 7, you'll usually get 3 or 4. That's normally enough.

---

## Common non-crash bug patterns

| Symptom | Likely cause | What to ask |
|---|---|---|
| "Numbers are wrong" | Column-mismatch (we read the wrong cell from the workbook), or a label-vs-value cell confusion | Get a screenshot of the Load Log + the activity log |
| "Nothing happened when I dropped CSVs" | CSV file extension wrong (`.CSV` capital, or an extra `.txt`), OR Cold Bore wasn't running, OR the parser didn't recognize the format | Ask for the filename, the activity log, and have them try again with the app definitely open |
| "Suggested charge is wrong" | Could be a real scoring bug, or the user set their weights weirdly, or they shot a partial ladder so scoring is unstable | Ask: did they shoot all loads? What does the Charts tab show? Are the weights at default (30/20/20/30)? |
| "Excel won't open the workbook" | Workbook got corrupted or a previous import wrote weird data | Ask them to look in `.backups/` folder for the most recent backup before things went bad. The lockdown + backup-before-import we built saves the day here. |
| "My workbook disappeared" | They moved it, deleted it, or are looking in the wrong folder | Tools → Show Project Folder in Finder. Workbook should be there. If not, check Trash. |
| "Drag-on-icon doesn't work" | Their installed app might be an old version without `CFBundleDocumentTypes` (need v0.6.0+), OR macOS file association got reset | Tools → About should show v0.6.0+. If older, tell them to download the latest. |

---

## When you can't reproduce the bug

Sometimes you'll try the user's exact steps on your own Mac and everything works fine. Possibilities:

- Their data triggers an edge case yours doesn't. Ask for the exact CSV file.
- They have a different version of the app. Ask them to update.
- macOS quirk specific to their version (e.g., Apple Silicon vs Intel, Sequoia vs Sonoma).
- User error (gentle, polite verification — sometimes worth asking *"can you walk me through exactly what you did, step by step?"* — they often realize the mistake while typing it out).

If after digging you genuinely cannot reproduce or figure out the issue, it's OK to reply: *"I haven't been able to reproduce this on my end. If it happens again, please send me the full activity log and a sample CSV — that'll give me what I need."* Don't ship a speculative fix without understanding the root cause.

---

## "Bug" vs "feature request" — quick triage

Sometimes a "bug" is actually the user asking for a feature that doesn't exist:

- *"Cold Bore should track my barrel round count"* — not a bug, a feature request. Add to the future-ideas list in `Build progress.md`.
- *"It should auto-fill my DOPE chart from confirmed loads"* — also a feature, not a bug. (Already in the deferred list.)
- *"It should support LabRadar"* — feature request. We need a sample CSV, then it's ~30 min of work.

Reply to feature requests honestly: *"That's a great idea. I've added it to the list. Here's what I'd need from you to build it…"* Don't promise dates.

---

## Reply template (free to copy/adapt)

Here's a friendly reply skeleton when you're not sure yet what's going on:

---

> Hey [Name],
>
> Thanks for reaching out — sorry Cold Bore is acting up. To figure out what's happening I need a few things from you:
>
> 1. The version shown in **Tools → About** in Cold Bore.
> 2. A copy of the **activity log** — that's the dark text box at the bottom of the Cold Bore window. Click in it, Cmd+A to select all, Cmd+C to copy, and paste it into a reply email.
> 3. If this happened during an import, please attach the CSV file that triggered it.
> 4. Briefly walk me through what you were doing right before things went wrong.
>
> Once I have those I can usually diagnose it pretty quickly. Sorry for the hassle, and thanks for helping me make Cold Bore better.
>
> — Cold Bore Support

---

## After shipping the fix

- User gets the fix via the in-app update banner (auto-update)
- **Reply to the original thread** confirming the fix is live: *"Fixed in v0.6.1 — just released. Update via Tools → Check for Updates."*
- **Update release notes** mentioning the fix
- **Update the `tests/` suite** if applicable so the regression doesn't come back
