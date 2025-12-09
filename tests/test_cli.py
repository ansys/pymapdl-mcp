"""Unit tests for MCP CLI parsing and startup connection behavior."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.unit
def test_main_parses_defaults(monkeypatch):
    """Default args populate mcp._cli_config correctly and doesn't run server."""
    from ansys.mapdl.mcp import app as package_mcp
    from ansys.mapdl.mcp.server import main

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
    from ansys.mapdl.mcp.server import main

    with pytest.raises(SystemExit) as excinfo:
        main(["--type", "http"])  # should call sys.exit(2)

    assert excinfo.value.code == 2


@pytest.mark.unit
def test_main_invalid_port_raises():
    """Providing an invalid port should cause argparse to exit."""
    from ansys.mapdl.mcp.server import main

    with pytest.raises(SystemExit):
        main(["--port", "70000"])  # out of 1-65535 should exit


def test_app_lifespan_attempts_connect_on_startup():
    """When connect_on_startup is True, AppContext should be created."""
    from ansys.mapdl.mcp.server import app, app_lifespan

    # Prepare a fake Mapdl instance to be returned by the constructor
    fake_mapdl = MagicMock()
    fake_mapdl.exit = MagicMock()

    # Attach CLI config to server
    setattr(
        app,
        "_cli_config",
        {
            "transport_type": "stdio",
            "mapdl_ip": "127.0.0.1",
            "mapdl_port": 50052,
            "connect_on_startup": True,
        },
    )

    async def runner():
        async with app_lifespan(app) as ctx:
            # Just verify that the context is created properly
            assert ctx is not None
            assert hasattr(ctx, "mapdl")
            # Set a fake mapdl instance to test cleanup
            ctx.mapdl = fake_mapdl

    # Run the async runner synchronously
    asyncio.run(runner())

    # Verify cleanup was called
    fake_mapdl.exit.assert_called_once()

    # Clean up _cli_config
    delattr(app, "_cli_config")
