#!/usr/bin/env python3
"""
Top-level CLI for queuectl.
Run: ./queuectl <command> ...
"""
import argparse
import sys
from src import queue_manager, config, worker, dashboard

def main():
    parser = argparse.ArgumentParser(prog='queuectl', description='queuectl - background job queue')
    sub = parser.add_subparsers(dest='cmd')

    # enqueue
    p_enq = sub.add_parser('enqueue', help='Enqueue a job JSON')
    p_enq.add_argument('json_payload', help='JSON payload for job, or path to JSON file')

    # worker
    p_worker = sub.add_parser('worker', help='Manage workers')
    p_worker.add_argument('action', choices=['start','stop','status'], help='start | stop | status')
    p_worker.add_argument('--count', type=int, default=1, help='how many worker processes to spawn (start)')

    # status / list
    p_status = sub.add_parser('status', help='Show counts by state')
    p_list = sub.add_parser('list', help='List jobs')
    p_list.add_argument('--state', choices=['pending','processing','completed'], default=None)

    # dlq
    p_dlq = sub.add_parser('dlq', help='Dead letter queue ops')
    dlq_sub = p_dlq.add_subparsers(dest='dlq_cmd')
    dlq_sub.add_parser('list', help='List DLQ jobs')
    p_dlq_retry = dlq_sub.add_parser('retry', help='Retry job from DLQ (move to pending)')
    p_dlq_retry.add_argument('job_id')

    # config
    p_cfg = sub.add_parser('config', help='Get/Set configuration')
    p_cfg.add_argument('action', choices=['get','set'])
    p_cfg.add_argument('key')
    p_cfg.add_argument('value', nargs='?')

    # dashboard
    p_dash = sub.add_parser('dashboard', help='Start minimal dashboard (Flask)')
    p_dash.add_argument('--port', type=int, default=5000)

    # tests
    p_test = sub.add_parser('selftest', help='Run quick smoke tests (blocking)')

    args = parser.parse_args()

    # ensure DB initialized
    config.ensure_db()

    if args.cmd == 'enqueue':
        queue_manager.enqueue_from_input(args.json_payload)
    elif args.cmd == 'worker':
        if args.action == 'start':
            worker.start_master(args.count)
        elif args.action == 'stop':
            worker.stop_master()
        elif args.action == 'status':
            worker.worker_status()
    elif args.cmd == 'status':
        queue_manager.print_status()
    elif args.cmd == 'list':
        queue_manager.list_jobs(args.state)
    elif args.cmd == 'dlq':
        if args.dlq_cmd == 'list':
            queue_manager.list_dlq()
        elif args.dlq_cmd == 'retry':
            queue_manager.retry_dlq_job(args.job_id)
        else:
            print("dlq requires a command: list | retry")
    elif args.cmd == 'config':
        if args.action == 'set' and args.value is not None:
            config.set_config(args.key, args.value)
        elif args.action == 'get':
            print(config.get_config(args.key))
        else:
            print("config usage: config (get|set) key [value]")
    elif args.cmd == 'dashboard':
        dashboard.run(port=args.port)
    elif args.cmd == 'selftest':
        import tests.validate_system as vs
        vs.run_smoke()
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()