#!/usr/bin/env bash
set -e
./queuectl enqueue '{"id":"demo_ok","command":"bash -c \"echo ok; exit 0\"","max_retries":2}'
./queuectl enqueue '{"id":"demo_fail","command":"bash -c \"exit 1\"","max_retries":2}'
# start worker in background (detached)
./queuectl worker start --count 1 &
MASTER_PID=$!
echo "Master started pid $MASTER_PID; will wait 6 seconds"
sleep 6
# show status
./queuectl status
./queuectl dlq list
# stop master
kill $MASTER_PID || true
