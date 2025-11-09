import json
import time
from . import storage
from .models import Job
import datetime
import uuid

def enqueue_from_input(payload):
    """
    payload can be a JSON string or a path to a JSON file.
    """
    import os
    if payload.strip().startswith('{'):
        data = json.loads(payload)
    elif os.path.exists(payload):
        data = json.loads(open(payload).read())
    else:
        raise ValueError("enqueue requires either JSON payload or path to JSON file")

    if 'id' not in data:
        data['id'] = str(uuid.uuid4())
    if 'command' not in data:
        raise ValueError("job payload must contain 'command'")

    job = Job(
        id=data['id'],
        command=data['command'],
        state='pending',
        attempts=0,
        max_retries=int(data.get('max_retries') or storage.fetch_one("SELECT value FROM meta WHERE key='max_retries'")['value']),
        created_at=datetime.datetime.utcnow().isoformat()+'Z',
        updated_at=datetime.datetime.utcnow().isoformat()+'Z',
        next_attempt_ts=0,
        timeout=int(data.get('timeout') or storage.fetch_one("SELECT value FROM meta WHERE key='job_timeout'")['value'])
    )
    storage.execute("INSERT OR REPLACE INTO jobs(id,command,state,attempts,max_retries,created_at,updated_at,next_attempt,timeout) VALUES(?,?,?,?,?,?,?,?,?)",
                    (job.id, job.command, job.state, job.attempts, job.max_retries, job.created_at, job.updated_at, job.next_attempt_ts, job.timeout))
    print(f"Enqueued job {job.id}")

def list_jobs(state=None):
    if state:
        rows = storage.fetch_all("SELECT * FROM jobs WHERE state=? ORDER BY created_at", (state,))
    else:
        rows = storage.fetch_all("SELECT * FROM jobs ORDER BY created_at")
    for r in rows:
        print(dict(r))

def list_dlq():
    rows = storage.fetch_all("SELECT * FROM dlq ORDER BY failed_at")
    for r in rows:
        print(dict(r))

def retry_dlq_job(job_id):
    row = storage.fetch_one("SELECT * FROM dlq WHERE id=?", (job_id,))
    if not row:
        print("Job not found in DLQ")
        return
    # move back to jobs with reset attempts and pending state
    now = datetime.datetime.utcnow().isoformat()+'Z'
    storage.execute("INSERT OR REPLACE INTO jobs(id,command,state,attempts,max_retries,created_at,updated_at,next_attempt,timeout) VALUES(?,?,?,?,?,?,?,?,?)",
                    (row['id'], row['command'], 'pending', 0, row['attempts'], now, now, 0, 60))
    storage.execute("DELETE FROM dlq WHERE id=?", (job_id,))
    print(f"Moved {job_id} from DLQ back to pending")

def print_status():
    rows = storage.fetch_all("SELECT state, COUNT(*) as cnt FROM jobs GROUP BY state")
    for r in rows:
        print(f"{r['state']}: {r['cnt']}")
    dlq_count = storage.fetch_one("SELECT COUNT(*) as c FROM dlq")['c']
    print(f"dlq: {dlq_count}")