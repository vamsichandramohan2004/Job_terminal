import subprocess
import time
import os
from pathlib import Path

ROOT = Path.cwd()

def run(cmd):
    print(f"$ {cmd}")
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p.stdout.decode())
    if p.stderr:
        print(p.stderr.decode())
    return p.returncode

def run_smoke():
    # Ensure clean DB
    db = ROOT / 'queue.db'
    if db.exists():
        db.unlink()
    # enqueue success and failing job
    run('./queuectl enqueue \'{"id":"smoke_ok","command":"bash -c \\"echo ok; exit 0\\"","max_retries":2}\'')
    run('./queuectl enqueue \'{"id":"smoke_fail","command":"bash -c \\"exit 1\\"","max_retries":2}\'')
    # start worker in background
    p = subprocess.Popen(['./queuectl','worker','start','--count','1'])
    print("Worker started, waiting 6s ...")
    time.sleep(6)
    # check status and dlq
    run('./queuectl status')
    run('./queuectl dlq list')
    # cleanup
    p.terminate()
    p.wait(timeout=5)
    print("Smoke test finished")

if __name__ == '__main__':
    run_smoke()
