import os
import subprocess
import json
import time
from pathlib import Path
import sqlite3

ROOT = Path.cwd()

def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode(), p.stderr.decode()

def setup_module():
    # remove DB if exists
    db = ROOT / 'queue.db'
    if db.exists():
        db.unlink()

def test_enqueue_and_worker_completion(tmp_path):
    # enqueue a job which exits 0
    cmd = f'./queuectl enqueue \'{{"id":"t-job-1","command":"bash -c \\"echo hello; exit 0\\"","max_retries":2}}\''
    rc, out, err = run_cmd(cmd)
    assert rc == 0
    assert "Enqueued" in out

    # start a worker in background (run as a process)
    p = subprocess.Popen(['./queuectl','worker','start','--count','1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # give worker time to pick up job

    # check DB for completed status
    conn = sqlite3.connect('queue.db')
    cur = conn.cursor()
    cur.execute("SELECT state FROM jobs WHERE id='t-job-1'")
    row = cur.fetchone()
    # job may be completed and still present or removed; ensure either completed or absent
    if row:
        assert row[0] == 'completed'
    conn.close()

    # kill worker
    p.terminate()
    p.wait(timeout=5)
