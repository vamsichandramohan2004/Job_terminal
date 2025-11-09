import sqlite3
from pathlib import Path
import threading
from typing import Optional, Dict, Any
import json

DB_PATH = Path.cwd() / 'queue.db'
_SCHEMA_SQL = Path(__file__).parent.joinpath('..', 'db_schema.sql').resolve()

_lock = threading.Lock()

def get_conn():
    # sqlite3 is not fully threadsafe by default; use check_same_thread=False for multi-threaded processes
    conn = sqlite3.connect(str(DB_PATH), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _lock:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = get_conn()
        cur = conn.cursor()
        # read schema file if exists in repository; fallback to embedded
        try:
            sql = _SCHEMA_SQL.read_text()
        except Exception:
            # fallback schema
            sql = """
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, command TEXT NOT NULL, state TEXT NOT NULL, attempts INTEGER NOT NULL,
              max_retries INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              next_attempt INTEGER NOT NULL DEFAULT 0, timeout INTEGER DEFAULT 60
            );
            CREATE TABLE IF NOT EXISTS dlq (
              id TEXT PRIMARY KEY, command TEXT NOT NULL, failed_at TEXT NOT NULL, attempts INTEGER NOT NULL, last_error TEXT
            );
            """
        cur.executescript(sql)
        # set default configs if not present
        cur.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('backoff_base','2')")
        cur.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('max_retries','3')")
        cur.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('job_timeout','60')")
        conn.commit()
        conn.close()

def fetch_one(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row

def fetch_all(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def execute(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid

def execute_many(sql, seq_of_params):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany(sql, seq_of_params)
    conn.commit()
    conn.close()

# Helper to run atomic claim/update
def atomic_claim_job():
    """
    Atomically find a pending job whose next_attempt <= now and mark it processing and increment attempts.
    Returns the job row or None.
    """
    import time
    conn = get_conn()
    cur = conn.cursor()
    now_ts = int(time.time())
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("SELECT id FROM jobs WHERE state='pending' AND next_attempt<=? ORDER BY created_at LIMIT 1", (now_ts,))
        row = cur.fetchone()
        if not row:
            conn.commit()
            return None
        job_id = row['id']
        cur.execute("UPDATE jobs SET state='processing', attempts=attempts+1, updated_at=?, next_attempt=0 WHERE id=? AND state='pending'",
                    (now_ts, job_id))
        # ensure we succeeded to claim
        if cur.rowcount == 0:
            conn.commit()
            return None
        cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        job = cur.fetchone()
        conn.commit()
        return job
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()