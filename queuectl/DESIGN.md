
---

# `DESIGN.md`
Short design doc / architecture.

```markdown
# DESIGN: queuectl

## Components
- CLI `queuectl` (entrypoint) — glue for user actions.
- `src.storage` — SQLite access & atomic claim helper.
- `src.queue_manager` — enqueue/list/dlq handling.
- `src.worker` — worker master and child logic.
- `src.config` — persistent config values.
- `src.dashboard` — minimal Flask monitoring UI.

## Job lifecycle
- `pending` → claimed by worker (atomic) → `processing` → success -> `completed`
- on failure attempt < max_retries -> set `next_attempt` to now + backoff -> `pending`
- on exhausted attempts -> moved to `dlq` table and removed from `jobs`.

## Concurrency control
- Claiming is done using `BEGIN IMMEDIATE` and an `UPDATE` where `state='pending'` to avoid race conditions.

## Persistence
- Jobs and DLQ stored in SQLite `queue.db`.

## Configuration
- `meta` table stores `backoff_base`, `max_retries`, `job_timeout`.