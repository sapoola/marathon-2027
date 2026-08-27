# Setup — GitHub version (replaces the Google Drive setup)

## 1. Create the repo (2 minutes)
On github.com: New repository → owner **sapoola**, name **marathon-2027**, **Public** (the raw file URL iCloud fetches only works without a token on a public repo — the content is a training plan, nothing sensitive), no README (we have one). Create.

Then from a terminal, in the unzipped folder:

    git init
    git add .
    git commit -m "initial plan"
    git branch -M main
    git remote add origin https://github.com/sapoola/marathon-2027.git
    git push -u origin main

Or, without a terminal: on the empty repo page choose "uploading an existing file" and drag the whole folder contents in (including the `briefs` folder).

## 2. Subscribe in iCloud (1 minute)
Mac: Calendar → File → New Calendar Subscription → paste

    webcal://raw.githubusercontent.com/sapoola/marathon-2027/main/marathon-2027.ics

→ Subscribe. Name "Marathon 2027", Location **iCloud**, Auto-refresh **Every hour**. Done — you never import again.
(iPhone alternative: Settings → Apps → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar → paste the URL.)

## 3. GitHub Pages for the phone calendar (1 minute, optional)
Repo → Settings → Pages → Source: "Deploy from a branch", Branch: `main`, folder `/ (root)` → Save. A minute later the calendar is live at

    https://sapoola.github.io/marathon-2027/marathon-2027-calendar.html

Open it in Safari on the phone → Share → Add to Home Screen. It's always the current version — no re-adding after changes.

## 4. The Monday routine (5 minutes)
Go to claude.ai/code/routines → New routine. Repository: `sapoola/marathon-2027`. Connectors: Strava. Schedule: weekly, Monday, 06:00 Europe/Amsterdam. Prompt: the block in `ROUTINE-PROMPT.md`. Save, then **Run now** once and check:
- a new file appears in `briefs/`
- `plan.json` changed only where a rule fired (probably nowhere on a first run)
- the commit shows on `main`
- the calendar in iCloud still shows this week (it will refresh within the hour)

Cloud Routines need a Pro/Max/Team plan with Claude Code on the web enabled. If you'd rather use Cowork's scheduled tasks, the same prompt works there provided a GitHub connector is available to it; without one, Cowork can't commit and the Drive version with manual "upload new version" is the fallback.

## 5. Garmin numbers (optional, weekly)
Open the latest file in `briefs/` on GitHub, fill in the four lines under `## Garmin reply` (HRV status, 7-day readiness, 7-day sleep score, resting HR), commit. The next Monday run reads them.

## What stays in chat with Claude
Pace re-sets after the 5k TT (17 Oct) and the half (17 Jan); anything a brief flags in bold.
