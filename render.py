"""render.py — regenerate the .ics files and the HTML calendar from plan.json.
Run from the folder containing plan.json and calendar_template.html:
    python3 render.py
Outputs (same folder): marathon-2027.ics (the subscribed file), marathon-2027-base.ics, marathon-2027-block.ics, marathon-2027-calendar.html
Week totals are recomputed from the sessions, so editing a session's km in plan.json is enough.
"""
import json, datetime as dt, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
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
        lines += ["BEGIN:VEVENT", f"UID:{s['id']}@marathon2027", f"DTSTAMP:{now}",
                  f"DTSTART:{st.strftime('%Y%m%dT%H%M%S')}", f"DTEND:{en.strftime('%Y%m%dT%H%M%S')}",
                  f"SUMMARY:{ics_escape(title)}", f"DESCRIPTION:{ics_escape(desc)}", f"CATEGORIES:{s['sport']}", "END:VEVENT"]
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
html_out = tpl.replace("/*__DATA__*/", "const PLAN = " + json.dumps(out, ensure_ascii=False) + ";")
open("marathon-2027-calendar.html", "w").write(html_out)


json.dump(out, open("plan.json", "w"), indent=1, ensure_ascii=False)
print("rendered", len(sessions), "sessions")
