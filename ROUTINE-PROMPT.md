# Monday routine — prompt for the Claude Code cloud Routine

Create at claude.ai/code/routines (or `/schedule` in Claude Code). Repository: `sapoola/marathon-2027`. Connector: Strava. Trigger: weekly, Monday 06:00 Europe/Amsterdam. Paste the block below as the routine's prompt.

---

You are running the weekly marathon-plan review in the repo `sapoola/marathon-2027`. Be conservative, follow `ADJUSTMENT-RULES.md` exactly, and keep the brief short.

CONTEXT
- `plan.json` is the source of truth; `render.py` regenerates the calendar files; `ADJUSTMENT-RULES.md` says how to adjust. Read all three first.
- Race: Sunday 21 February 2027. Goals A 3:40 / B 3:45 / C 3:55. Fixed dates that never move: 5k TT 17 Oct, 70.3 13 Dec, half 17 Jan, race 21 Feb.
- The athlete is a strong cyclist (FTP 320 W, 82 kg) rebuilding running from a low base. Injury avoidance beats every other consideration.

STEPS
1. Work out last week (Monday–Sunday, Europe/Amsterdam) and the coming week from today's date.
2. Strava: list all activities for last week. For each run: distance, moving time, average HR, title, description. For each ride: moving time and average HR or relative effort. Note any other sport.
3. From `plan.json`, take last week's planned sessions and the coming week's. Compute the inputs in section 1 of the rules (completion ratio, long run done, quality done, bike hours vs cap, easy-run HR, injury words).
4. If the most recent file in `briefs/` contains a `## Garmin reply` section (the athlete adds it by hand), use those numbers as recovery inputs; otherwise treat them as absent.
5. Apply the rules in section 2, in order. Record which rules fired and why. If none fire, the coming week is unchanged.
6. If anything changed: edit `plan.json` exactly as section 3 describes (same session `id`; km and title updated; reason prepended to `detail`; week `notes` appended). Run `python3 render.py`. Confirm `marathon-2027.ics` and `marathon-2027-calendar.html` regenerated.
7. Write the brief per section 4 of the rules (under 200 words) to `briefs/YYYY-MM-DD.md`, with a table of last week's runs (date, planned vs actual km, avg HR) below it, then a `## Garmin reply` heading with four empty lines (HRV status / readiness / sleep / RHR) for the athlete to fill in.
8. Commit everything to `main` with the message `weekly review YYYY-MM-DD: <no changes | what changed>` and push. No pull request — commit directly. Before committing, run `git config user.name "sapoola" && git config user.email "177226958+sapoola@users.noreply.github.com"`. Do not add any Co-Authored-By trailer or AI-attribution line to the commit message.
9. Never: add volume, change paces, touch fixed dates, alter taper weeks (W16+), edit past sessions, make a cutback week harder, or edit `render.py` / `calendar_template.html` / `ADJUSTMENT-RULES.md`. If the data looks wrong (Strava returned nothing, plan.json won't parse, render.py fails), make no changes, still write the brief saying so, commit that, and stop.

OUTPUT
The brief text, then one line listing files changed.
