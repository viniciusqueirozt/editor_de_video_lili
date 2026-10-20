"""Operações explícitas para o Codex atuar sobre o mesmo projeto da interface."""

import argparse
import json
from pathlib import Path

from .client import Client


def main():
    parser = argparse.ArgumentParser(description="Lili — comandos para edição assistida")
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    create = sub.add_parser("create")
    create.add_argument("--name", required=True)
    create.add_argument("--script-file")
    for command in ("get", "context", "jobs"):
        sub.add_parser(command).add_argument("project_id")
    upload = sub.add_parser("import")
    upload.add_argument("project_id")
    upload.add_argument("--file", required=True)
    edit = sub.add_parser("edit")
    edit.add_argument("project_id")
    edit.add_argument("--operation", required=True)
    edit.add_argument("--revision", type=int, required=True)
    edit.add_argument("--args-file", required=True)
    export = sub.add_parser("export")
    export.add_argument("project_id")
    export.add_argument("--revision", type=int, required=True)
    export.add_argument("--quality", choices=("full", "preview"), default="full")
    sub.add_parser("job").add_argument("job_id")
    args = parser.parse_args()
    client = Client(args.url)
    try:
        if args.command == "list":
            result = client.call("GET", "/api/projects")
        elif args.command == "create":
            script = Path(args.script_file).read_text(encoding="utf-8") if args.script_file else ""
            result = client.call("POST", "/api/projects", {"name": args.name, "script": script})
        elif args.command == "import":
            result = client.upload(args.project_id, args.file)
        elif args.command == "edit":
            result = client.call("POST", f"/api/projects/{args.project_id}/commands", {
                "operation": args.operation, "args": json.loads(Path(args.args_file).read_text(encoding="utf-8-sig")),
                "expected_revision": args.revision, "actor": "codex"})
        elif args.command == "export":
            result = client.call("POST", f"/api/projects/{args.project_id}/exports", {"expected_revision": args.revision, "quality": args.quality})
        elif args.command == "job":
            result = client.call("GET", f"/api/jobs/{args.job_id}")
        else:
            suffix = "" if args.command == "get" else "/" + args.command
            result = client.call("GET", f"/api/projects/{args.project_id}{suffix}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
