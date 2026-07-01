"""
Interactive dashboard generator. Reads the database and renders the
Aithical-styled HTML dashboard WITH controls: per-task status dropdowns, an
add-task form, and a generate-client-draft button. The buttons call the live
API endpoints via JavaScript, reading the API key from the page URL (?key=...)
and sending it as the X-API-Key header. Internal view - never sent to client.
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
STATUS_ORDER = ["to_do", "in_progress", "completed", "on_hold_client", "on_hold_internal"]


def _status_select(task):
    opts = "".join(
        f'<option value="{s}"{" selected" if s == task["status"] else ""}>{STATUS_LABEL[s]}</option>'
        for s in STATUS_ORDER
    )
    return (
        f'<select class="statussel" data-id="{task["id"]}" '
        f'onchange="updateStatus(this)">{opts}</select>'
    )


def _task_row(task):
    ref = task["external_ref"] or "-"
    flag = '<span class="flag">INTERNALLY BLOCKED</span>' if task["internal_blocked"] else ""
    note = task["blocker_note"] or ""
    return (
        f'<tr><td class="ref">{ref}</td>'
        f'<td>{task["title"]}{flag}</td>'
        f'<td>{_status_select(task)}</td>'
        f'<td class="note">{note}</td></tr>'
    )


def render_dashboard() -> str:
    tasks = db.list_tasks()
    counts = {k: 0 for k in STATUS_LABEL}
    for t in tasks:
        counts[t["status"]] = counts.get(t["status"], 0) + 1

    ring_pct = int(AI_VISIBILITY_BASELINE)
    defects = [t for t in tasks if t["blocker_note"] and "LIVE" in (t["blocker_note"] or "").upper()]
    all_sorted = sorted(tasks, key=lambda t: (STATUS_ORDER.index(t["status"]), t["id"]))
    rows_html = "".join(_task_row(t) for t in all_sorted)
    defect_html = "".join(
        f'<div class="redflag"><strong>Live defect:</strong> {t["external_ref"]} - {t["title"]}. {t["blocker_note"]}</div>'
        for t in defects
    )
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RegenesisMD - Weekly Dashboard</title>
<style>
:root{{--cream:#F5F2EC;--charcoal:#1C1C1E;--gold:#B8A06A;--sage:#8A9E8C;--sand:#C9B99A;--white:#FAF8F5;--line:#E4DED3;--muted:#6B6659;--blocked:#B5544A}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--cream);color:var(--charcoal);font-family:'DM Sans',-apple-system,Segoe UI,sans-serif;line-height:1.5;padding-bottom:60px}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
header.top{{background:var(--charcoal);color:var(--white);padding:26px 0;margin-bottom:22px}}
header.top .wrap{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}}
h1{{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;font-size:30px}}
.sub{{color:var(--sand);font-size:13px;letter-spacing:.5px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;margin-bottom:22px}}
.card{{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:16px 14px;text-align:center}}
.card .n{{font-family:'Cormorant Garamond',Georgia,serif;font-size:34px;font-weight:600;line-height:1}}
.card .l{{font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted);margin-top:8px}}
.prog .n{{color:var(--sage)}} .done .n{{color:#5B7A5B}} .holdc .n{{color:#C98A5A}} .holdi .n{{color:#9A7B8A}} .todo .n{{color:#A9A192}}
.toolbar{{display:flex;gap:12px;flex-wrap:wrap;align-items:center;background:var(--white);border:1px solid var(--line);border-radius:6px;padding:16px;margin-bottom:22px}}
.btn{{background:var(--gold);color:#1C1C1E;border:none;border-radius:5px;padding:10px 16px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}}
.btn:hover{{opacity:.9}}
.btn.sec{{background:transparent;border:1px solid var(--gold);color:#8A6D2A}}
h2{{font-family:'Cormorant Garamond',Georgia,serif;font-size:22px;font-weight:600;margin:22px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}}
table{{width:100%;border-collapse:collapse;background:var(--white);border:1px solid var(--line);border-radius:6px;overflow:hidden}}
th{{background:#EFEAE0;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);padding:10px 14px}}
td{{padding:9px 14px;border-top:1px solid var(--line);font-size:14px;vertical-align:middle}}
td.ref{{color:var(--muted);white-space:nowrap}} td.note{{color:var(--muted);font-size:12px}}
select.statussel{{font-family:inherit;font-size:13px;padding:5px 8px;border:1px solid var(--line);border-radius:5px;background:var(--white);cursor:pointer}}
.flag{{display:inline-block;font-size:10px;color:var(--blocked);border:1px solid var(--blocked);border-radius:4px;padding:1px 6px;margin-left:6px;font-weight:600}}
.addform{{display:none;background:var(--white);border:1px solid var(--line);border-radius:6px;padding:16px;margin-bottom:22px;gap:10px;flex-wrap:wrap}}
.addform.show{{display:flex}}
.addform input,.addform select{{font-family:inherit;font-size:14px;padding:8px 10px;border:1px solid var(--line);border-radius:5px}}
.addform input.title{{flex:1;min-width:240px}}
#draftbox{{display:none;background:var(--white);border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:6px;padding:18px;margin-bottom:22px;white-space:pre-wrap;font-size:14px;line-height:1.6}}
#draftbox.show{{display:block}}
#toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--charcoal);color:#fff;padding:10px 18px;border-radius:6px;font-size:14px;opacity:0;transition:opacity .3s;z-index:99}}
#toast.show{{opacity:1}}
.score{{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:18px 22px;margin-bottom:22px;display:flex;align-items:center;gap:22px;flex-wrap:wrap}}
.score .meta h3{{font-family:'Cormorant Garamond',Georgia,serif;font-size:22px;font-weight:600;margin-bottom:4px}}
.score .meta p{{font-size:13px;color:var(--muted)}}
.redflag{{background:#FBEEEC;border:1px solid #E7C3BD;border-left:3px solid var(--blocked);border-radius:4px;padding:12px 16px;margin-top:8px;font-size:13px;color:#7A2E26}}
.muted{{color:var(--muted);font-size:12px}}
</style></head><body>
<header class="top"><div class="wrap">
<div><h1>RegenesisMD - Weekly Dashboard</h1>
<div class="sub">Dr. Bhavna Vaidya, MD &nbsp;|&nbsp; live and editable from the task database</div></div>
<div class="sub">{now} &nbsp;|&nbsp; INTERNAL</div>
</div></header>
<div class="wrap">

<div class="cards">
<div class="card done"><div class="n">{counts['completed']}</div><div class="l">Completed</div></div>
<div class="card prog"><div class="n">{counts['in_progress']}</div><div class="l">In Progress</div></div>
<div class="card holdc"><div class="n">{counts['on_hold_client']}</div><div class="l">On Hold - Client</div></div>
<div class="card holdi"><div class="n">{counts['on_hold_internal']}</div><div class="l">On Hold - Internal</div></div>
<div class="card todo"><div class="n">{counts['to_do']}</div><div class="l">To Do</div></div>
</div>

<div class="toolbar">
<button class="btn" onclick="toggleAdd()">+ Add Task</button>
<button class="btn" onclick="genDraft()">Generate Client Draft</button>
<span class="muted">Change a task's status from its dropdown. Changes save immediately.</span>
</div>

<div class="addform" id="addform">
<input class="title" id="nt-title" placeholder="New task title" />
<input id="nt-ws" placeholder="Workstream (optional)" />
<input id="nt-assignee" placeholder="Assignee (optional)" />
<select id="nt-status">
<option value="to_do">To Do</option><option value="in_progress">In Progress</option>
<option value="completed">Completed</option><option value="on_hold_client">On Hold - Client</option>
<option value="on_hold_internal">On Hold - Internal</option>
</select>
<button class="btn" onclick="addTask()">Save Task</button>
<button class="btn sec" onclick="toggleAdd()">Cancel</button>
</div>

<div id="draftbox"></div>

<div class="score">
<svg width="90" height="90" viewBox="0 0 36 36">
<path d="M18 2.5a15.5 15.5 0 1 1 0 31 15.5 15.5 0 0 1 0-31" fill="none" stroke="#E4DED3" stroke-width="3"/>
<path d="M18 2.5a15.5 15.5 0 1 1 0 31 15.5 15.5 0 0 1 0-31" fill="none" stroke="#B8A06A" stroke-width="3"
 stroke-dasharray="{ring_pct},100" stroke-linecap="round"/>
<text x="18" y="19" text-anchor="middle" font-size="9" font-weight="700" fill="#1C1C1E">{ring_pct}</text>
<text x="18" y="25" text-anchor="middle" font-size="3.4" fill="#6B6659">/ 100</text></svg>
<div class="meta"><h3>AI Visibility Baseline: {AI_VISIBILITY_BASELINE} / 100</h3>
<p>Clean five-engine baseline. Target {AI_VISIBILITY_TARGET}+. Prior 18 and 27 retired as poisoned by 401 auth failures.</p></div>
</div>

<h2>All Tasks ({len(tasks)})</h2>
<table><tr><th>Ref</th><th>Task</th><th>Status</th><th>Notes</th></tr>
{rows_html}
</table>

<h2>Compliance Watch (internal)</h2>
<div class="redflag"><strong>Botox hard stop.</strong> RMD carries Dysport and Xeomin only. No Botox-named content ships until Dr. Vaidya confirms framing.</div>
{defect_html}

<footer style="margin-top:36px;font-size:12px;color:var(--muted);text-align:center;padding-top:18px;border-top:1px solid var(--line)">
Live and editable from the RMD task database. INTERNAL ONLY. The client-facing draft routes to Jay for approval before sending.
</footer>
</div>

<div id="toast"></div>

<script>
const KEY = new URLSearchParams(window.location.search).get('key') || '';
function toast(m){{const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600);}}
async function updateStatus(sel){{
  const id=sel.dataset.id,newStatus=sel.value;
  try{{
    const r=await fetch(`/tasks/${{id}}/status`,{{method:'POST',headers:{{'Content-Type':'application/json','X-API-Key':KEY}},body:JSON.stringify({{new_status:newStatus}})}});
    if(!r.ok){{toast('Update failed ('+r.status+')');return;}}
    toast('Task '+id+' updated');setTimeout(()=>location.reload(),700);
  }}catch(e){{toast('Network error');}}
}}
function toggleAdd(){{document.getElementById('addform').classList.toggle('show');}}
async function addTask(){{
  const title=document.getElementById('nt-title').value.trim();
  if(!title){{toast('Title required');return;}}
  const body={{title:title,workstream:document.getElementById('nt-ws').value.trim()||null,assignee:document.getElementById('nt-assignee').value.trim()||null,status:document.getElementById('nt-status').value}};
  try{{
    const r=await fetch('/tasks',{{method:'POST',headers:{{'Content-Type':'application/json','X-API-Key':KEY}},body:JSON.stringify(body)}});
    if(!r.ok){{toast('Add failed ('+r.status+')');return;}}
    toast('Task added');setTimeout(()=>location.reload(),700);
  }}catch(e){{toast('Network error');}}
}}
async function genDraft(){{
  const box=document.getElementById('draftbox');box.classList.add('show');box.textContent='Generating draft...';
  try{{
    const r=await fetch('/client-draft',{{method:'POST',headers:{{'Content-Type':'application/json','X-API-Key':KEY}}}});
    const data=await r.json();
    if(!r.ok){{box.textContent='Draft blocked or failed: '+(data.detail||r.status);return;}}
    box.textContent=data.draft;
  }}catch(e){{box.textContent='Network error generating draft.';}}
}}
</script>
</body></html>"""
