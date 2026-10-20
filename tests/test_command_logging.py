# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import base64
from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

from ansys.mapdl.core.mapdl_core import _MapdlCore
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
import pytest

from ansys.mapdl.mcp._command_logging import (
    _allocate_log,
    _attach_main_log,
    _register_log,
    _retire_native_log,
)
from ansys.mapdl.mcp.server import PyMAPDLAppContext, PyMAPDLMCP
from ansys.mapdl.mcp.tools import (
    connect_to_mapdl,
    disconnect_from_mapdl,
    launch_mapdl_session,
    list_command_logs,
    read_command_log,
)


class NativeLogClient:
    open_apdl_log = _MapdlCore.open_apdl_log
    _close_apdl_log = _MapdlCore._close_apdl_log

    def __init__(self, **kwargs):
        self._apdl_log = None
        self._log = logging.getLogger(__name__)
        self.ip = self._ip = kwargs.get("ip", "127.0.0.1")
        self.port = self._port = kwargs.get("port", 50052)
        self.version = "26.1"
        self.directory = "."
        self.exited = False

    def exit(self):
        self.exited = True


def payload(result):
    return json.loads(result.content[0].text)


@pytest.fixture
def logged_context(mock_context, tmp_path):
    mock_context.request_context.lifespan_context = PyMAPDLAppContext(apdl_log_dir=tmp_path)
    return mock_context


@pytest.mark.unit
def test_native_files_are_unique_and_readable_after_retirement(logged_context):
    context = logged_context.request_context.lifespan_context
    first, second = NativeLogClient(), NativeLogClient()
    _attach_main_log(context, first)
    first._apdl_log.write("/COM,first\n")
    _retire_native_log(first)
    _attach_main_log(context, second)
    second._apdl_log.write("/COM,second\n")
    _retire_native_log(second)
    context.mapdl = None
    page = payload(list_command_logs(logged_context, limit=1))
    assert page["enabled"] is True
    assert page["next_offset"] == 1
    first_id = page["logs"][0]["log_id"]
    second_id = payload(list_command_logs(logged_context, offset=1))["logs"][0]["log_id"]
    assert first_id != second_id
    for log_id, command in [(first_id, b"/COM,first"), (second_id, b"/COM,second")]:
        result = payload(read_command_log(logged_context, log_id))
        assert result["source"] == "main"
        assert command in base64.b64decode(result["data_base64"])
    assert len({ref.path for ref in context.command_logs.values()}) == 2


@pytest.mark.unit
def test_exact_byte_pages_growth_and_eof(logged_context):
    context = logged_context.request_context.lifespan_context
    client = NativeLogClient()
    _attach_main_log(context, client)
    _retire_native_log(client)
    log_id, ref = next(iter(context.command_logs.items()))
    ref.path.write_bytes(b"A\xc3\xa9Z")
    page = payload(read_command_log(logged_context, log_id, offset=1, max_bytes=1))
    assert page == {
        "success": True,
        "log_id": log_id,
        "source": "main",
        "data_base64": "ww==",
        "size_bytes": 4,
        "next_offset": 2,
    }
    with ref.path.open("ab") as stream:
        stream.write(b"!")
    page = payload(read_command_log(logged_context, log_id, offset=2, max_bytes=3))
    assert base64.b64decode(page["data_base64"]) == b"\xa9Z!"
    assert page["size_bytes"] == page["next_offset"] == 5
    assert payload(read_command_log(logged_context, log_id, offset=5))["data_base64"] == ""
    assert payload(read_command_log(logged_context, log_id, offset=6)) == {
        "success": False,
        "error": "Byte offset is out of range.",
    }


@pytest.mark.unit
@pytest.mark.parametrize("offset,limit", [(-1, 1), (True, 1), (0, 0), (0, 101), (0.5, 1)])
def test_invalid_catalogue_pages(logged_context, offset, limit):
    result = payload(list_command_logs(logged_context, offset=offset, limit=limit))
    assert result == {
        "success": False,
        "error": "offset must be a nonnegative integer and limit must be 1-100.",
    }


