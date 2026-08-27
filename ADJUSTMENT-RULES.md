# Adjustment rules — Monday routine

These rules decide how the plan changes each Monday based on last week's Strava data (and Garmin numbers if the athlete supplied them). They are deliberately conservative and deterministic. The routine applies them; it does not improvise.

## 0. Things the routine never does
- Never adds volume or intensity beyond what `plan.json` already says. It only holds, reduces, or flags.
- Never moves or alters the fixed dates: 5k TT (Sat 17 Oct), 70.3 (Sun 13 Dec), half (Sun 17 Jan), race (Sun 21 Feb).
- Never makes a cutback or recovery week harder (B5, B8, W4, W9, W13).
- Never changes anything from W16 onward (taper + race week) — it only flags.
- Never re-sets training paces. Pace changes happen in a chat with Claude after the 5k TT and the half.
- Never edits sessions in the past. Only the coming week (and, where a rule says so, the long-run progression after it).
- Never changes session times or the gym/mobility content. Load rules apply to running distance and bike hours only; gym changes are flags.

## 1. Inputs to compute (last Mon–Sun, from Strava)
- `run_planned`: sum of km for planned run sessions last week, **excluding** ones marked `optional`.
- `run_actual`: km of all Strava runs last week.
- `R = run_actual / run_planned` (completion ratio).
- `long_done`: true if the longest run last week ≥ 85% of the planned Saturday long run km.
- `quality_done`: true if a run exists on Wed (±1 day) with ≥ 70% of the planned Wednesday session's km.
- `bike_hours`: total moving time of rides last week (all rides, trainer included).
- `bike_cap`: that week's cap from the phase table (Base 7 h, Build 5.5 h, Specific 4 h, Taper 3 h; W8 = 70.3 week, W9 = 3 h).
- `easy_hr_high`: count of planned easy runs (Mon, Tue-optional, Thu-in-B1) where average HR > 150.
- `injury_signal`: any run last week whose Strava title or description contains pain / niggle / sore / tight / calf / achilles / hamstring / knee / shin / cut short / limp, OR a planned run that was stopped at < 50% of its distance with no other explanation.
- Optional Garmin inputs, if the athlete replied to the previous brief: `hrv_status` (balanced / unbalanced / low), `readiness` (0–100, 7-day avg), `sleep` (0–100, 7-day avg), `rhr`.

## 2. Rules — apply in this order, first match on each row wins

### 2.1 Injury / illness
- If `injury_signal` → coming week: Wednesday quality becomes an easy run of the same km + strides; Saturday long run −30%; add a note to both sessions saying why. Brief asks what happened. Do not touch any later week.
- If `R < 0.3` and no runs at all for ≥ 5 days → assume illness/travel. Coming week becomes a rebuild: Monday easy 5 km, Wednesday easy 6 km + strides, Saturday long = 60% of the planned long run. Brief asks. Do not touch later weeks.

### 2.2 Completion
- If `R ≥ 0.85` and `long_done` → coming week as planned.
- If `0.6 ≤ R < 0.85` or `long_done` is false → coming week's Saturday long run = last week's planned long run distance (i.e. repeat, don't progress). Everything else as planned. Note on the session: "held — last week's long run was N km short / missed".
- If `R < 0.6` (and 2.1 didn't fire) → coming week: long run = max(longest run actually done last week, 60% of coming week's planned long run); Wednesday quality becomes easy + strides. Later weeks untouched.
- Two consecutive weeks with `R < 0.6` → apply the rule above AND flag in bold at the top of the brief: "Two low weeks — the peak long run (32 km, 23 Jan) may need to come down to 30. Talk to Claude before W12."

### 2.3 Progression sanity (after 2.2, only if the coming week was left "as planned")
- If the coming week's long run is more than 3 km longer than the longest run actually completed in the last 14 days → cap it at that +3 km. Note: "capped — progression from what you actually ran".
- If coming week `run_planned` > 1.12 × last week's `run_actual` (excluding cutback→build transitions, and excluding weeks where `run_actual` < 60% of its own plan) → reduce the Monday easy run until it fits; if still over, reduce the Wednesday session's warm-up/cool-down (never the reps). Long run is last to be touched.

### 2.4 Bike creep
- If `bike_hours > 1.25 × bike_cap` → coming week's Saturday long run −20%. Note on the session and a line in the brief with the actual hours vs cap. This fires **in addition** to 2.2.
- If `bike_hours > 1.5 × bike_cap` in two consecutive weeks → brief in bold: "Cycling is above the cap two weeks running; the marathon and the bike are now competing. Decide which one wins this block."
- Thursday ride not Z2 (avg HR > 150 or Strava relative effort > 40) in the Build phase or later → flag only, no change.

### 2.5 Easy running too hard
- `easy_hr_high ≥ 2` → no distance change. Prepend to every easy run in the coming week: "HR under 145 — last week N easy runs averaged >150."

### 2.6 Garmin recovery (only if the athlete supplied numbers)
- `hrv_status` = low, OR `readiness` < 40, OR `sleep` < 60 → coming week: Wednesday quality becomes easy + strides; long run held at last week's distance (no progression). Note why.
- `hrv_status` = unbalanced OR `readiness` 40–55 → keep the plan, but shorten Wednesday to reps −1 (e.g. 5×800 → 4×800) and add a note. Long run unchanged.
- Otherwise no change.
- If recovery rules and completion rules both reduce the same session, apply the larger reduction once — don't stack.

### 2.7 Cutback / recovery weeks
- If the coming week is a cutback (B5, B8, W4, W9, W13) → only 2.1 and 2.4 apply. Never reduce a cutback week for completion reasons (it's already the reduction).

## 3. How to write the change into plan.json
- Find the session by `date` + `sport`. Edit `km`, and edit the number in `title` to match (e.g. "Long run 24 km" → "Long run 20 km"). Keep `id` unchanged so the calendar event updates in place rather than duplicating.
- Prepend the reason to `detail` as a first line: `ADJUSTED (date): <reason>.` then a blank line, then the original detail.
- If a quality session becomes easy: change `kind` to "easy", `title` to "Easy run N km + strides", `detail` to the standard easy-run text with the reason prepended.
- Append one line to the week's `notes`: `<date>: <what changed>`.
- Then run `python3 render.py`. It recomputes week totals and rewrites the .ics and the HTML.
- Overwrite `marathon-2027.ics` with the new `marathon-2027-full.ics` **in place** (same Drive file, new content — never delete-and-recreate, or the subscription link breaks).

## 4. The Monday brief (what the athlete reads)
Under 200 words, plain text, in this order:
1. Last week in one line: run km actual vs planned, long run done or not, bike hours vs cap.
2. What changed in the coming week and which rule did it (or "no changes").
3. Flags (bike creep, easy HR, injury words, two-low-weeks).
4. The coming week's key session(s) in one line each.
5. If Garmin numbers would change the decision: "Reply with HRV status / readiness / sleep / RHR and I'll re-run."
No praise, no motivation, no restating the whole week.
