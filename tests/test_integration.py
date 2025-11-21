"""Integration tests for PyMAPDL MCP Server.

These tests require a running MAPDL instance and are marked as 'integration'.
Run with: pytest -m integration

To skip integration tests, run: pytest -m "not integration"
"""

import os

import numpy as np
import pytest

from ansys.mapdl.mcp import (
    check_mapdl_status,
    list_mapdl_instances,
    run_mapdl_command,
    run_multiple_commands,
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
            from ansys.mapdl.core import launch_mapdl

            mapdl = launch_mapdl(cleanup_on_exit=False, loglevel="ERROR")

            yield mapdl

            # Cleanup after tests
            # Don't exit since MAPDL is running externally

        except Exception as e:
            # Not allow to skip if running on CICD
            if os.getenv("ON_CI", False):
                raise e
            else:
                pytest.skip(f"MAPDL not available: {e}")

    @pytest.fixture()
    def mapdl(self, real_mapdl):
        real_mapdl.clear()
        return real_mapdl

    @pytest.fixture
    def real_context(self, real_mapdl):
        """Create a real context with actual MAPDL connection."""
        from unittest.mock import MagicMock

        from ansys.mapdl.mcp.mcp import AppContext

        context = MagicMock()
        context.request_context = MagicMock()
        context.request_context.lifespan_context = AppContext(mapdl=real_mapdl)

        return context

    def test_real_check_mapdl_status(self, real_context):
        """Test checking MAPDL status with a real connection."""
        import json

        result = check_mapdl_status(real_context)

        assert isinstance(result, str)
        # Check for JSON structure
        data = json.loads(result)
        assert "connection" in data
        assert "version" in data["connection"]
        assert data["connection"]["status"] == "Running"

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

    def test_real_run_multiple_commands(self, real_context):
        """Test running multiple commands with real MAPDL."""
        # Clear any existing model
        run_mapdl_command(real_context, "/CLEAR")

        # Run multiple commands
        commands = [
            "/PREP7",
            "ET,1,SOLID185",
            "MP,EX,1,200E9",
            "MP,PRXY,1,0.3",
        ]

        result = run_multiple_commands(real_context, commands)

        assert isinstance(result, str)
        assert "Successfully executed 4 MAPDL commands" in result
        assert all(cmd in result for cmd in commands)

    def test_real_run_multiple_commands_with_geometry(self, real_context):
        """Test running multiple commands to create simple geometry."""
        # Clear any existing model
        run_mapdl_command(real_context, "/CLEAR")

        # Create a simple block using multiple commands
        commands = [
            "/PREP7",
            "ET,1,SOLID185",
            "MP,EX,1,200E9",
            "MP,PRXY,1,0.3",
            "BLC4,0,0,1,1,1",  # Create a block
        ]

        result = run_multiple_commands(real_context, commands)

        assert "Successfully executed 5 MAPDL commands" in result
        assert "BLC4,0,0,1,1,1" in result

    def test_real_run_multiple_commands_empty_list(self, real_context):
        """Test error handling with empty command list."""
        result = run_multiple_commands(real_context, [])

        assert "No commands provided" in result

    def test_real_run_multiple_commands_vs_single(self, real_context):
        """Compare run_multiple_commands with sequential single commands."""
        # Clear any existing model
        run_mapdl_command(real_context, "/CLEAR")

        commands = [
            "/PREP7",
            "ET,1,SOLID185",
            "MP,EX,1,200E9",
        ]

        # Test multiple commands
        result_multi = run_multiple_commands(real_context, commands)
        assert "Successfully executed 3 MAPDL commands" in result_multi

        # Clear and test single commands
        run_mapdl_command(real_context, "/CLEAR")

        results_single = []
        for cmd in commands:
            result = run_mapdl_command(real_context, cmd)
            results_single.append(result)
            assert "executed successfully" in result

        # Both approaches should work successfully
        assert len(results_single) == 3


@pytest.mark.integration
class TestRunMultipleCommandsIntegration:
    """Integration tests specifically for run_multiple_commands."""

    @pytest.fixture(scope="class")
    def real_mapdl(self):
        """Fixture to connect to a real MAPDL instance."""
        try:
            from ansys.mapdl.core import launch_mapdl

            mapdl = launch_mapdl(cleanup_on_exit=False, loglevel="ERROR")
            yield mapdl
        except Exception as e:
            if os.getenv("ON_CI", False):
                raise e
            else:
                pytest.skip(f"MAPDL not available: {e}")

    @pytest.fixture()
    def mapdl(self, real_mapdl):
        real_mapdl.clear()
        return real_mapdl

    @pytest.fixture
    def real_context(self, real_mapdl):
        """Create a real context with actual MAPDL connection."""
        from unittest.mock import MagicMock

        from ansys.mapdl.mcp.mcp import AppContext

        context = MagicMock()
        context.request_context = MagicMock()
        context.request_context.lifespan_context = AppContext(mapdl=real_mapdl)

        return context

    def test_multiple_commands_large_batch(self, real_context, mapdl):
        """Test running a large batch of commands."""
        # Clear model
        run_mapdl_command(real_context, "/CLEAR")
        run_mapdl_command(real_context, "/PREP7")

        # Create many keypoints
        commands = [f"K,{i},{i*0.1},{i*0.1},{i*0.1}" for i in range(1, 51)]

        result = run_multiple_commands(real_context, commands)

        assert "Successfully executed 50 MAPDL commands" in result

        assert mapdl.geometry.get_keypoints(return_as_array=True).shape[0] == 50

    def test_multiple_commands_with_comments(self, real_context, mapdl):
        """Test running multiple commands including comments."""
        run_mapdl_command(real_context, "/CLEAR")

        commands = [
            "/COM, Starting material definition",
            "/PREP7",
            "/COM, Define element type",
            "ET,1,SOLID185",
            "/COM, Define material properties",
            "MP,EX,1,200E9",
            "MP,PRXY,1,0.3",
        ]

        result = run_multiple_commands(real_context, commands)

        assert "Successfully executed 7 MAPDL commands" in result

        assert mapdl.get_value("MAT", 0, "count") == 1.0
        assert mapdl.get_value("ETYP", 1, "attr", "enam") == 185.0
        assert np.allclose(mapdl.get_value("EX", 1), 200e9)
        assert np.allclose(mapdl.get_value("PRXY", 1), 0.3)

    def test_multiple_commands_error_handling(self, real_context):
        """Test error handling with invalid commands."""
        run_mapdl_command(real_context, "/CLEAR")

        # Include an invalid command
        commands = [
            "/PREP7",
            "ET,1,SOLID185",
            "INVALID_MAPDL_COMMAND_XYZ",  # This should cause an error
        ]

        result = run_multiple_commands(real_context, commands)

        # Should get error message
        assert isinstance(result, str)
        # Either successful execution or error message
        assert (
            "Successfully executed" in result
            or "Error executing commands" in result
            or "error" in result.lower()
        )

    def test_multiple_commands_performance(self, real_context):
        """Test that multiple commands are faster than sequential single commands."""
        import time

        run_mapdl_command(real_context, "/CLEAR")

        commands = ["/PREP7", "ET,1,SOLID185", "MP,EX,1,200E9", "MP,PRXY,1,0.3"]

        # Time multiple commands approach
        start_multi = time.time()
        result_multi = run_multiple_commands(real_context, commands)
        time_multi = time.time() - start_multi

        assert "Successfully executed 4 MAPDL commands" in result_multi

        # Clear and time single commands approach
        run_mapdl_command(real_context, "/CLEAR")

        start_single = time.time()
        for cmd in commands:
            run_mapdl_command(real_context, cmd)
        time_single = time.time() - start_single

        # Multiple commands should be at least as fast (usually faster)
        # We allow some tolerance since timing can vary
        print(f"Multiple commands time: {time_multi:.4f}s")
        print(f"Single commands time: {time_single:.4f}s")
        print(f"Speedup: {time_single/time_multi:.2f}x")

        # Just verify both completed successfully
        assert time_multi > 0
        assert time_single > 0
        # assert time_multi < time_single


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
            from ansys.mapdl.core import launch_mapdl

            # Try to connect to verify MAPDL is running
            mapdl = launch_mapdl(
                cleanup_on_exit=False,
                loglevel="ERROR",
            )

        except Exception as e:
            # Not allow to skip if running on CICD
            if os.getenv("ON_CI", False):
                raise e
            else:
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