@pytest.mark.unit
@pytest.mark.parametrize("offset,max_bytes", [(-1, 1), (True, 1), (0, 0), (0, 65537), (0, False)])
def test_invalid_byte_pages(logged_context, offset, max_bytes):
    result = payload(read_command_log(logged_context, "unknown", offset, max_bytes))
    assert result == {
        "success": False,
        "error": "offset must be a nonnegative integer and max_bytes must be 1-65536.",
    }


@pytest.mark.unit
def test_disabled_unknown_missing_and_read_errors(logged_context):
    disabled = SimpleNamespace(
        request_context=SimpleNamespace(lifespan_context=PyMAPDLAppContext())
    )
    assert payload(list_command_logs(disabled)) == {
        "success": True,
        "enabled": False,
        "logs": [],
        "next_offset": None,
    }
    assert payload(read_command_log(disabled, "unknown"))["error"] == "Command logging is disabled."
    assert payload(read_command_log(logged_context, str(Path(__file__)))) == {
        "success": False,
        "error": "Unknown command log ID.",
    }
    context = logged_context.request_context.lifespan_context
    client = NativeLogClient()
    _attach_main_log(context, client)
    _retire_native_log(client)
    log_id, ref = next(iter(context.command_logs.items()))
    ref.path.unlink()
    assert payload(read_command_log(logged_context, log_id))["error"] == (
        "Command log file is missing."
    )
    ref.path.mkdir()
    assert payload(read_command_log(logged_context, log_id))["error"].startswith(
        "Cannot read command log:"
    )
    assert payload(list_command_logs(logged_context, offset=2))["error"] == (
        "Catalogue offset is out of range."
    )


@pytest.mark.unit
def test_each_context_owns_a_new_run_directory(tmp_path):
    one = PyMAPDLAppContext(apdl_log_dir=tmp_path)
    two = PyMAPDLAppContext(apdl_log_dir=tmp_path)
    assert one.command_log_dir != two.command_log_dir
    assert one.command_log_dir.parent == two.command_log_dir.parent == tmp_path


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["connect", "launch"])
async def test_attachment_failure_keeps_external_solver_and_cleans_owned_launch(
    logged_context, operation
):
    client = NativeLogClient()
    target = "ansys.mapdl.core.Mapdl" if operation == "connect" else "ansys.mapdl.core.launch_mapdl"
    with (
        patch(target, return_value=client),
        patch.object(client, "open_apdl_log", side_effect=OSError("disk full")),
    ):
        result = await (
            connect_to_mapdl(logged_context)
            if operation == "connect"
            else launch_mapdl_session(logged_context)
        )
    assert "Failed to attach native main command log: disk full" in result.content[0].text
    assert client.exited is (operation == "launch")
    assert logged_context.request_context.lifespan_context.mapdl is None
    assert payload(list_command_logs(logged_context))["logs"] == []


@pytest.mark.unit
def test_startup_attachment_failure_is_explicit_without_exiting_external_solver(tmp_path):
    server = PyMAPDLMCP()
    server._cli_config = {"connect_on_startup": True, "apdl_log_dir": tmp_path}
    context = server.create_context()
    client = NativeLogClient()
    with (
        patch("ansys.mapdl.core.Mapdl", return_value=client),
        patch.object(client, "open_apdl_log", side_effect=OSError("disk full")),
    ):
        with pytest.raises(RuntimeError, match="Failed to attach native main command log"):
            server.product_startup()
    assert client.exited is False
    assert context.mapdl is None


@pytest.mark.unit
def test_read_does_not_cross_open_handle_size_snapshot(logged_context):
    import os

    context = logged_context.request_context.lifespan_context
    client = NativeLogClient()
    _attach_main_log(context, client)
    _retire_native_log(client)
    log_id, ref = next(iter(context.command_logs.items()))
    ref.path.write_bytes(b"old")
    real_fstat = os.fstat

    def grow_after_snapshot(fd):
        stat = real_fstat(fd)
        with ref.path.open("ab") as stream:
            stream.write(b"new")
        return stat

    with patch("ansys.mapdl.mcp.tools.os.fstat", side_effect=grow_after_snapshot):
        page = payload(read_command_log(logged_context, log_id))
    assert base64.b64decode(page["data_base64"]) == b"old"
    assert page["size_bytes"] == page["next_offset"] == 3
    assert ref.path.read_bytes() == b"oldnew"


