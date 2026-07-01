"""
RMD Task Agent - API.
Endpoints:
  GET  /health                 - liveness, no auth
  GET  /tasks                  - list tasks (filters: status, workstream, origin)
  GET  /tasks/{id}             - one task
  POST /tasks/{id}/status      - update a task's status (auto-logs history)
  POST /tasks                  - add a new agent-origin task
  GET  /completed              - tasks completed since ?since=ISO datetime

Every endpoint except /health requires header:  X-API-Key: <the key>
"""
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .settings import settings, require_startup_secrets
from . import db
from . import dashboard as dash
from . import client_draft as cd

require_startup_secrets()  # refuse to boot without DATABASE_URL and API_KEY

app = FastAPI(title="RMD Task Agent", version="0.1.0")


def check_api_key(x_api_key: str = Header(default="")) -> None:
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


def check_dashboard_key(x_api_key: str = Header(default=""), key: str = "") -> None:
    """Dashboard-only auth. Accepts the key from the X-API-Key header OR a
    ?key=... URL parameter, so the dashboard opens as a plain browser link.
    Treat the resulting link like a password - it exposes the key in URL/history.
    All OTHER endpoints stay header-only via check_api_key."""
    if x_api_key == settings.API_KEY or key == settings.API_KEY:
        return
    raise HTTPException(status_code=401, detail="Invalid or missing key. Add ?key=YOUR_API_KEY to the URL.")


# ---- request models ----
class StatusUpdate(BaseModel):
    new_status: str = Field(..., description="to_do|in_progress|completed|on_hold_client|on_hold_internal")
    changed_by: str | None = Field(default=None, description="team member making the change")


class NewTask(BaseModel):
    title: str
    workstream: str | None = None
    assignee: str | None = None
    task_type: str = "one_shot"
    cadence: str | None = None
    status: str = "to_do"
    blocker_note: str | None = None


# ---- endpoints ----
@app.get("/health")
def health():
    return {"status": "ok", "client": settings.CLIENT_NAME}


@app.get("/tasks", dependencies=[Depends(check_api_key)])
def get_tasks(status: str | None = None, workstream: str | None = None,
              origin: str | None = None):
    if status and status not in db.VALID_STATUSES:
        raise HTTPException(422, f"invalid status. valid: {sorted(db.VALID_STATUSES)}")
    return db.list_tasks(status=status, workstream=workstream, origin=origin)


@app.get("/tasks/{task_id}", dependencies=[Depends(check_api_key)])
def get_one(task_id: int):
    row = db.get_task(task_id)
    if not row:
        raise HTTPException(404, "task not found")
    return row


@app.post("/tasks/{task_id}/status", dependencies=[Depends(check_api_key)])
def set_status(task_id: int, body: StatusUpdate):
    if body.new_status not in db.VALID_STATUSES:
        raise HTTPException(422, f"invalid status. valid: {sorted(db.VALID_STATUSES)}")
    if not db.get_task(task_id):
        raise HTTPException(404, "task not found")
    return db.update_status(task_id, body.new_status, body.changed_by)


@app.post("/tasks", dependencies=[Depends(check_api_key)])
def create_task(body: NewTask):
    if body.status not in db.VALID_STATUSES:
        raise HTTPException(422, f"invalid status. valid: {sorted(db.VALID_STATUSES)}")
    if body.task_type not in db.VALID_TYPES:
        raise HTTPException(422, f"invalid task_type. valid: {sorted(db.VALID_TYPES)}")
    # cadence/type consistency is ALSO enforced by the DB constraint; we check
    # here to return a clean 422 instead of a raw DB error.
    if body.task_type == "recurring" and not body.cadence:
        raise HTTPException(422, "recurring task requires a cadence")
    if body.task_type == "one_shot" and body.cadence:
        raise HTTPException(422, "one_shot task must not have a cadence")
    if body.cadence and body.cadence not in db.VALID_CADENCES:
        raise HTTPException(422, f"invalid cadence. valid: {sorted(db.VALID_CADENCES)}")
    return db.add_task(
        title=body.title, workstream=body.workstream, assignee=body.assignee,
        task_type=body.task_type, cadence=body.cadence, status=body.status,
        blocker_note=body.blocker_note,
    )


@app.get("/completed", dependencies=[Depends(check_api_key)])
def get_completed(since: str):
    """since = ISO datetime, e.g. 2026-06-25T00:00:00Z"""
    return db.completed_since(since)


@app.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(check_dashboard_key)])
def get_dashboard():
    """Internal dashboard, rendered live from the database. Shows everything.
    Opens as a plain browser link with ?key=YOUR_API_KEY. Not world-open."""
    return dash.render_dashboard()


@app.post("/client-draft", dependencies=[Depends(check_api_key)])
def make_client_draft():
    """Generate the client update draft (Claude-written, self-check gated).
    Returns the draft for routing to Jay, or a 409 if the compliance gate
    blocked it. Never auto-sends."""
    try:
        return cd.generate_client_draft()
    except cd.ComplianceBlock as e:
        raise HTTPException(status_code=409, detail=str(e))
