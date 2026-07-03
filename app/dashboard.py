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

    # group tasks by status into collapsible sections (open the working ones,
    # collapse To Do since it is the largest and least actively worked)
    section_meta = [
        ("completed", "Completed", "done", False),
        ("in_progress", "In Progress", "prog", True),
        ("on_hold_client", "On Hold - Awaiting Client", "holdc", True),
        ("on_hold_internal", "On Hold - Awaiting Internal", "holdi", True),
        ("to_do", "To Do", "todo", False),
    ]
    sections_html = ""
    for status_key, label, cls, open_default in section_meta:
        items = [t for t in tasks if t["status"] == status_key]
        rows = "".join(_task_row(t) for t in items)
        open_attr = " open" if (open_default and items) else ""
        body = (
            f'<table><tr><th>Ref</th><th>Task</th><th>Status</th><th>Notes</th></tr>{rows}</table>'
            if items else '<p class="muted" style="padding:10px 4px">No tasks in this status.</p>'
        )
        sections_html += (
            f'<details class="statusgroup {cls}"{open_attr}>'
            f'<summary><span class="dot"></span>{label}'
            f'<span class="count">{len(items)}</span></summary>'
            f'<div class="groupbody">{body}</div></details>'
        )

    defect_html = "".join(
        f'<div class="redflag"><strong>Live defect:</strong> {t["external_ref"]} - {t["title"]}. {t["blocker_note"]}</div>'
        for t in defects
    )
    waiting_on_client = [t for t in tasks if t["status"] == "on_hold_client"]; attention_items = defects + [t for t in waiting_on_client if t not in defects]; attention_html = "".join(f'<div class="alertRow"><div><span class="ref">{t["external_ref"] or "-"}</span> <span class="title">{t["title"]}</span></div><span class="pill {"live" if t in defects else "waiting"}">{"LIVE DEFECT" if t in defects else "WAITING ON CLIENT"}</span></div>' for t in attention_items)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RegenesisMD - Weekly Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=JetBrains+Mono:wght@400;600&display=swap');
