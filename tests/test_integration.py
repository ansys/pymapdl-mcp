"""Integration tests for PyMAPDL MCP Server.

These tests require a running MAPDL instance and are marked as 'integration'.
Run with: pytest -m integration

To skip integration tests, run: pytest -m "not integration"
"""

import pytest

from ansys.mapdl.mcp import (
    check_mapdl_status,
    list_mapdl_instances,
    run_mapdl_command,
    write_comment,
)


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


@pytest.mark.integration
class TestListMapdlInstancesIntegration:
    """Integration tests for list_mapdl_instances function."""

    def test_list_instances_real_call(self):
        """Test list_mapdl_instances with a real call to PyMAPDL CLI.

        This test calls the actual list_instances function from PyMAPDL
        without mocking. It should work regardless of whether MAPDL
        instances are running.
        """
        result = list_mapdl_instances()

        # The result should always be a string
        assert isinstance(result, str)
        assert len(result) > 0

        # Should not contain error messages if PyMAPDL is properly installed
        # (unless there's an actual error, which would still return a string)

    def test_list_instances_with_running_mapdl(self):
        """Test list_mapdl_instances when MAPDL is known to be running.

        This test assumes a MAPDL instance is running on port 50052
        and verifies that list_mapdl_instances can detect it.
        """
        try:
            from ansys.mapdl.core import Mapdl

            # Try to connect to verify MAPDL is running
            mapdl = Mapdl(
                start_instance=False,
                ip="localhost",
                port=50052,
                cleanup_on_exit=False,
                loglevel="ERROR",
            )

        except Exception as e:
            pytest.skip(f"MAPDL not available on port 50052: {e}")

        # If we get here, MAPDL is running
        result = list_mapdl_instances()

        assert isinstance(result, str)
        assert len(result) > 0

        # The output should contain information about instances
        # It might show "50052" port if the instance was started with PyMAPDL
        # or might show an empty table if MAPDL was started externally
        # without PyMAPDL (e.g., Docker container)
        # Check for table headers
        assert "Name" in result and "Is Instance" in result and "Status" in result

    def test_list_instances_output_format(self):
        """Test that list_mapdl_instances returns properly formatted output."""
        result = list_mapdl_instances()

        assert isinstance(result, str)

        # Should have a table header (always present even if empty)
        # Headers from list_instances: Name, Is Instance, Status, gRPC port, PID, Command line, Working directory
        has_table = all(
            header in result for header in ["Name", "Is Instance", "Status", "gRPC port", "PID"]
        )
        has_error = "Error" in result

        assert has_table or has_error, "Output should contain table headers or an error message"

    def test_list_instances_no_crash(self):
        """Test that list_mapdl_instances never crashes or raises exceptions.

        The function should always return a string, even if there are errors.
        """
        try:
            result = list_mapdl_instances()
            assert isinstance(result, str)
            assert result is not None
        except Exception as e:
            pytest.fail(f"list_mapdl_instances should not raise exceptions, but got: {e}")

    def test_list_instances_consistent_calls(self):
        """Test that multiple calls to list_mapdl_instances are consistent."""
        result1 = list_mapdl_instances()
        result2 = list_mapdl_instances()

        # Both should be strings
        assert isinstance(result1, str)
        assert isinstance(result2, str)

        # Results should be similar (may not be identical due to timing)
        # But at least both should be non-empty
        assert len(result1) > 0
        assert len(result2) > 0
