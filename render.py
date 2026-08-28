"""render.py — regenerate the .ics files, the HTML calendar and the session pages from plan.json.
Run from the folder containing plan.json and calendar_template.html:
    python3 render.py
Outputs (same folder): marathon-2027.ics (the subscribed file), marathon-2027-base.ics, marathon-2027-block.ics, marathon-2027-calendar.html, sessions/*.html
Week totals are recomputed from the sessions, so editing a session's km in plan.json is enough.
Session pages come from exercises.json + session_template.html; any problem there degrades to
"no guide links" with a warning — it never fails the run (the weekly routine depends on that).
"""
import html as html_mod
import json, datetime as dt, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
SITE = "https://sapoola.github.io/marathon-2027/"
out = json.load(open("plan.json"))
sessions = out["sessions"]; weeks = out["weeks"]
START = dt.date.fromisoformat(out["start"])

# recompute week totals from sessions
def km_of(s):
    k = float(s.get("km") or 0)
    return 0 if k == 42.2 else k   # race day itself isn't counted in the week total
for i, w in enumerate(weeks):
    mon = START + dt.timedelta(weeks=i); sun = mon + dt.timedelta(days=6)
    tot = sum(km_of(s) for s in sessions if mon.isoformat() <= s["date"] <= sun.isoformat() and s["sport"] in ("run","race"))
    w["run_km"] = round(tot, 1); w["monday"] = mon.isoformat()

# ---------------------------------------------------------------- session pages (gym / mobility guides)
# PAGES maps session id -> relative page path. Kept separate from the session dicts on purpose:
# plan.json is dumped back at the end of this script, so injecting fields into the sessions
# would leak into the source of truth and into what the weekly routine diffs.
DOW_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MON_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def fmt_day(d):
    return f"{d.day} {MON_ABBR[d.month - 1]}"

def watch_url(vid):
    t = f"&t={vid['start']}s" if vid.get("start") else ""
    return f"https://www.youtube.com/watch?v={vid['id']}{t}"

def embed_url(vid):
    s = f"?start={vid['start']}" if vid.get("start") else ""
    return f"https://www.youtube-nocookie.com/embed/{vid['id']}{s}"

def exercise_cards(variant, videos):
    parts = []
    for ex in variant.get("exercises", []):
        keys = ex.get("videos", [])
        blocks = []
        for key in keys:
            vid = videos.get(key)
            if vid is None:
                print(f"warning: exercises.json: video {key!r} (variant {variant['slug']}) not in the video map; skipping it", file=sys.stderr)
                continue
            label = "Technique video" if len(keys) == 1 else f"Technique video — {html_mod.escape(key)}"
            yt = f'<a class="yt" href="{html_mod.escape(watch_url(vid))}" target="_blank" rel="noopener">Watch on YouTube</a>'
            if vid.get("embed", True):
                blocks.append(f'    <details class="vid"><summary>{label}</summary>\n'
                              f'      <div class="frame" data-embed="{html_mod.escape(embed_url(vid))}"></div>\n'
                              f'      {yt}\n    </details>')
            else:
                blocks.append(f'    <details class="vid"><summary>{label}</summary>\n      {yt}\n    </details>')
        parts.append('  <article class="ex">\n'
                     f'    <h2>{html_mod.escape(ex["name"])}</h2>\n'
                     f'    <div class="sets">{html_mod.escape(ex["sets"])}</div>\n'
                     + ("\n".join(blocks) + "\n" if blocks else "")
                     + '  </article>')
    return "\n".join(parts)

def build_session_pages():
    """Match gym/mobility sessions to exercises.json variants and write sessions/<slug>.html.
    Returns {session id: relative page path}. Never raises: any problem is a warning and the
    affected links are simply skipped — the weekly routine must never be broken by this feature."""
    try:
        ex_data = json.load(open("exercises.json"))
        page_tpl = open("session_template.html").read()
        videos = ex_data["videos"]; variants = ex_data["variants"]
        groups = {}   # slug -> list of sessions
        pages = {}    # session id -> relative path
        for s in sessions:
            if s["sport"] not in ("gym", "mobility"):
                continue
            hit = None
            for v in variants:
                m = v["match"]
                if s["sport"] == m["sport"] and s["title"] == m["title"] and m.get("detail_contains", "") in s["detail"]:
                    hit = v; break
            if hit is None:
                print(f"warning: no exercises.json variant matches session {s['id']} ({s['title']!r}); no guide link for it", file=sys.stderr)
                continue
            groups.setdefault(hit["slug"], []).append(s)
            pages[s["id"]] = f"sessions/{hit['slug']}.html"
        os.makedirs("sessions", exist_ok=True)
        phase_of = {w["label"]: w["phase"] for w in weeks}
        for v in variants:
            ss = groups.get(v["slug"])
            if not ss:
                print(f"warning: exercises.json variant {v['slug']!r} matches no session; page not written", file=sys.stderr)
                continue
            ss = sorted(ss, key=lambda s: s["date"])
            dates = [dt.date.fromisoformat(s["date"]) for s in ss]
            days = list(dict.fromkeys(DOW_ABBR[d.weekday()] for d in dates))
            times = list(dict.fromkeys(s["time"] for s in ss))
            mins = list(dict.fromkeys(str(s["mins"]) for s in ss))
            sport = "Gym" if ss[0]["sport"] == "gym" else "Mobility"
            phases = list(dict.fromkeys(phase_of[s["week"]] for s in ss if s["week"] in phase_of))
            phase_txt = phases[0] if len(phases) == 1 else (f"{phases[0]}–{phases[-1]}" if phases else "")
            rng = fmt_day(dates[0]) if dates[0] == dates[-1] else f"{fmt_day(dates[0])} – {fmt_day(dates[-1])}"
            meta = f"{'/'.join(days)} {'/'.join(times)} · ~{'/'.join(mins)} min · {sport}"
            rng_txt = f"{phase_txt}, {rng}" if phase_txt else rng
            page = (page_tpl
                    .replace("__TITLE__", html_mod.escape(ss[0]["title"]))
                    .replace("__ACCENT__", "var(--gym)" if ss[0]["sport"] == "gym" else "var(--mob)")
                    .replace("__META__", html_mod.escape(meta))
                    .replace("__RANGE__", html_mod.escape(rng_txt))
                    .replace("__EXERCISES__", exercise_cards(v, videos))
                    .replace("__NOTES__", html_mod.escape(ss[0]["detail"])))
            open(os.path.join("sessions", f"{v['slug']}.html"), "w").write(page)
        return pages
    except Exception as e:
        print(f"warning: session pages skipped ({e.__class__.__name__}: {e}); calendar and .ics still render without guide links", file=sys.stderr)
        return {}