:root{{
--cream:#F3ECE2;--ink:#1E2142;--white:#FFFFFF;--line:#E7DFD2;--muted:#6B6659;
--blush:#F3DCD6;--blocked:#8B2E2E;--waiting:#7A2E26;--waiting-bg:#E9C6C0;
--peri1:#CBCBEA;--peri2:#9C9FDD;
--sage:#5B7A5B;--holdc:#C9667C;--holdi:#B5544A;--todo:#A9A192;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--cream);color:var(--ink);font-family:'DM Sans',-apple-system,Segoe UI,sans-serif;line-height:1.5;padding-bottom:60px}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
header.top{{background:var(--ink);color:#fff;padding:22px 0}}
header.top .wrap{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
h1{{font-family:'Cormorant Garamond',Georgia,serif;font-style:italic;font-weight:600;font-size:28px}}
.sub{{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:12px;color:#C7C8E8}}
.btn{{background:#fff;color:var(--ink);border:1px solid #fff;border-radius:999px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif}}
.btn.sec{{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.6)}}
.btn:hover{{opacity:.9}}
.alertBox{{background:var(--blush);border-radius:14px;padding:22px 26px;margin:26px 0}}
.alertBox h2{{font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;font-weight:600;display:inline}}
.alertBox .tag{{font-family:'JetBrains Mono',monospace;color:#8B2E2E;font-size:12px;margin-left:12px}}
.alertRow{{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,.35);border-radius:10px;padding:14px 18px;margin-top:14px}}
.alertRow .ref{{font-family:'JetBrains Mono',monospace;color:#8A5A52;font-size:13px;margin-right:16px}}
.alertRow .title{{font-weight:600;font-size:15px}}
.pill{{font-family:'JetBrains Mono',monospace;font-size:11px;text-transform:uppercase;letter-spacing:.5px;padding:5px 12px;border-radius:999px;font-weight:600}}
.pill.live{{background:#8B2E2E;color:#fff}}
.pill.waiting{{background:var(--waiting-bg);color:var(--waiting)}}
.topgrid{{display:grid;grid-template-columns:1.6fr repeat(5,1fr);gap:16px;margin:26px 0}}
.score{{background:var(--white);border-radius:14px;padding:20px;display:flex;align-items:center;gap:16px;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.score .meta p.lbl{{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.5px;color:var(--muted);text-transform:uppercase}}
.score .meta h3{{font-family:'Cormorant Garamond',Georgia,serif;font-size:26px;font-weight:600;margin:4px 0}}
.score .meta p.desc{{font-size:12px;color:var(--muted);max-width:220px}}
.card{{background:var(--white);border-radius:14px;padding:18px 16px;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.card .l{{font-family:'JetBrains Mono',monospace;font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);display:flex;align-items:center;gap:6px}}
.card .l .dot{{width:8px;height:8px;border-radius:50%;display:inline-block}}
.card .n{{font-size:32px;font-weight:700;margin-top:8px}}
.prog .dot{{background:var(--ink)}} .done .dot{{background:var(--sage)}} .holdc .dot{{background:var(--holdc)}} .holdi .dot{{background:var(--holdi)}} .todo .dot{{background:var(--todo)}}
.tasksSection{{background:linear-gradient(180deg,var(--peri1),var(--peri2));position:relative;left:50%;right:50%;margin-left:-50vw;margin-right:-50vw;width:100vw;padding:32px 0 40px}}
.tasksSection h2{{font-family:'Cormorant Garamond',Georgia,serif;font-size:24px;font-weight:600;color:var(--ink);margin-bottom:16px}}
.statusgroup{{background:var(--white);border-radius:12px;margin-bottom:14px;overflow:hidden}}
.statusgroup summary{{list-style:none;cursor:pointer;padding:16px 20px;font-family:'Cormorant Garamond',Georgia,serif;font-size:19px;font-weight:600;display:flex;align-items:center;gap:10px;user-select:none}}
.statusgroup summary::-webkit-details-marker{{display:none}}
.statusgroup .dot{{width:9px;height:9px;border-radius:50%;flex:0 0 9px}}
.statusgroup.done .dot{{background:var(--sage)}} .statusgroup.prog .dot{{background:var(--ink)}}
.statusgroup.holdc .dot{{background:var(--holdc)}} .statusgroup.holdi .dot{{background:var(--holdi)}} .statusgroup.todo .dot{{background:var(--todo)}}
.statusgroup .count{{font-family:'DM Sans',sans-serif;font-size:12px;font-weight:600;color:var(--muted);background:#EFEAE0;border-radius:20px;padding:2px 10px;min-width:26px;text-align:center}}
.statusgroup summary::after{{content:"expand";font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-left:auto}}
.statusgroup[open] summary::after{{content:"collapse"}}
.statusgroup .groupbody{{padding:0 6px 8px}}
table{{width:100%;border-collapse:collapse}}
th{{background:#EFEAE0;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);padding:10px 14px}}
td{{padding:9px 14px;border-top:1px solid var(--line);font-size:14px;vertical-align:middle}}
td.ref{{color:var(--muted);white-space:nowrap;font-size:12px}}
td.note{{color:var(--muted);font-size:12px}}
select.statussel{{font-family:'DM Sans',sans-serif;font-size:13px;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:var(--white);cursor:pointer}}
.flag{{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:10px;color:#fff;background:#B5544A;border-radius:4px;padding:2px 6px;margin-left:6px;font-weight:600}}
.muted{{color:var(--muted);font-size:12px}}
.addform{{display:none;background:var(--white);border-radius:10px;padding:16px;margin-bottom:22px;gap:10px;flex-wrap:wrap}}
.addform.show{{display:flex}}
.addform input,.addform select{{font-family:inherit;font-size:14px;padding:8px 10px;border:1px solid var(--line);border-radius:6px}}
.addform input.title{{flex:1;min-width:240px}}
#draftbox{{display:none;background:var(--white);border-left:3px solid var(--ink);border-radius:10px;padding:18px;margin-bottom:22px;white-space:pre-wrap;font-size:14px;line-height:1.6}}
#draftbox.show{{display:block}}
#toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--ink);color:#fff;padding:10px 18px;border-radius:6px;font-size:14px;opacity:0;transition:opacity .3s;z-index:99}}
#toast.show{{opacity:1}}
.redflag{{background:#FBEEEC;border-left:3px solid var(--blocked);border-radius:6px;padding:12px 16px;margin-top:8px;font-size:13px;color:#7A2E26}}
.compliance{{padding:24px 0}}
footer.dashFooter{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;font-family:'JetBrains Mono',monospace;font-size:11px;color:#7A2E26;text-transform:uppercase;letter-spacing:.5px;padding:20px 0;border-top:1px solid rgba(0,0,0,.08)}}
</style></head><body>
<header class="top"><div class="wrap">
<div><h1>RegenesisMD</h1>
<div class="sub">WEEKLY TASK DASHBOARD &middot; INTERNAL</div></div>
<div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
<div class="sub">{now}</div>
<button class="btn sec" onclick="genDraft()">Generate client draft</button>
<button class="btn" onclick="toggleAdd()">Add task</button>
</div>
</div></header>
<div class="wrap">

<div class="alertBox">
<h2>Needs attention today</h2><span class="tag">{len(attention_items)} items blocking progress</span>
{attention_html if attention_items else '<p class="muted" style="margin-top:14px">Nothing needs attention right now.</p>'}
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
<button class="btn sec" style="color:var(--ink);border-color:var(--ink)" onclick="toggleAdd()">Cancel</button>
</div>

<div id="draftbox"></div>

<div class="topgrid">
<div class="score">
<svg width="86" height="86" viewBox="0 0 36 36">
<path d="M18 2.5a15.5 15.5 0 1 1 0 31 15.5 15.5 0 0 1 0-31" fill="none" stroke="#E7DFD2" stroke-width="3"/>
<path d="M18 2.5a15.5 15.5 0 1 1 0 31 15.5 15.5 0 0 1 0-31" fill="none" stroke="#1E2142" stroke-width="3" stroke-dasharray="{ring_pct},100" stroke-linecap="round"/>
    <text x="18" y="19" text-anchor="middle" font-size="9" font-weight="700" fill="#1E2142">{ring_pct}</text>
    <text x="18" y="25" text-anchor="middle" font-size="3.4" fill="#6B6659">/ 100</text></svg>
    <div class="meta"><p class="lbl">AI Visibility Score</p><h3>{ring_pct} &rarr; {AI_VISIBILITY_TARGET}</h3><p class="desc">Baseline vs 90-day target. Every open task below moves this number.</p></div>
    </div>
    <div class="card prog"><div class="l"><span class="dot"></span>In Progress</div><div class="n">{counts['in_progress']}</div></div>
    <div class="card done"><div class="l"><span class="dot"></span>Completed</div><div class="n">{counts['completed']}</div></div>
    <div class="card holdc"><div class="l"><span class="dot"></span>On Hold - Client</div><div class="n">{counts['on_hold_client']}</div></div>
    <div class="card holdi"><div class="l"><span class="dot"></span>On Hold - Internal</div><div class="n">{counts['on_hold_internal']}</div></div>
    <div class="card todo"><div class="l"><span class="dot"></span>To Do</div><div class="n">{counts['to_do']}</div></div>
    </div>

    </div>

    <div class="tasksSection"><div class="wrap">
    <h2>Tasks by status <span class="muted">{len(tasks)} tasks</span></h2>
    {sections_html}
    </div></div>

    <div class="wrap">
    <div class="compliance">
    <h2>Compliance Watch (internal)</h2>
    <div class="redflag"><strong>Botox hard stop.</strong> RMD carries Dysport and Xeomin only. No Botox-named content ships until Dr. Vaidya confirms framing.</div>
    {defect_html}
    </div>

    <footer class="dashFooter">
    <span>Internal dashboard &mdash; RegenesisMD &middot; Not for client distribution</span>
    <span>{now}</span>
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
