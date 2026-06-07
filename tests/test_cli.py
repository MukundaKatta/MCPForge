"""Tests for mcpforge CLI."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from mcpforge.cli import (
    CheckError,
    build_parser,
    create_project,
    read_message,
    run_check,
)


def test_create_project_generates_files(tmp_path: Path) -> None:
    target = tmp_path / "my-server"
    create_project(target, force=False)

    assert (target / "server.py").exists()
    assert (target / "README.md").exists()
    assert (target / ".gitignore").exists()


def test_create_project_refuses_nonempty_without_force(tmp_path: Path) -> None:
    (tmp_path / "existing.txt").write_text("data")
    with pytest.raises(SystemExit):
        create_project(tmp_path, force=False)


def test_create_project_force_overwrites(tmp_path: Path) -> None:
    (tmp_path / "server.py").write_text("old content")
    create_project(tmp_path, force=True)
    content = (tmp_path / "server.py").read_text()
    assert "old content" not in content
    assert "def main" in content


def test_run_check_passes_on_generated_project(tmp_path: Path) -> None:
    create_project(tmp_path, force=False)
    # Should not raise — the generated server must pass its own smoke test.
    run_check(tmp_path)


def test_run_check_accepts_server_py_path(tmp_path: Path) -> None:
    create_project(tmp_path, force=False)
    run_check(tmp_path / "server.py")


def test_run_check_missing_server_exits(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run_check(tmp_path / "nonexistent")


def test_read_message_rejects_invalid_json() -> None:
    body = b'{"jsonrpc":'  # truncated / invalid JSON
    stream = io.BytesIO(b"Content-Length: %d\r\n\r\n%s" % (len(body), body))
    with pytest.raises(CheckError, match="not valid JSON"):
        read_message(stream)


def test_read_message_rejects_truncated_body() -> None:
    # Header claims 100 bytes but only a few are present before EOF.
    stream = io.BytesIO(b"Content-Length: 100\r\n\r\nshort")
    with pytest.raises(CheckError, match="before sending the full message body"):
        read_message(stream)


def test_read_message_rejects_missing_content_length() -> None:
    stream = io.BytesIO(b"X-Other: 1\r\n\r\n{}")
    with pytest.raises(CheckError, match="missing a Content-Length header"):
        read_message(stream)


def test_build_parser_init_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["init", "/some/path"])
    assert args.command == "init"
    assert args.path == "/some/path"
    assert args.force is False


def test_build_parser_check_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["check", "/some/path"])
    assert args.command == "check"
    assert args.path == "/some/path"


def test_build_parser_no_command_exits() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
