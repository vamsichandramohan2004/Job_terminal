import os
import signal
import time
import sys
from multiprocessing import Process, Event
from . import storage, queue_manager, config
import subprocess
import threading
from pathlib import Path
import json

PID_FILE = Path.cwd() / 'queuectl_master.pid'

def _run_command(command, timeout):
    try:
        p = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        out = p.stdout.decode('utf-8', errors='ignore')
        err = p.stderr.decode('utf-8', errors='ignore')
        return p.returncode, out, err
    except subprocess.TimeoutExpired as e:
        return 124, '', f"timeout: {e}"

def worker_loop(worker_id, event:Event):
    """
    Keep claiming jobs and processing them until event.is_set() is True.
    """
    backoff_base = float(config.get_config('backoff_base') or 2.0)
    while not event.is_set():
        job_row = storage.atomic_claim_job()
        if not job_row:
            time.sleep(0.5)
            continue
        job = dict(job_row)
        job_id = job['id']
        attempts = job['attempts']
        max_retries = job['max_retries']
        timeout = job.get('timeout') or int(config.get_config('job_timeout') or 60)
        print(f"[worker {worker_id}] picked job={job_id} attempts={attempts}/{max_retries} cmd={job['command']}")
        rc, out, err = _run_command(job['command'], timeout=timeout)
        now_ts = int(time.time())
        if rc == 0:
            storage.execute("UPDATE jobs SET state=?, updated_at=? WHERE id=?", ('completed', now_ts, job_id))
            print(f"[worker {worker_id}] job {job_id} completed. out={out.strip()}")
        else:
            # failure
            if attempts >= max_retries:
                # move to dlq
                storage.execute("INSERT OR REPLACE INTO dlq(id,command,failed_at,attempts,last_error) VALUES(?,?,?,?,?)",
                                (job_id, job['command'], now_ts, attempts, (err or out)[:2000]))
                storage.execute("DELETE FROM jobs WHERE id=?", (job_id,))
                print(f"[worker {worker_id}] job {job_id} moved to DLQ after {attempts} attempts")
            else:
                # compute exponential backoff: delay = base ** attempts
                delay = int(backoff_base ** attempts)
                next_ts = int(time.time()) + delay
                storage.execute("UPDATE jobs SET state=?, next_attempt=?, updated_at=? WHERE id=?",
                                ('pending', next_ts, now_ts, job_id))
                print(f"[worker {worker_id}] job {job_id} failed rc={rc}; will retry after {delay}s (attempt {attempts}/{max_retries})")

def start_master(count:int=1):
    """
    Spawn a master process that starts `count` worker processes and waits.
    We run master in foreground so user sees output. Master writes PID file.
    Press Ctrl+C to stop (graceful shutdown).
    """
    if PID_FILE.exists():
        print("Master appears to be running (pidfile exists). Stop it first or delete pidfile.")
        return

    config.ensure_db()

    stop_event = Event()
    processes = []
    try:
        # write pidfile for master
        PID_FILE.write_text(str(os.getpid()))
        print(f"Master PID {os.getpid()} (pidfile={PID_FILE})")
        for i in range(count):
            e = Event()
            p = Process(target=_worker_process_entry, args=(i+1,))
            p.start()
            processes.append(p)
            print(f"Started worker pid={p.pid}")
        # wait for children
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Master received KeyboardInterrupt, terminating workers...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        for p in processes:
            p.join(timeout=5)
    finally:
        if PID_FILE.exists():
            try:
                PID_FILE.unlink()
            except Exception:
                pass

def _worker_process_entry(worker_id):
    """
    Entrypoint for each separate process; runs worker_loop until SIGTERM.
    """
    event = Event()

    def _sigterm(signum, frame):
        print(f"[worker {worker_id}] received signal {signum}, stopping after current job")
        event.set()

    signal.signal(signal.SIGTERM, _sigterm)
    # inside a child process, ensure DB available
    storage.init_db = storage.init_db  # noop
    print(f"[worker child {worker_id}] started, pid={os.getpid()}")
    try:
        worker_loop(worker_id, event)
    except KeyboardInterrupt:
        print(f"[worker child {worker_id}] interrupted")
    print(f"[worker child {worker_id}] exiting")

def stop_master():
    if not PID_FILE.exists():
        print("No master pidfile found.")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to master pid {pid}")
    except Exception as e:
        print("Error stopping master:", e)
    finally:
        try:
            PID_FILE.unlink()
        except Exception:
            pass

def worker_status():
    from . import queue_manager
    queue_manager.print_status()
