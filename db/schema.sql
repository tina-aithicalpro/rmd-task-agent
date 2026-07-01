-- RMD Task Agent - Database Schema (Postgres)
-- Deploy target: Railway (native Postgres).
-- This file defines the data layer only. Redaction rules, compliance hard stops,
-- and the 36/100 baseline are LOGIC and live in the agent code, NOT here.
-- Data changes weekly (task statuses); rules stay constant. Keep them apart.

-- ---------------------------------------------------------------------------
-- ENUMS - enforced at the database level so invalid data cannot be written.
-- ---------------------------------------------------------------------------

CREATE TYPE task_origin   AS ENUM ('clickup', 'project', 'agent');
CREATE TYPE task_status   AS ENUM (
  'to_do',
  'in_progress',
  'completed',
  'on_hold_client',     -- On Hold - Awaiting Client (Jay or RMD/Dr. Vaidya)
  'on_hold_internal'    -- On Hold - Awaiting Internal (dashboard-only, never client-facing)
);
CREATE TYPE task_type     AS ENUM ('one_shot', 'recurring');
CREATE TYPE task_cadence  AS ENUM ('weekly', 'biweekly', 'monthly', 'twice_weekly', 'daily');

-- ---------------------------------------------------------------------------
-- SERVICES - the locked six pillars. Agent reads these from the DB once
-- standalone, instead of a config file. Changes only when the service line does.
-- ---------------------------------------------------------------------------

CREATE TABLE services (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  brand       TEXT NOT NULL DEFAULT 'RMD',   -- RMD or PTR
  note        TEXT
);

-- ---------------------------------------------------------------------------
-- TASKS - every task, both origins, both types, one table.
-- ---------------------------------------------------------------------------

CREATE TABLE tasks (
  id                 SERIAL PRIMARY KEY,        -- agent-owned identity, not the ClickUp id
  origin             task_origin  NOT NULL,
  external_ref       TEXT,                       -- ClickUp id or P-number; NULL for agent-created
  title              TEXT NOT NULL,
  status             task_status  NOT NULL DEFAULT 'to_do',
  task_type          task_type    NOT NULL DEFAULT 'one_shot',
  cadence            task_cadence,               -- only for recurring; see constraint below
  assignee           TEXT,                       -- plain text for now; promote to FK if per-person views needed
  internal_blocked   BOOLEAN NOT NULL DEFAULT FALSE, -- dashboard-only sub-flag, independent of status
  blocker_note       TEXT,                       -- who/what it waits on
  duplicate_of       TEXT,                       -- e.g. 'clickup-3' for P-22; keeps counts honest
  workstream         TEXT,                       -- AI Visibility, Competitor Intel, Shopify, Website, T Room, AMC, Commercial
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_status_change TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- A one_shot task must NOT carry a cadence; a recurring task MUST.
  CONSTRAINT cadence_matches_type CHECK (
    (task_type = 'recurring' AND cadence IS NOT NULL) OR
    (task_type = 'one_shot'  AND cadence IS NULL)
  )
);

CREATE INDEX idx_tasks_status     ON tasks(status);
CREATE INDEX idx_tasks_origin     ON tasks(origin);
CREATE INDEX idx_tasks_workstream ON tasks(workstream);

-- ---------------------------------------------------------------------------
-- STATUS_HISTORY - every status change as a row. This is what makes the weekly
-- update AUTOMATIC: "completed this week" / "moved on hold this week" compute
-- from here. Without it the agent can only show a static snapshot.
-- ---------------------------------------------------------------------------

CREATE TABLE status_history (
  id           SERIAL PRIMARY KEY,
  task_id      INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  old_status   task_status,               -- NULL on first insert (task creation)
  new_status   task_status NOT NULL,
  changed_by   TEXT,                       -- team member who made the change
  changed_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_history_task ON status_history(task_id);
CREATE INDEX idx_history_when ON status_history(changed_at);

-- ---------------------------------------------------------------------------
-- Trigger: keep updated_at and last_status_change honest, and auto-log history.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION touch_task() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  IF (NEW.status IS DISTINCT FROM OLD.status) THEN
    NEW.last_status_change := now();
    INSERT INTO status_history(task_id, old_status, new_status, changed_by)
    VALUES (NEW.id, OLD.status, NEW.status, NEW.assignee);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_touch_task
  BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION touch_task();
