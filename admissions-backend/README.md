# Local admissions backend

This local prototype serves the school site and accepts admission submissions at
`POST /api/admissions`. It stores learner and guardian details in a SQLite
database on the computer running the server.

## Run locally

From the repository root, run:

```sh
python3 admissions-backend/server.py
```

Open the local URL printed by the server (usually
`http://127.0.0.1:8000`). Stop it with `Ctrl+C`. The database is created at
`admissions-backend/admissions.sqlite3` and is excluded from Git.

Run backend tests with:

```sh
python3 -m unittest discover -s admissions-backend -p 'test_*.py'
```

## Important

GitHub Pages only hosts static files, so the public website does not send
submissions to this local server. This prototype binds to `127.0.0.1` and is
for local testing only; do not expose it to the internet or use it for real
admissions. Before accepting real learner information, deploy an authenticated,
HTTPS backend with appropriate access controls, backups, retention rules, and
privacy notices. The database contains personal information and must not be
shared or committed.
