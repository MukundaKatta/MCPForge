"""Command line interface for MCPForge."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .templates import GITIGNORE, STARTER_README, STARTER_SERVER


class CheckError(RuntimeError):
    """Raised when server validation fails."""


def send_message(stream, message: dict[str, Any]) -> None:
    encoded = json.dumps(message).encode("utf-8")
    stream.write(f"Content-Length: {len(encoded)}\r\n\r\n".encode("utf-8"))
    stream.write(encoded)
    stream.flush()


def read_message(stream) -> dict[str, Any]:
    content_length = None
    while True:
        line = stream.readline()
        if not line:
            raise CheckError("Server closed the stdio stream unexpectedly.")
        if line in (b"\r\n", b"\n"):
            break
        header = line.decode("utf-8").strip()
        if header.lower().startswith("content-length:"):
            content_length = int(header.split(":", 1)[1].strip())
    if content_length is None:
        raise CheckError("Server response was missing a Content-Length header.")
    body = stream.read(content_length)
    return json.loads(body.decode("utf-8"))


def create_project(path: Path, force: bool) -> None:
    if path.exists() and any(path.iterdir()) and not force:
        raise SystemExit(
            f"Refusing to initialize non-empty directory: {path}. Use --force to overwrite files."
        )

    path.mkdir(parents=True, exist_ok=True)
    (path / "server.py").write_text(STARTER_SERVER, encoding="utf-8")
    (path / "README.md").write_text(STARTER_README, encoding="utf-8")
    (path / ".gitignore").write_text(GITIGNORE, encoding="utf-8")

    print(f"Created starter MCP server at {path}")
    print("Next steps:")
    print(f"  cd {path}")
    print("  python server.py")
    print("  mcpforge check .")


def run_check(path: Path) -> None:
    server_path = path / "server.py" if path.is_dir() else path
    if not server_path.exists():
        raise SystemExit(f"Could not find server entry point at {server_path}")

    process = subprocess.Popen(
        [sys.executable, str(server_path)],
        cwd=str(server_path.parent),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise SystemExit("Could not start validation process.")

    check_error: CheckError | None = None
    try:
        send_message(
            process.stdin,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "mcpforge", "version": "0.1.0"},
                },
            },
        )
        initialize_response = read_message(process.stdout)
        result = initialize_response.get("result", {})
        if "serverInfo" not in result or "capabilities" not in result:
            raise CheckError("Initialize response did not include serverInfo and capabilities.")

        send_message(
            process.stdin,
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )

        for request_id, method, expected_key in (
            (2, "tools/list", "tools"),
            (3, "resources/list", "resources"),
            (4, "prompts/list", "prompts"),
        ):
            send_message(
                process.stdin,
                {"jsonrpc": "2.0", "id": request_id, "method": method, "params": {}},
            )
            response = read_message(process.stdout)
            payload = response.get("result", {})
            if expected_key not in payload:
                raise CheckError(f"{method} did not return a '{expected_key}' payload.")

        server_info = result["serverInfo"]
        print("PASS: stdio server handshake succeeded.")
        print(f"Server: {server_info.get('name', 'unknown')} {server_info.get('version', '')}".strip())
        print("Verified methods: initialize, tools/list, resources/list, prompts/list")
    except CheckError as exc:
        check_error = exc
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

    if check_error is not None:
        stderr_output = process.stderr.read().decode("utf-8").strip()
        print(f"FAIL: {check_error}", file=sys.stderr)
        if stderr_output:
            print("\nServer stderr:\n" + stderr_output, file=sys.stderr)
        raise SystemExit(1) from check_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scaffold and validate MCP server projects.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a starter MCP server project.")
    init_parser.add_argument("path", help="Directory to create.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite generated files in a non-empty directory.")

    check_parser = subparsers.add_parser("check", help="Run a local stdio smoke check against a server.")
    check_parser.add_argument("path", help="Project directory or server.py path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        create_project(Path(args.path).resolve(), args.force)
        return 0

    if args.command == "check":
        run_check(Path(args.path).resolve())
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
