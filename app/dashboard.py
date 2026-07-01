"""
Internal dashboard generator. Deterministic, no LLM. Reads the database and
renders the Aithical-styled HTML dashboard. Shows EVERYTHING - this is the
internal operating view for Tina and Jay. Never sent to the client.
"""
from datetime import datetime, timedelta, timezone
from . import db
from .rules import AI_VISIBILITY_BASELINE, AI_VISIBILITY_TARGET

STATUS_LABEL = {
    "to_do": "To Do",
    "in_progress": "In Progress",
    "completed": "Completed",
    "on_hold_client": "On Hold - Client",
    "on_hold_internal": "On Hold - Internal",
}
STATUS_PILL = {
    "to_do": "todo", "in_progress": "prog", "completed": "done",
    "on_hold_client": "holdc", "on_hold_internal": "holdi",
}


def _rows(tasks, cols):
    out = []
    for t in tasks:
        cells = "".join(f"<td>{c}</td>" for c in cols(t))
        out.append(f"<tr>{cells}</tr>")
    return "".join(out)


def render_dashboard() -> str:
    tasks = db.list_tasks()
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    completed_week = db.completed_since(week_start)

    counts = {k: 0 for k in STATUS_LABEL}
    for t in tasks:
        counts[t["status"]] = counts.get(t["status"], 0) + 1

    by = lambda s: [t for t in tasks if t["status"] == s]

    def status_pill(t):
        return f'<span class="pill {STATUS_PILL[t["status"]]}">{STATUS_LABEL[t["status"]]}</span>'

    def flag(t):
        f = ""
        if t["internal_blocked"]:
            f = '<span class="flag">INTERNALLY BLOCKED</span>'
        return f

    inprog = by("in_progress")
    holdc = by("on_hold_client")
    holdi = by("on_hold_internal")
    todo = by("to_do")
    done = by("completed")

    ring_pct = int(AI_VISIBILITY_BASELINE)  # 36

    # compliance watch: any task whose blocker_note mentions a live defect
    defects = [t for t in tasks if t["blocker_note"] and "LIVE" in (t["blocker_note"] or "").upper()]

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RegenesisMD - Weekly Internal Dashboard</title>
<style>
:root{{--cream:#F5F2EC;--charcoal:#1C1C1E;--gold:#B8A06A;--sage:#8A9E8C;--sand:#C9B99A;--white:#FAF8F5;--line:#E4DED3;--muted:#6B6659;--blocked:#B5544A}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--cream);color:var(--charcoal);font-family:'DM Sans',-apple-system,Segoe UI,sans-serif;line-height:1.5;padding-bottom:60px}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
header.top{{background:var(--charcoal);color:var(--white);padding:26px 0;margin-bottom:26px}}
header.top .wrap{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}}
h1{{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;font-size:30px}}
.sub{{color:var(--sand);font-size:13px;letter-spacing:.5px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;margin-bottom:28px}}
.card{{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:18px 14px;text-align:center}}
.card .n{{font-family:'Cormorant Garamond',Georgia,serif;font-size:36px;font-weight:600;line-height:1}}
.card .l{{font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-top:8px}}
.prog .n{{color:var(--sage)}} .done .n{{color:#5B7A5B}} .holdc .n{{color:#C98A5A}} .holdi .n{{color:#9A7B8A}} .todo .n{{color:#A9A192}}
.score{{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:20px 22px;margin-bottom:28px;display:flex;align-items:center;gap:22px;flex-wrap:wrap}}
.score .meta h3{{font-family:'Cormorant Garamond',Georgia,serif;font-size:22px;font-weight:600;margin-bottom:4px}}
.score .meta p{{font-size:13px;color:var(--muted)}}
h2{{font-family:'Cormorant Garamond',Georgia,serif;font-size:22px;font-weight:600;margin:24px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}}
table{{width:100%;border-collapse:collapse;background:var(--white);border:1px solid var(--line);border-radius:6px;overflow:hidden}}
th{{background:#EFEAE0;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);padding:10px 14px}}
td{{padding:11px 14px;border-top:1px solid var(--line);font-size:14px;vertical-align:top}}
.pill{{display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;white-space:nowrap}}
.pill.prog{{background:#E7EDE7;color:#3F5A3F}} .pill.done{{background:#DDE8DD;color:#2F4A2F}}
.pill.holdc{{background:#F6E7D8;color:#8A5426}} .pill.holdi{{background:#EEE3EA;color:#6E4A62}} .pill.todo{{background:#ECE8DF;color:#6B6250}}
.flag{{display:inline-block;font-size:10px;color:var(--blocked);border:1px solid var(--blocked);border-radius:4px;padding:1px 6px;margin-left:6px;font-weight:600}}
.redflag{{background:#FBEEEC;border:1px solid #E7C3BD;border-left:3px solid var(--blocked);border-radius:4px;padding:12px 16px;margin-top:8px;font-size:13px;color:#7A2E26}}
footer{{margin-top:36px;font-size:12px;color:var(--muted);text-align:center;padding-top:18px;border-top:1px solid var(--line)}}
.muted{{color:var(--muted);font-size:12px}}
</style></head><body>
<header class="top"><div class="wrap">
<div><h1>RegenesisMD - Weekly Internal Dashboard</h1>
<div class="sub">Dr. Bhavna Vaidya, MD &nbsp;|&nbsp; live from task database</div></div>
<div class="sub">Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} &nbsp;|&nbsp; INTERNAL - not for client</div>
</div></header>
<div class="wrap">

<div class="cards">
<div class="card done"><div class="n">{counts['completed']}</div><div class="l">Completed</div></div>
<div class="card prog"><div class="n">{counts['in_progress']}</div><div class="l">In Progress</div></div>
<div class="card holdc"><div class="n">{counts['on_hold_client']}</div><div class="l">On Hold - Client</div></div>
<div class="card holdi"><div class="n">{counts['on_hold_internal']}</div><div class="l">On Hold - Internal</div></div>
<div class="card todo"><div class="n">{counts['to_do']}</div><div class="l">To Do</div></div>
</div>

<div class="score">
<svg width="96" height="96" viewBox="0 0 36 36">
<path d="M18 2.5a15.5 15.5 0 1 1 0 31 15.5 15.5 0 0 1 0-31" fill="none" stroke="#E4DED3" stroke-width="3"/>
<path d="M18 2.5a15.5 15.5 0 1 1 0 31 15.5 15.5 0 0 1 0-31" fill="none" stroke="#B8A06A" stroke-width="3"
 stroke-dasharray="{ring_pct},100" stroke-linecap="round"/>
<text x="18" y="19" text-anchor="middle" font-size="9" font-weight="700" fill="#1C1C1E">{ring_pct}</text>
<text x="18" y="25" text-anchor="middle" font-size="3.4" fill="#6B6659">/ 100</text></svg>
<div class="meta"><h3>AI Visibility Baseline: {AI_VISIBILITY_BASELINE} / 100</h3>
<p>Clean five-engine baseline. Target {AI_VISIBILITY_TARGET}+. Prior 18 and 27 retired as poisoned by 401 auth failures.</p></div>
</div>

<h2>Completed this week ({len(completed_week)})</h2>
{"<table><tr><th>Ref</th><th>Task</th><th>Status</th></tr>" + _rows(completed_week, lambda t:[t['external_ref'] or '-', t['title'], status_pill(t)]) + "</table>" if completed_week else '<p class="muted">Nothing moved to completed in the last 7 days.</p>'}

<h2>In Progress ({len(inprog)})</h2>
<table><tr><th>Ref</th><th>Task</th><th>Status</th><th>Notes</th></tr>
{_rows(inprog, lambda t:[t['external_ref'] or '-', t['title']+flag(t), status_pill(t), t['blocker_note'] or ''])}
</table>

<h2>On Hold - Awaiting Client ({len(holdc)})</h2>
<table><tr><th>Ref</th><th>Task</th><th>Status</th><th>Waiting on</th></tr>
{_rows(holdc, lambda t:[t['external_ref'] or '-', t['title'], status_pill(t), t['blocker_note'] or ''])}
</table>

<h2>On Hold - Awaiting Internal ({len(holdi)})</h2>
<table><tr><th>Ref</th><th>Task</th><th>Status</th><th>Waiting on</th></tr>
{_rows(holdi, lambda t:[t['external_ref'] or '-', t['title'], status_pill(t), t['blocker_note'] or ''])}
</table>

<h2>To Do ({len(todo)})</h2>
<table><tr><th>Ref</th><th>Task</th><th>Workstream</th></tr>
{_rows(todo, lambda t:[t['external_ref'] or '-', t['title'], t['workstream'] or ''])}
</table>

<h2>Compliance Watch (internal)</h2>
<div class="redflag"><strong>Botox hard stop.</strong> RMD carries Dysport and Xeomin only. No Botox-named content ships until Dr. Vaidya confirms framing.</div>
{"".join(f'<div class="redflag"><strong>Live defect:</strong> {t["external_ref"]} - {t["title"]}. {t["blocker_note"]}</div>' for t in defects)}

<footer>Live from the RMD task database. INTERNAL ONLY. The client-facing draft is a separate, redacted document.</footer>
</div></body></html>"""
    return html