@pytest.mark.unit
def test_native_exclusive_open_preserves_existing_evidence(tmp_path):
    path = tmp_path / "existing.log"
    path.write_bytes(b"existing evidence")
    client = NativeLogClient()
    with pytest.raises(FileExistsError):
        client.open_apdl_log(str(path), mode="x")
    assert path.read_bytes() == b"existing evidence"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_main_connection_publishes_attached_log_and_retires_on_disconnect(logged_context):
    client = NativeLogClient()
    with patch("ansys.mapdl.core.Mapdl", return_value=client):
        connected = await connect_to_mapdl(logged_context)
    assert "Successfully connected to MAPDL" in connected.content[0].text
    handle = client._apdl_log
    client._apdl_log.write("/COM,consumer command\n")
    disconnected = await disconnect_from_mapdl(logged_context)
    assert "Successfully disconnected" in disconnected.content[0].text
    assert handle.closed is True
    log_id = payload(list_command_logs(logged_context))["logs"][0]["log_id"]
    assert b"/COM,consumer command" in base64.b64decode(
        payload(read_command_log(logged_context, log_id))["data_base64"]
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reconnect_retires_stale_main_log_before_attaching_replacement(logged_context):
    context = logged_context.request_context.lifespan_context
    stale = NativeLogClient()
    stale._exited = True
    context.mapdl = stale
    _attach_main_log(context, stale)
    old_handle = stale._apdl_log
    replacement = NativeLogClient()
    with patch("ansys.mapdl.core.Mapdl", return_value=replacement):
        result = await connect_to_mapdl(logged_context)
    assert "Successfully connected to MAPDL" in result.content[0].text
    assert old_handle.closed is True
    assert context.mapdl is replacement
    assert [ref.source for ref in context.command_logs.values()] == ["main", "main"]
    stale.exit()
    _retire_native_log(replacement)
    replacement.exit()


@pytest.mark.unit
def test_startup_client_is_logged_and_shutdown_keeps_evidence(tmp_path):
    server = PyMAPDLMCP()
    server._cli_config = {"connect_on_startup": True, "apdl_log_dir": tmp_path}
    context = server.create_context()
    client = NativeLogClient()
    with patch("ansys.mapdl.core.Mapdl", return_value=client):
        server.product_startup()
    assert context.mapdl is client
    client._apdl_log.write("/COM,startup-user\n")
    handle = client._apdl_log
    server.product_cleanup()
    assert handle.closed is True and client.exited is True
    assert b"/COM,startup-user" in next(iter(context.command_logs.values())).path.read_bytes()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_failure_is_explicit_and_still_cleans_owned_client(logged_context):
    context = logged_context.request_context.lifespan_context
    client = NativeLogClient()
    _attach_main_log(context, client)
    context.mapdl = client
    with patch.object(client, "_close_apdl_log", side_effect=OSError("close failed")):
        result = await disconnect_from_mapdl(logged_context)
    assert result.content[0].text == "Error during disconnect: close failed"
    assert client.exited is True
    assert context.mapdl is None


@pytest.mark.unit
@pytest.mark.parametrize("max_bytes", [1, 65536])
def test_large_file_pages_respect_byte_cap(logged_context, max_bytes):
    context = logged_context.request_context.lifespan_context
    client = NativeLogClient()
    _attach_main_log(context, client)
    _retire_native_log(client)
    log_id, ref = next(iter(context.command_logs.items()))
    ref.path.write_bytes(b"x" * 70000)
    result = payload(read_command_log(logged_context, log_id, max_bytes=max_bytes))
    assert base64.b64decode(result["data_base64"]) == b"x" * max_bytes
    assert result["next_offset"] == max_bytes
    assert result["size_bytes"] == 70000


@pytest.fixture
def logging_mcp_server(tmp_path):
    context = PyMAPDLAppContext(apdl_log_dir=tmp_path)
    allocations = []
    for source, data in [("main", b"A\xc3\xa9Z"), ("python", b"/COM,second\n")]:
        allocation = _allocate_log(context, source)
        assert allocation is not None
        log_id, ref = allocation
        ref.path.write_bytes(data)
        _register_log(context, allocation)
        allocations.append(log_id)

    @asynccontextmanager
    async def lifespan(server):
        yield context

    server = FastMCP("logging-boundary", lifespan=lifespan)
    for tool in [
        list_command_logs,
        read_command_log,
        connect_to_mapdl,
        launch_mapdl_session,
        disconnect_from_mapdl,
    ]:
        server.add_tool(tool)
    return server, context, allocations


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mcp_retrieval_rejects_non_integer_inputs(logging_mcp_server):
    server, _, log_ids = logging_mcp_server
    async with Client(server) as client:
        for tool, arguments, parameter in [
            ("list_command_logs", {"offset": 0, "limit": 1}, "offset"),
            ("list_command_logs", {"offset": 0, "limit": 1}, "limit"),
            (
                "read_command_log",
                {"log_id": log_ids[0], "offset": 0, "max_bytes": 1},
                "offset",
            ),
            (
                "read_command_log",
                {"log_id": log_ids[0], "offset": 0, "max_bytes": 1},
                "max_bytes",
            ),
        ]:
            for value in [True, False, "0", "1", "1.0", 0.0, 1.0, 1.5, None]:
                with pytest.raises(ToolError, match="valid integer"):
                    await client.call_tool(tool, {**arguments, parameter: value})
        assert payload(await client.call_tool("list_command_logs", {"offset": 0, "limit": 1})) == {
            "success": True,
            "enabled": True,
            "logs": [{"log_id": log_ids[0], "source": "main"}],
            "next_offset": 1,
        }
        assert payload(
            await client.call_tool(
                "read_command_log",
                {"log_id": log_ids[0], "offset": 1, "max_bytes": 1},
            )
        ) == {
            "success": True,
            "log_id": log_ids[0],
            "source": "main",
            "data_base64": "ww==",
            "size_bytes": 4,
            "next_offset": 2,
        }
        assert payload(
            await client.call_tool(
                "read_command_log",
                {"log_id": log_ids[0], "offset": 0, "max_bytes": 65536},
            )
        ) == {
            "success": True,
            "log_id": log_ids[0],
            "source": "main",
            "data_base64": "QcOpWg==",
            "size_bytes": 4,
            "next_offset": 4,
        }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mcp_catalogue_end_and_huge_offsets(logging_mcp_server):
    server, context, log_ids = logging_mcp_server
    async with Client(server) as client:
        result = await client.call_tool("list_command_logs", {"offset": 1, "limit": 100})
        assert payload(result) == {
            "success": True,
            "enabled": True,
            "logs": [{"log_id": log_ids[1], "source": "python"}],
            "next_offset": None,
        }
        assert payload(await client.call_tool("list_command_logs", {"offset": 2, "limit": 1})) == {
            "success": True,
            "enabled": True,
            "logs": [],
            "next_offset": None,
        }
        for offset in [3, sys.maxsize, sys.maxsize + 1, 10**100]:
            result = await client.call_tool("list_command_logs", {"offset": offset, "limit": 1})
            assert payload(result) == {
                "success": False,
                "error": "Catalogue offset is out of range.",
            }
        context.command_logs.clear()
        result = await client.call_tool("list_command_logs", {"offset": 0, "limit": 100})
        assert payload(result) == {
            "success": True,
            "enabled": True,
            "logs": [],
            "next_offset": None,
        }


@pytest.mark.unit
@pytest.mark.parametrize("offset", [1, sys.maxsize, sys.maxsize + 1, 10**100])
def test_direct_catalogue_rejects_beyond_end_before_slicing(logged_context, offset):
    assert payload(list_command_logs(logged_context, offset=offset, limit=100)) == {
        "success": False,
        "error": "Catalogue offset is out of range.",
    }
    assert payload(list_command_logs(logged_context, offset=0, limit=100)) == {
        "success": True,
        "enabled": True,
        "logs": [],
        "next_offset": None,
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_clients_share_logs_across_disconnect_and_reconnect(logging_mcp_server):
    server, context, _ = logging_mcp_server
    first_client = NativeLogClient()
    second_client = NativeLogClient()
    async with Client(server) as first, Client(server) as second:
        with patch("ansys.mapdl.core.Mapdl", return_value=first_client):
            connected = await first.call_tool("connect_to_mapdl", {})
        assert "Successfully connected to MAPDL" in connected.content[0].text
        first_client._apdl_log.write("/COM,shared-client\n")
        page = payload(await second.call_tool("list_command_logs", {}))
        entry = page["logs"][-1]
        assert entry["source"] == "main"

        disconnected = await first.call_tool("disconnect_from_mapdl", {})
        assert "Successfully disconnected" in disconnected.content[0].text
        retrieved = payload(await second.call_tool("read_command_log", {"log_id": entry["log_id"]}))
        assert b"/COM,shared-client" in base64.b64decode(retrieved["data_base64"])

        with patch("ansys.mapdl.core.Mapdl", return_value=second_client):
            reconnected = await second.call_tool("connect_to_mapdl", {})
        assert "Successfully connected to MAPDL" in reconnected.content[0].text
        assert first_client._apdl_log is None
        assert context.mapdl is second_client
        assert payload(await first.call_tool("list_command_logs", {}))["logs"][-1]["source"] == (
            "main"
        )
        _retire_native_log(second_client)
        second_client.exit()


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("failed_transition", ["connect", "launch", "disconnect", "retirement"])
async def test_failed_main_transitions_preserve_shared_log_retrieval(
    logging_mcp_server, failed_transition
):
    server, context, log_ids = logging_mcp_server
    client = NativeLogClient()
    async with Client(server) as first, Client(server) as second:
        with patch("ansys.mapdl.core.Mapdl", return_value=client):
            connected = await first.call_tool("connect_to_mapdl", {})
        assert "Successfully connected to MAPDL" in connected.content[0].text
        if failed_transition == "disconnect":
            with patch.object(client, "exit", side_effect=RuntimeError("exit failed")):
                result = await second.call_tool("disconnect_from_mapdl", {})
            assert "exit failed" in result.content[0].text
        elif failed_transition == "retirement":
            client._exited = True
            with patch.object(
                client, "_close_apdl_log", side_effect=RuntimeError("retirement failed")
            ):
                result = await second.call_tool("connect_to_mapdl", {})
            assert "retirement failed" in result.content[0].text
            assert context.mapdl is client
        else:
            client._exited = True
            target = (
                "ansys.mapdl.core.Mapdl"
                if failed_transition == "connect"
                else "ansys.mapdl.core.launch_mapdl"
            )
            with patch(target, side_effect=RuntimeError("replacement failed")):
                tool = (
                    "connect_to_mapdl" if failed_transition == "connect" else "launch_mapdl_session"
                )
                result = await second.call_tool(tool, {})
            assert "replacement failed" in result.content[0].text
            assert context.mapdl is None

        for reader in [first, second]:
            result = payload(await reader.call_tool("read_command_log", {"log_id": log_ids[0]}))
            assert base64.b64decode(result["data_base64"]) == b"A\xc3\xa9Z"

        recovered = NativeLogClient()
        with patch("ansys.mapdl.core.Mapdl", return_value=recovered):
            connected = await first.call_tool("connect_to_mapdl", {})
        assert "Successfully connected to MAPDL" in connected.content[0].text
        assert context.mapdl is recovered
        for reader in [first, second]:
            result = payload(await reader.call_tool("read_command_log", {"log_id": log_ids[0]}))
            assert base64.b64decode(result["data_base64"]) == b"A\xc3\xa9Z"
        _retire_native_log(recovered)
        recovered.exit()
        client.exit()
