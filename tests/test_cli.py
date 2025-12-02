"""Unit tests for MCP CLI parsing and startup connection behavior."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.unit
def test_main_parses_defaults(monkeypatch):
    """Default args populate mcp._cli_config correctly and doesn't run server."""
    from ansys.mapdl.mcp import mcp as package_mcp
    from ansys.mapdl.mcp.mcp import main

    # Prevent actual asyncio.run from running
    with patch.object(asyncio, "run") as mock_run:
        main([])
        mock_run.assert_called_once()

    # Ensure mcp._cli_config attached and has defaults
    cfg = getattr(package_mcp, "_cli_config", None)
    assert cfg is not None
    assert cfg["transport_type"] == "stdio"
    assert cfg["mapdl_ip"] == "127.0.0.1"
    assert cfg["mapdl_port"] == 50052
    assert cfg["connect_on_startup"] is False


@pytest.mark.unit
def test_main_rejects_http_transport(monkeypatch, capsys):
    """Selecting http transport prints message and exits with code 2."""
    from ansys.mapdl.mcp.mcp import main

    with pytest.raises(SystemExit) as excinfo:
        main(["--type", "http"])  # should call sys.exit(2)

    assert excinfo.value.code == 2


@pytest.mark.unit
def test_main_invalid_port_raises():
    """Providing an invalid port should cause argparse to exit."""
    from ansys.mapdl.mcp.mcp import main

    with pytest.raises(SystemExit):
        main(["--port", "70000"])  # out of 1-65535 should exit


def test_app_lifespan_attempts_connect_on_startup():
    """When connect_on_startup is True, AppContext should attempt Mapdl()."""
    from ansys.mapdl.mcp.mcp import app_lifespan, mcp

    # Prepare a fake Mapdl instance to be returned by the constructor
    fake_mapdl = MagicMock()
    fake_mapdl.exit = MagicMock()

    # Attach CLI config to server
    setattr(
        mcp,
        "_cli_config",
        {
            "transport_type": "stdio",
            "mapdl_ip": "127.0.0.1",
            "mapdl_port": 50052,
            "connect_on_startup": True,
        },
    )

    # Patch helpers.create_pool so startup populates ctx.pool with our fake_mapdl.
    # app_lifespan calls create_pool(..., ctx=context, ...), so we intercept
    # that call and set the pool directly for this unit test.
    with patch("ansys.mapdl.mcp.helpers.create_pool") as mock_create_pool:

        def _fake_create_pool(*args, **kwargs):
            # ctx can be passed as keyword or positional arg
            ctx = kwargs.get("ctx") if "ctx" in kwargs else (args[0] if args else None)
            if ctx is not None:
                ctx.pool = [fake_mapdl]
            return "ok"

        mock_create_pool.side_effect = _fake_create_pool

        async def runner():
            async with app_lifespan(mcp) as ctx:
                assert ctx.pool is not None
                assert ctx.pool[0] is fake_mapdl

        # Run the async runner synchronously
        asyncio.run(runner())

        # Ensure create_pool was invoked during startup
        mock_create_pool.assert_called()

    # Clean up _cli_config
    delattr(mcp, "_cli_config")