PAGES = build_session_pages()
# ---------------------------------------------------------------- ICS
def ics_escape(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def fold(line):
    out = []
    b = line.encode("utf-8")
    while len(b) > 73:
        cut = 73
        while (b[cut] & 0xC0) == 0x80: cut -= 1
        out.append(b[:cut].decode("utf-8")); b = b" " + b[cut:]
    out.append(b.decode("utf-8"))
    return "\r\n".join(out)

SPORT_EMOJI = {"run": "🏃", "bike": "🚴", "gym": "🏋️", "mobility": "🧘", "swim": "🏊", "race": "🏁"}

def make_ics(sess, weeks_sel, name):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//marathon-2027 plan//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{name}", "X-WR-TIMEZONE:Europe/Amsterdam"]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for s in sess:
        d = dt.date.fromisoformat(s["date"]); hh, mm = map(int, s["time"].split(":"))
        st = dt.datetime(d.year, d.month, d.day, hh, mm); en = st + dt.timedelta(minutes=s["mins"])
        title = f"{SPORT_EMOJI[s['sport']]} {s['title']}" + (" (optional)" if s["optional"] and "ptional" not in s["title"] else "")
        desc = f"Week {s['week']}\n\n{s['detail']}"
        guide = SITE + PAGES[s["id"]] if s["id"] in PAGES else None
        if guide:
            desc += f"\n\nGuide: {guide}"
        lines += ["BEGIN:VEVENT", f"UID:{s['id']}@marathon2027", f"DTSTAMP:{now}",
                  f"DTSTART:{st.strftime('%Y%m%dT%H%M%S')}", f"DTEND:{en.strftime('%Y%m%dT%H%M%S')}",
                  f"SUMMARY:{ics_escape(title)}", f"DESCRIPTION:{ics_escape(desc)}", f"CATEGORIES:{s['sport']}"]
        if guide:
            lines.append(f"URL:{guide}")
        lines.append("END:VEVENT")
    for w in weeks_sel:
        d = dt.date.fromisoformat(w["monday"])
        summ = f"Week {w['label']} · {w['phase']} · run {w['run_km']:g} km · bike ~{w['bike_h']} h" + (" · cutback" if w["cutback"] else "") + ("".join(" · " + k for k in w["key"]))
        lines += ["BEGIN:VEVENT", f"UID:week-{w['label']}@marathon2027", f"DTSTAMP:{now}",
                  f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(d+dt.timedelta(days=1)).strftime('%Y%m%d')}",
                  f"SUMMARY:{ics_escape(summ)}", f"DESCRIPTION:{ics_escape(w['notes'])}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"

base_weeks = [w for w in weeks if w["phase"] == "Base"]
block_weeks = [w for w in weeks if w["phase"] != "Base"]
cut = dt.date(2026, 10, 19)
base_s = [s for s in sessions if dt.date.fromisoformat(s["date"]) < cut]
block_s = [s for s in sessions if dt.date.fromisoformat(s["date"]) >= cut]
open("marathon-2027-base.ics", "w").write(make_ics(base_s, base_weeks, "Marathon 2027"))
open("marathon-2027-block.ics", "w").write(make_ics(block_s, block_weeks, "Marathon 2027"))
open("marathon-2027.ics", "w").write(make_ics(sessions, weeks, "Marathon 2027"))

# ---------------------------------------------------------------- HTML
tpl = open("calendar_template.html").read()
html_out = tpl.replace("/*__DATA__*/", "const PLAN = " + json.dumps(out, ensure_ascii=False) + ";\nconst PAGES = " + json.dumps(PAGES) + ";")
open("marathon-2027-calendar.html", "w").write(html_out)


json.dump(out, open("plan.json", "w"), indent=1, ensure_ascii=False)
print("rendered", len(sessions), "sessions;", len(PAGES), "with a session page")
