# QUICKSTART

# create virtualenv & install
bash setup.sh
source .venv/bin/activate

# enqueue example jobs
./queuectl enqueue '{"id":"demo-1","command":"bash -c \"echo demo-1; exit 0\"","max_retries":2}'
./queuectl enqueue '{"id":"demo-2","command":"bash -c \"exit 1\"","max_retries":2}'

# start one worker (foreground)
./queuectl worker start --count 1

# in another terminal check status
./queuectl status
./queuectl dlq list
