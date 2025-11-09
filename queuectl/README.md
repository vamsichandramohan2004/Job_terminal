######################################################################
# 🚀 QueueCTL – Background Job Queue System
# Backend Developer Internship Assignment
######################################################################

👨‍💻 Author: Vamsi Chandra Mohan  
🧠 Tech Stack: Python 3.11+, Flask, SQLite, Subprocess, Argparse  
🎯 Objective: CLI-based background job system with retry, DLQ, dashboard

######################################################################
# 🏗️ 1 SETUP PROJECT
######################################################################

# Clone Repository
https://github.com/vamsichandramohan2004/Job_terminal
cd queuectl

# Create Virtual Environment
python -m venv .venv

# Activate Virtual Environment
# (Linux/Mac)
source .venv/bin/activate
# (Windows)
.venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Initialize Database
bash setup.sh

######################################################################
# 💡 2 CORE FEATURES
######################################################################

# ✅ Persistent Job Queue (SQLite)
# ✅ Multiple Worker Support
# ✅ Retry with Exponential Backoff
# ✅ Dead Letter Queue (DLQ)
# ✅ Configurable Retry & Backoff Base
# ✅ Graceful Worker Shutdown
# ✅ Flask Dashboard (Auto-refresh, Bonus)

######################################################################
# 💻 3 BASIC USAGE
######################################################################

# --- Enqueue a New Job ---
python queuectl.py enqueue '{"id":"job1","command":"echo hello"}'

# --- Enqueue a Failing Job for Retry Test ---
python queuectl.py enqueue '{"id":"fail1","command":"bash -c \"exit 1\""}'

# --- Start 2 Worker Processes ---
python queuectl.py worker start --count 2

# --- Show Job Summary ---
python queuectl.py status

# --- List Jobs by State ---
python queuectl.py list --state pending
python queuectl.py list --state completed

# --- Manage Dead Letter Queue (DLQ) ---
python queuectl.py dlq list
python queuectl.py dlq retry fail1

# --- Config Management ---
python queuectl.py config get max_retries
python queuectl.py config set max_retries 5

# --- Run System Smoke Tests ---
python queuectl.py selftest

######################################################################
# 🌐 4 FLASK DASHBOARD (BONUS FEATURE)
######################################################################

# Launch Dashboard
python queuectl.py dashboard --port 5000

# Open in Browser
# 👉 http://localhost:5000

# Dashboard Features:
#   - Real-time job stats (auto-refresh every 5s)
#   - Add job directly from UI
#   - Retry jobs and DLQ entries
#   - Auto-starts worker on retry
#   - Sleek dark mode design 💚

######################################################################
# 🔄 5 JOB LIFECYCLE
######################################################################

# pending → processing → completed
#        ↘
#         failed → retry (exponential backoff)
#                     ↘
#                      DLQ (after max retries)

# Exponential Backoff Formula:
# delay = base ^ attempts
# Example: base=2 → delays = 1s, 2s, 4s, 8s → DLQ after retries

######################################################################
# 🧪 6 EXAMPLES
######################################################################

# --- Successful Job Example ---
python queuectl.py enqueue '{"id":"ok1","command":"echo Hello QueueCTL"}'
python queuectl.py worker start --count 1
# Output:
# Worker-1: picked job ok1
# Worker-1: completed successfully ✅

# --- Failing Job Example ---
python queuectl.py enqueue '{"id":"fail2","command":"bash -c \"exit 1\""}'
python queuectl.py worker start --count 1
# Output:
# Worker-1: failed (attempt 1), retrying in 2s...
# Worker-1: failed (attempt 3), moving to DLQ ❌

######################################################################
# 📋 7 EVALUATION CHECKLIST
######################################################################

# ✅ Working CLI Application
# ✅ Persistent SQLite Storage
# ✅ Retry + Backoff
# ✅ DLQ Functional
# ✅ Configurable Parameters
# ✅ Graceful Shutdown
# ✅ Multiple Workers
# ✅ Modular Code
# ✅ Self-Test Validation
# ✅ Flask Dashboard (Bonus)
# 💯 All test scenarios passed successfully

######################################################################
# 🧾 9️⃣ SUBMISSION DETAILS
######################################################################

# Assignment: QueueCTL - Backend Developer Internship
# Candidate:  Vamsi Chandra Mohan
# Stack:      Python + Flask + SQLite

# Deliverables:
#   1️⃣ Public GitHub Repository
#   2️⃣ README.md (this file)
#   3️⃣ Demo Video (CLI + Dashboard)
#   4️⃣ DESIGN.md and QUICKSTART.md
#   5️⃣ Verified Working Code

######################################################################
# 💾 11️⃣ PERSISTENCE DETAILS
######################################################################

# Jobs, Config, and DLQ data stored in:
# → queue.db (SQLite)
# Tables:
#   - jobs
#   - dlq
#   - meta
# All data persists after restart ✔️

######################################################################
# ⚙️ 12️⃣ CONFIGURATION
######################################################################

# Configuration stored in SQLite meta table.
# Keys and defaults:
#   max_retries   = 3
#   backoff_base  = 2
#   job_timeout   = 60

# Modify config:
python queuectl.py config set backoff_base 3
python queuectl.py config get backoff_base

######################################################################
# 🌟 13️⃣ BONUS FEATURES
######################################################################

# ✅ Flask Dashboard with Auto-refresh
# ✅ DLQ Retry Support
# ✅ Worker Auto-start on Retry
# ✅ Modular & Clean Architecture
# ✅ 5-Second Auto-update Stats

######################################################################
# 🧠 14️⃣ FUTURE IMPROVEMENTS
######################################################################

# - Add priority queues
# - Implement scheduled jobs
# - Use WebSocket for live dashboard
# - Build REST API endpoints
# - Containerize with Docker

######################################################################
# ✅ 15️⃣ FINAL SUBMISSION CHECKLIST
######################################################################

# [x] All commands functional
# [x] Jobs persist on restart
# [x] Retry + DLQ verified
# [x] Config management works
# [x] Dashboard operational
# [x] Code modular and maintainable
# [x] README + Demo ready

######################################################################
# 🏁 END OF FILE — QueueCTL by Vamsi Chandra Mohan
######################################################################
