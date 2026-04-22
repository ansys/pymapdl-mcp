# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: ANSYS MCP SERVER TECHNOLOGY PREVIEW LICENSE AGREEMENT

#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for main entry point functionality."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.unit
def test_main_function_exists():
    """Test that main function is defined."""
    from ansys.mapdl.mcp.server import launcher

    assert callable(launcher)


@pytest.mark.unit
def test_main_entry_point():
    """Test that main entry point can be called."""
    import asyncio

    from ansys.mapdl.mcp.server import app, launcher

    with patch.object(asyncio, "run") as mock_run:
        with patch.object(app, "run_stdio_async", new_callable=AsyncMock):
            # Mock asyncio.run to avoid actually starting the server
            launcher([])

            # Verify that asyncio.run was called with app.run_stdio_async()
            mock_run.assert_called_once()


@pytest.mark.unit
def test_main_with_http_transport():
    """Test that main entry point can be called with HTTP transport."""
    import asyncio

    from ansys.mapdl.mcp.server import app, launcher

    with patch.object(asyncio, "run") as mock_run:
        with patch.object(app, "run_http_async", new_callable=AsyncMock):
            # Mock asyncio.run to avoid actually starting the server
            launcher(["--transport", "http"])

            # Verify that asyncio.run was called
            mock_run.assert_called_once()


@pytest.mark.unit
def test_main_http_with_custom_host_port():
    """Test HTTP transport with custom host and port."""
    import asyncio

    from ansys.mapdl.mcp.server import app, launcher

    with patch.object(asyncio, "run") as mock_run:
        with patch.object(app, "run_http_async", new_callable=AsyncMock):
            launcher(["--transport", "http", "--http-host", "0.0.0.0", "--http-port", "9000"])

            # Verify that asyncio.run was called
            mock_run.assert_called_once()

            # Verify the CLI config was set correctly
            assert hasattr(app, "_cli_config")
            assert app._cli_config["http_host"] == "0.0.0.0"
            assert app._cli_config["http_port"] == 9000


@pytest.mark.unit
def test_main_with_cors_origins():
    """Test HTTP transport with CORS origins."""
    import asyncio

    from ansys.mapdl.mcp.server import app, launcher

    with patch.object(asyncio, "run"):
        with patch.object(app, "run_http_async", new_callable=AsyncMock):
            launcher(
                [
                    "--transport",
                    "http",
                    "--cors-origins",
                    "http://localhost:3000,https://example.com",
                ]
            )

            # Verify CORS origins were parsed correctly
            assert hasattr(app, "_cli_config")
            assert app._cli_config["cors_origins"] == [
                "http://localhost:3000",
                "https://example.com",
            ]


@pytest.mark.unit
def test_mapdl_args_work_with_http():
    """Test that MAPDL connection arguments work with HTTP transport."""
    import asyncio

    from ansys.mapdl.mcp.server import app, launcher

    with patch.object(asyncio, "run"):
        with patch.object(app, "run_http_async", new_callable=AsyncMock):
            launcher(
                [
                    "--transport",
                    "http",
                    "--ip",
                    "192.168.1.100",
                    "--port",
                    "50053",
                    "--connect-on-startup",
                ]
            )

            # Verify MAPDL args were set correctly
            assert hasattr(app, "_cli_config")
            assert app._cli_config["mapdl_ip"] == "192.168.1.100"
            assert app._cli_config["mapdl_port"] == 50053
            assert app._cli_config["connect_on_startup"] is True


@pytest.mark.unit
def test_module_main_guard():
    """Test that the module can be imported without running main."""
    # This test verifies that importing the module doesn't automatically
    # start the server (due to if __name__ == "__main__" guard)
    import ansys.mapdl.mcp

    # If we got here without hanging, the guard works correctly
    assert hasattr(ansys.mapdl.mcp, "launcher")
