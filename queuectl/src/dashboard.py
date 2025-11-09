from flask import Flask, request, jsonify
import sqlite3
import os
import json
from src import queue_manager
import html
import subprocess, sys

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'queue.db')

app = Flask(__name__)

# ---------- DB Connection Helper ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Dashboard UI ----------
@app.route('/')
def index():
    conn = get_db()
    counts = conn.execute("SELECT state, COUNT(*) AS count FROM jobs GROUP BY state").fetchall()
    dlq_count = conn.execute("SELECT COUNT(*) AS count FROM dlq").fetchone()['count']
    jobs = conn.execute("SELECT * FROM jobs ORDER BY updated_at DESC LIMIT 10").fetchall()
    conn.close()

    # Prepare state counts
    states = {row['state']: row['count'] for row in counts}
    pending = states.get('pending', 0)
    processing = states.get('processing', 0)
    completed = states.get('completed', 0)
    failed = states.get('failed', 0)

    # Escape job data to avoid JS/HTML errors
    rows_html = ""
    for j in jobs:
        safe_id = html.escape(j["id"])
        safe_cmd = html.escape(j["command"])
        safe_state = html.escape(j["state"])
        safe_attempts = html.escape(str(j["attempts"]))
        rows_html += (
            f"<tr>"
            f"<td>{safe_id}</td>"
            f"<td>{safe_cmd}</td>"
            f"<td>{safe_state}</td>"
            f"<td>{safe_attempts}</td>"
            f"<td><button onclick=\"retryJob('{safe_id}')\">Retry</button></td>"
            f"</tr>"
        )

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>QueueCTL Dashboard</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #121212;
                color: #f2f2f2;
                text-align: center;
                padding: 40px;
            }}
            h1 {{ color: #00ff99; }}
            .card {{
                display: inline-block;
                background: #1f1f1f;
                border-radius: 10px;
                margin: 20px;
                padding: 20px 40px;
                box-shadow: 0 0 10px #00ff99;
            }}
            .value {{
                font-size: 2rem;
                color: #00ff99;
            }}
            table {{
                margin: auto;
                margin-top: 30px;
                border-collapse: collapse;
                width: 80%;
                background: #1f1f1f;
                border-radius: 10px;
            }}
            th, td {{
                border: 1px solid #00ff99;
                padding: 8px;
            }}
            th {{
                background-color: #00ff99;
                color: black;
            }}
            tr:hover {{
                background-color: #333;
            }}
            input, button {{
                padding: 10px;
                border-radius: 8px;
                border: none;
                margin: 5px;
            }}
            input {{
                width: 250px;
            }}
            button {{
                background-color: #00ff99;
                color: black;
                cursor: pointer;
                font-weight: bold;
            }}
            button:hover {{
                background-color: #00cc7a;
            }}
            .section {{
                margin-top: 40px;
            }}
        </style>
    </head>
    <body>
        <h1>QueueCTL Dashboard</h1>
        <div class="card"><h3>Pending Jobs</h3><div class="value">{pending}</div></div>
        <div class="card"><h3>Processing Jobs</h3><div class="value">{processing}</div></div>
        <div class="card"><h3>Completed Jobs</h3><div class="value">{completed}</div></div>
        <div class="card"><h3>Failed Jobs</h3><div class="value">{failed}</div></div>
        <div class="card"><h3>Dead Letter Queue</h3><div class="value">{dlq_count}</div></div>

        <div class="section">
            <h2> Add Job</h2>
            <input id="job_id" placeholder="Job ID" />
            <input id="job_cmd" placeholder="Command (e.g. echo hello)" />
            <button onclick="enqueueJob()">Add Job</button>
        </div>

        <div class="section">
            <h2> Recent Jobs</h2>
            <table>
                <tr><th>ID</th><th>Command</th><th>State</th><th>Attempts</th><th>Action</th></tr>
                {rows_html}
            </table>
        </div>

        <div class="section">
            <h2> Dead Letter Queue (DLQ)</h2>
            <button onclick="listDLQ()">View DLQ</button>
            <div id="dlqDisplay"></div>
        </div>

        <script>
            async function enqueueJob() {{
                const id = document.getElementById('job_id').value;
                const cmd = document.getElementById('job_cmd').value;
                if (!id || !cmd) return alert('Please provide both Job ID and Command');
                const body = {{id: id, command: cmd}};
                const res = await fetch('/api/enqueue', {{
                    method: 'POST',
                    headers: {{'Content-Type':'application/json'}},
                    body: JSON.stringify(body)
                }});
                const data = await res.json();
                alert(data.message);
                location.reload();
            }}

            async function retryJob(id) {{
                const res = await fetch('/api/retry/' + encodeURIComponent(id), {{ method:'POST' }});
                const data = await res.json();
                alert(data.message);
                location.reload();
            }}

            async function listDLQ() {{
                const res = await fetch('/api/dlq/list');
                const data = await res.json();
                if (data.jobs.length === 0) {{
                    document.getElementById('dlqDisplay').innerHTML = "<p>No DLQ Jobs</p>";
                    return;
                }}
                let html = "<table><tr><th>ID</th><th>Command</th><th>Attempts</th><th>Action</th></tr>";
                data.jobs.forEach(j => {{
                    html += `<tr><td>${{j.id}}</td><td>${{j.command}}</td><td>${{j.attempts}}</td><td><button onclick="retryDLQ('${{j.id}}')">🔁 Retry DLQ</button></td></tr>`;
                }});
                html += "</table>";
                document.getElementById('dlqDisplay').innerHTML = html;
            }}

            async function retryDLQ(id) {{
                const res = await fetch('/api/dlq/retry/' + encodeURIComponent(id), {{ method:'POST' }});
                const data = await res.json();
                alert(data.message);
                location.reload();
            }}
        </script>
    </body>
    </html>
    """
    return html_code


# ---------- API Routes ----------
@app.route('/api/enqueue', methods=['POST'])
def enqueue():
    data = request.get_json(force=True)
    queue_manager.enqueue_from_input(json.dumps(data))
    return jsonify({"message": f"Job {data['id']} enqueued!"})


@app.route('/api/retry/<job_id>', methods=['POST'])
def retry_job(job_id):
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    conn.execute("UPDATE jobs SET state='pending', attempts=0 WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

    # Automatically start a worker for demo
    subprocess.Popen([sys.executable, "queuectl.py", "worker", "start", "--count", "1"])
    return jsonify({"message": f"Job {job_id} reset and worker started!"})


@app.route('/api/dlq/list')
def list_dlq():
    conn = get_db()
    rows = conn.execute("SELECT * FROM dlq").fetchall()
    conn.close()
    return jsonify({"jobs": [dict(row) for row in rows]})


@app.route('/api/dlq/retry/<job_id>', methods=['POST'])
def retry_dlq(job_id):
    queue_manager.retry_dlq_job(job_id)
    return jsonify({"message": f"Job {job_id} moved from DLQ to pending!"})


# ---------- Run Flask ----------
def run(port=5000):
    print(f"🚀 Flask dashboard running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)