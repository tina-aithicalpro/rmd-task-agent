"""
Database access layer. Thin functions over the schema. The status-change
trigger in schema.sql auto-logs status_history, so update_status does NOT
write history itself - the database handles that.
"""
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row

from .settings import settings

VALID_STATUSES = {
    "to_do", "in_progress", "completed", "on_hold_client", "on_hold_internal",
}
VALID_TYPES = {"one_shot", "recurring"}
VALID_CADENCES = {"weekly", "biweekly", "monthly", "twice_weekly", "daily"}


@contextmanager
def get_conn():
    conn = psycopg.connect(settings.DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_tasks(status: str | None = None, workstream: str | None = None,
               origin: str | None = None) -> list[dict]:
    clauses, params = [], []
    if status:
        clauses.append("status = %s"); params.append(status)
    if workstream:
        clauses.append("workstream = %s"); params.append(workstream)
    if origin:
        clauses.append("origin = %s"); params.append(origin)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM tasks {where} ORDER BY origin, id"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def get_task(task_id: int) -> dict | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = %s", [task_id]).fetchone()


def update_status(task_id: int, new_status: str, changed_by: str | None) -> dict | None:
    """Update a task's status. The DB trigger logs history automatically.
    We set assignee to changed_by only if provided, so history captures who
    made the change (the trigger reads NEW.assignee)."""
    with get_conn() as conn:
        if changed_by:
            conn.execute(
                "UPDATE tasks SET status = %s, assignee = %s WHERE id = %s",
                [new_status, changed_by, task_id],
            )
        else:
            conn.execute(
                "UPDATE tasks SET status = %s WHERE id = %s",
                [new_status, task_id],
            )
        return conn.execute("SELECT * FROM tasks WHERE id = %s", [task_id]).fetchone()


def add_task(title: str, workstream: str | None, assignee: str | None,
             task_type: str = "one_shot", cadence: str | None = None,
             status: str = "to_do", blocker_note: str | None = None) -> dict:
    """Create an agent-origin task. origin is always 'agent' here - tasks the
    agent adds are distinct from clickup/project seed tasks."""
    with get_conn() as conn:
        row = conn.execute(
            """INSERT INTO tasks
                 (origin, title, status, task_type, cadence, assignee,
                  workstream, blocker_note)
               VALUES ('agent', %s, %s, %s, %s, %s, %s, %s)
               RETURNING *""",
            [title, status, task_type, cadence, assignee, workstream, blocker_note],
        ).fetchone()
        return row


def completed_since(iso_datetime: str) -> list[dict]:
    """Tasks moved to 'completed' since a given time - powers 'completed this
    week' from status_history rather than a static snapshot."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT t.* FROM tasks t
               JOIN status_history h ON h.task_id = t.id
               WHERE h.new_status = 'completed' AND h.changed_at >= %s
               ORDER BY t.id""",
            [iso_datetime],
        ).fetchall()
