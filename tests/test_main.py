"""Tests for main entry point functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.unit
def test_main_function_exists():
    """Test that main function is defined."""
    from ansys.mapdl.mcp.mpc import main

    assert callable(main)


@pytest.mark.unit
def test_main_entry_point():
    """Test that main entry point can be called."""
    import asyncio

    with patch.object(asyncio, "run") as mock_run:
        with patch("ansys.mapdl.mcp.mpc.mcp") as mock_mcp:
            mock_mcp.run_stdio_async = AsyncMock()

            from ansys.mapdl.mcp.mpc import main

            # Mock asyncio.run to avoid actually starting the server
            main()

            # Verify that asyncio.run was called
            mock_run.assert_called_once()


@pytest.mark.unit
def test_module_main_guard():
    """Test that the module can be imported without running main."""
    # This test verifies that importing the module doesn't automatically
    # start the server (due to if __name__ == "__main__" guard)
    import ansys.mapdl.mcp.mpc

    # If we got here without hanging, the guard works correctly
    assert hasattr(ansys.mapdl.mcp.mpc, "main")
