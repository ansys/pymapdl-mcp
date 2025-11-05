"""Integration tests for PyMAPDL MCP Server.

These tests require a running MAPDL instance and are marked as 'integration'.
Run with: pytest -m integration

To skip integration tests, run: pytest -m "not integration"
"""

import pytest

from ansys.mapdl.mcp import check_mapdl_status, run_mapdl_command, write_comment


@pytest.mark.integration
@pytest.mark.slow
class TestMapdlIntegration:
    """Integration tests that require a real MAPDL connection."""

    @pytest.fixture(scope="class")
    def real_mapdl(self):
        """
        Fixture to connect to a real MAPDL instance.

        This requires MAPDL to be running on localhost:50052.
        Skip these tests if MAPDL is not available.
        """
        try:
            from ansys.mapdl.core import Mapdl

            mapdl = Mapdl(
                start_instance=False,
                ip="localhost",
                port=50052,
                cleanup_on_exit=False,
                loglevel="ERROR",
            )

            yield mapdl

            # Cleanup after tests
            # Don't exit since MAPDL is running externally

        except Exception as e:
            pytest.skip(f"MAPDL not available: {e}")

    @pytest.fixture
    def real_context(self, real_mapdl):
        """Create a real context with actual MAPDL connection."""
        from unittest.mock import MagicMock

        from ansys.mapdl.mcp.mpc import AppContext

        context = MagicMock()
        context.request_context = MagicMock()
        context.request_context.lifespan_context = AppContext(mapdl=real_mapdl)

        return context

    def test_real_check_mapdl_status(self, real_context):
        """Test checking MAPDL status with a real connection."""
        result = check_mapdl_status(real_context)

        assert isinstance(result, str)
        assert "MAPDL is available" in result
        assert "Version" in result

    def test_real_write_comment(self, real_context):
        """Test writing a comment with a real MAPDL connection."""
        comment = "Integration test comment"
        result = write_comment(real_context, comment)

        assert isinstance(result, str)
        assert "Comment written successfully" in result

    def test_real_run_command(self, real_context):
        """Test running a MAPDL command with a real connection."""
        # Use a safe command that doesn't affect the model
        command = "/INQUIRE,RELEASE"
        result = run_mapdl_command(real_context, command)

        assert isinstance(result, str)
        assert "MAPDL command executed successfully" in result

    def test_real_prep7_workflow(self, real_context):
        """Test a basic PREP7 workflow with real MAPDL."""
        # Clear any existing model
        run_mapdl_command(real_context, "/CLEAR")

        # Enter preprocessor
        result = run_mapdl_command(real_context, "/PREP7")
        assert "executed successfully" in result

        # Write a comment
        result = write_comment(real_context, "Starting PREP7 workflow")
        assert "Comment written successfully" in result

        # Define element type
        result = run_mapdl_command(real_context, "ET,1,SOLID185")
        assert "executed successfully" in result

        # Define material property
        result = run_mapdl_command(real_context, "MP,EX,1,200E9")
        assert "executed successfully" in result
