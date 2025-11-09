# 🚀 QueueCTL – Background Job Queue System
### 🧠 Backend Developer Internship Assignment  
**Author:** Vamsi Chandra Mohan  
**Tech Stack:** Python 3.11+, Flask, SQLite, Subprocess, Argparse  
**Objective:** Build a CLI-based background job queue system with retry, DLQ, and a minimal dashboard.

---

## 🏗️ 1️⃣ SETUP PROJECT

```bash
# Clone Repository
git clone https://github.com/<your-username>/queuectl.git
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
