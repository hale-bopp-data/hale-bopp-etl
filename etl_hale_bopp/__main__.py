"""CLI entry point for hale-bopp-etl."""

from __future__ import annotations

import argparse
import logging
import sys


def main() -> int:
    parser = argparse.ArgumentParser(prog="hale-bopp-etl", description="Lightweight ETL runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a pipeline by ID")
    run_p.add_argument("pipeline_id", help="Pipeline ID from pipelines.yaml")
    run_p.add_argument("-c", "--config", help="Config file path")

    sub.add_parser("list", help="List available pipelines")

    watch_p = sub.add_parser("watch", help="Watch events directory and trigger pipelines")
    watch_p.add_argument("-i", "--interval", type=int, default=10, help="Poll interval (seconds)")

    wh_p = sub.add_parser("webhook", help="Start webhook receiver")
    wh_p.add_argument("-p", "--port", type=int, default=3001, help="Port")
    wh_p.add_argument("--host", default="0.0.0.0", help="Host")

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.command == "run":
        from etl_hale_bopp.runner import run_by_id
        results = run_by_id(args.pipeline_id, args.config)
        for r in results:
            print(f"  {r['task_id']}: OK")
        return 0

    elif args.command == "list":
        from etl_hale_bopp.runner import list_pipelines
        for p in list_pipelines():
            print(f"  {p['id']:40s} {p['schedule']:20s} {p['description']}")
        return 0

    elif args.command == "watch":
        from etl_hale_bopp.watcher import watch
        watch(args.interval)
        return 0

    elif args.command == "webhook":
        import uvicorn
        uvicorn.run("etl_hale_bopp.webhook_app:app", host=args.host, port=args.port)
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
