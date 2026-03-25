"""Unit tests for MCP CLI parsing and startup connection behavior."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from ansys.mapdl.mcp import app, launcher
from ansys.mapdl.mcp.server import PyMAPDLMCP


@pytest.mark.unit
def test_main_parses_defaults(monkeypatch):
    """Default args populate mcp._cli_config correctly and doesn't run server."""
    # Prevent actual asyncio.run from running
    with patch.object(asyncio, "run") as mock_run:
        launcher([])
        mock_run.assert_called_once()

    # Ensure mcp._cli_config attached and has defaults
    cfg = getattr(app, "_cli_config", None)
    assert cfg is not None
    assert cfg["transport_type"] == "stdio"
    assert cfg["mapdl_ip"] == "127.0.0.1"
    assert cfg["mapdl_port"] == 50052
    assert cfg["connect_on_startup"] is False
    assert cfg["http_host"] == "127.0.0.1"
    assert cfg["http_port"] == 8080
    assert cfg["cors_origins"] is None


@pytest.mark.unit
def test_main_accepts_http_transport(monkeypatch):
    """Selecting http transport should work now."""
    # Prevent actual asyncio.run from running
    with patch.object(asyncio, "run") as mock_run:
        launcher(["--transport", "http"])
        mock_run.assert_called_once()

    # Ensure mcp._cli_config attached and has http transport
    cfg = getattr(app, "_cli_config", None)
    assert cfg is not None
    assert cfg["transport_type"] == "http"


@pytest.mark.unit
def test_main_invalid_port_raises():
    """Providing an invalid port should cause argparse to exit."""
    from ansys.mapdl.mcp.server import launcher

    with pytest.raises(SystemExit):
        launcher(["--port", "70000"])  # out of 1-65535 should exit


def test_product_startup_attempts_connect_on_startup():
    """When connect_on_startup is True, MCP should attempt to connect to MAPDL."""
    # Prepare a fake Mapdl instance to be returned by launch_mapdl
    fake_mapdl = MagicMock()
    fake_mapdl.exit = MagicMock()

    # Mock launch_mapdl to return our fake instance
    with patch("ansys.mapdl.core.launch_mapdl", return_value=fake_mapdl) as mock_launch:
        # Create MCP instance and attach CLI config directly
        mcp = PyMAPDLMCP()
        setattr(
            mcp,
            "_cli_config",
            {
                "transport_type": "stdio",
                "mapdl_ip": "127.0.0.1",
                "mapdl_port": 50052,
                "connect_on_startup": True,
                "http_host": "127.0.0.1",
                "http_port": 8080,
                "cors_origins": None,
            },
        )
        mcp.create_context()
        mcp.product_startup()

        assert mcp.context.connect_on_startup is True

        # Verify launch_mapdl was called with correct parameters
        mock_launch.assert_called_once_with(
            start_instance=False,
            ip="127.0.0.1",
            port=50052,
        )

        # Verify MAPDL instance was stored in context
        assert mcp.context.mapdl == fake_mapdl

        # Test cleanup
        mcp.product_cleanup()
        fake_mapdl.exit.assert_called_once()
