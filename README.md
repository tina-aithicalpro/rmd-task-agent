# RMD Task Agent

A small web service that holds all RegenesisMD tasks (from ClickUp and from this
project) in one database, lets your team update task statuses, add new tasks, and
powers the weekly dashboard and client-update draft.

You do not need to write or edit any code to run this. The steps below are
copy-paste and one-time. After that, the team just updates task statuses.

---

## What's in here (you never edit these)

- `app/` - the running service (the task API and its rules).
- `db/schema.sql` - sets up the database tables. Run once.
- `db/seed.sql` - loads the 56 starting tasks. Run once.
- `railway.json`, `Procfile`, `runtime.txt` - tell Railway how to run it.
- `requirements.txt` - the libraries Railway installs automatically.

---

## One-time setup

### Step 1 - Put this folder on GitHub
1. Go to github.com and create a new empty repository named `rmd-task-agent`.
2. On the new repo page, choose "uploading an existing file."
3. Drag this entire folder's contents in and commit.

That's it for GitHub. You will not touch it again unless the app changes.

### Step 2 - Create the Railway project
1. Go to railway.app and sign in.
2. Click "New Project" then "Deploy from GitHub repo."
3. Pick the `rmd-task-agent` repo you just created.

Railway will start building automatically. It will not fully work yet - it needs
a database and three settings. Next steps.

### Step 3 - Add the database
1. In your Railway project, click "New" then "Database" then "Add PostgreSQL."
2. Railway creates it and automatically provides a `DATABASE_URL` to your app.
   You do not copy anything by hand for this one.

### Step 4 - Add the three settings (environment variables)
In your Railway project, open the app service, go to the "Variables" tab, and add:

| Name | Value | What it is |
|------|-------|-----------|
| `API_KEY` | a long random string you make up | The password that protects your task list. Keep it private. |
| `ANTHROPIC_API_KEY` | your Anthropic API key | Used later by the dashboard/draft generator. |
| `DATABASE_URL` | already set by Railway | Do not add this - Railway added it in Step 3. |

For `API_KEY`, any long random string works. Treat it like a password. Anyone
who has it can read and change your task list, so do not share it publicly.

The app is built to REFUSE to start if `API_KEY` or `DATABASE_URL` is missing.
That is on purpose - it will not run wide open.

### Step 5 - Load the tasks into the database (one time)
1. In Railway, click your PostgreSQL database, open the "Data" or "Query" tab
   (Railway provides a query box for the database).
2. Open `db/schema.sql` from this folder, copy all of it, paste it into the
   query box, and run it. This creates the tables.
3. Then open `db/seed.sql`, copy all of it, paste it into the query box, and run
   it. This loads the 56 starting tasks.

Run schema first, then seed. Run each once. If you run seed twice you get
duplicate tasks.

### Step 6 - Confirm it works
Railway gives your app a public web address (something like
`rmd-task-agent-production.up.railway.app`). Open that address with `/health`
on the end:

`https://your-app-address.up.railway.app/health`

You should see: `{"status":"ok","client":"RegenesisMD"}`

That means it is live.

---

## Using it day to day

You do not use the web address directly for daily work - that's the plumbing.
The weekly dashboard and client draft (built in the next step) read from this
service. Your team's only job is to keep task statuses current.

The valid statuses are:
`to_do`, `in_progress`, `completed`, `on_hold_client`, `on_hold_internal`.

- `on_hold_client` = waiting on Jay or the RMD/client side. Shows to the client.
- `on_hold_internal` = waiting on an internal party. Never shows to the client.

---

## What is NOT included yet

- The weekly dashboard generator and the client-update draft generator, reading
  from this database. That is the next build.
- A friendly form for the team to click statuses. Right now updates go through
  the API. If the team needs a simpler front door, that gets added on top of
  this same database without changing the core.

## A note on ClickUp
This agent uses its own database, not ClickUp, because the ClickUp connector is
authed to an account that is not a member of the RMD workspace. If that access is
fixed later, tasks can be reconciled back to ClickUp using the `origin` and
`external_ref` fields already stored on every task.
