"""Tests for MCP tools functionality."""

from unittest.mock import Mock, patch

import pytest

from ansys.mapdl.mcp import (
    check_mapdl_status,
    list_mapdl_instances,
    run_mapdl_command,
    write_comment,
)


@pytest.mark.unit
class TestCheckMapdlStatus:
    """Tests for check_mapdl_status tool."""

    def test_check_status_with_mapdl(self, mock_context):
        """Test checking MAPDL status when MAPDL is available."""
        result = check_mapdl_status(mock_context)

        assert isinstance(result, str)
        assert "MAPDL is available" in result
        assert "2024 R2" in result

    def test_check_status_without_mapdl(self, mock_context_no_mapdl):
        """Test checking MAPDL status when MAPDL is not available."""
        result = check_mapdl_status(mock_context_no_mapdl)

        # Should return helpful error message instead of raising exception
        assert isinstance(result, str)
        assert "No MAPDL connection available" in result
        assert "connect_to_mapdl" in result


@pytest.mark.unit
class TestWriteComment:
    """Tests for write_comment tool."""

    def test_write_comment_success(self, mock_context):
        """Test writing a comment successfully."""
        comment = "This is a test comment"
        result = write_comment(mock_context, comment)

        assert isinstance(result, str)
        assert "Comment written successfully" in result

        # Verify that MAPDL's com method was called
        mock_context.request_context.lifespan_context.mapdl.com.assert_called_once()
        call_args = mock_context.request_context.lifespan_context.mapdl.com.call_args
        assert comment in call_args[0][0]

    def test_write_comment_empty_string(self, mock_context):
        """Test writing an empty comment."""
        result = write_comment(mock_context, "")

        assert isinstance(result, str)
        assert "Comment written successfully" in result

    def test_write_comment_special_characters(self, mock_context):
        """Test writing a comment with special characters."""
        comment = "Comment with special chars: !@#$%^&*()"
        result = write_comment(mock_context, comment)

        assert isinstance(result, str)
        assert "Comment written successfully" in result

    def test_write_comment_without_mapdl(self, mock_context_no_mapdl):
        """Test writing a comment when MAPDL is not available."""
        result = write_comment(mock_context_no_mapdl, "Test comment")

        # Should return helpful error message instead of raising exception
        assert isinstance(result, str)
        assert "No MAPDL connection available" in result
        assert "connect_to_mapdl" in result


@pytest.mark.unit
class TestRunMapdlCommand:
    """Tests for run_mapdl_command tool."""

    def test_run_command_success(self, mock_context):
        """Test running a MAPDL command successfully."""
        command = "/PREP7"
        result = run_mapdl_command(mock_context, command)

        assert isinstance(result, str)
        assert "MAPDL command executed successfully" in result

        # Verify that MAPDL's run method was called
        mock_context.request_context.lifespan_context.mapdl.run.assert_called_once_with(command)

    def test_run_command_with_arguments(self, mock_context):
        """Test running a MAPDL command with arguments."""
        command = "K,1,0,0,0"
        result = run_mapdl_command(mock_context, command)

        assert isinstance(result, str)
        assert "MAPDL command executed successfully" in result

    def test_run_command_without_mapdl(self, mock_context_no_mapdl):
        """Test running a command when MAPDL is not available."""
        result = run_mapdl_command(mock_context_no_mapdl, "/PREP7")

        # Should return helpful error message instead of raising exception
        assert isinstance(result, str)
        assert "No MAPDL connection available" in result
        assert "connect_to_mapdl" in result

    def test_run_multiple_commands(self, mock_context):
        """Test running multiple MAPDL commands sequentially."""
        commands = ["/PREP7", "ET,1,SOLID185", "MP,EX,1,200E9"]

        for cmd in commands:
            result = run_mapdl_command(mock_context, cmd)
            assert "MAPDL command executed successfully" in result

        # Verify all commands were called
        assert mock_context.request_context.lifespan_context.mapdl.run.call_count == len(commands)


@pytest.mark.unit
class TestListMapdlInstances:
    """Tests for list_mapdl_instances tool."""

    def test_list_instances_success(self):
        """Test list_mapdl_instances with successful instance discovery."""
        # Mock the list_instances function to return sample instances
        mock_output = """Name      Is Instance    Status      gRPC port    PID    Command line                Working directory
------  -------------  --------  -----------  -----  -------------------------  -------------------
ansys     True          running         50052  12345  ansys242 -grpc -port 50052  /tmp/ansys_tmp
ansys     True          running         50053  12346  ansys242 -grpc -port 50053  /tmp/ansys_tmp2"""

        with patch("ansys.mapdl.mcp.helpers.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Verify the function returns the output from list_instances
            assert result == mock_output
            assert "ansys" in result
            assert "50052" in result

    def test_list_instances_no_instances(self):
        """Test list_mapdl_instances when no instances are found."""
        # Mock the list_instances function to return empty table
        mock_output = """Name    Is Instance    Status    gRPC port    PID    Command line    Working directory
------  -------------  --------  -----------  -----  --------------  -------------------"""

        with patch("ansys.mapdl.mcp.helpers.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Verify appropriate message is returned
            assert result == mock_output

    def test_list_instances_calls_with_long_flag(self):
        """Test that list_mapdl_instances calls list_instances with long=True."""
        mock_list_instances = Mock(return_value="Sample output")

        with patch("ansys.mapdl.mcp.helpers.list_instances", mock_list_instances):
            result = list_mapdl_instances()

            # Verify list_instances was called with long=True
            mock_list_instances.assert_called_once_with(long=True)
            assert result == "Sample output"

    def test_list_instances_multiple_instances(self):
        """Test list_mapdl_instances with multiple running instances."""
        # Mock the list_instances function with multiple instances
        mock_output = """Name      Is Instance    Status      gRPC port    PID    Command line                Working directory
------  -------------  --------  -----------  -----  -------------------------  ------------------------------------
ansys     True          running         50052  12345  ansys242 -grpc -port 50052  /tmp/ansys_workdir1
ansys     True          running         50053  12346  ansys242 -grpc -port 50053  /tmp/ansys_workdir2
ansys     True          running         50054  12347  ansys242 -grpc -port 50054  /tmp/ansys_workdir3"""

        with patch("ansys.mapdl.mcp.helpers.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Verify all instances are included in output
            assert "ansys" in result
            assert "50052" in result
            assert "50053" in result
            assert "50054" in result

    def test_list_instances_stderr_logging(self, capsys):
        """Test that list_mapdl_instances logs to stderr."""
        mock_output = "Sample output"

        with patch("ansys.mapdl.mcp.helpers.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Capture stderr output
            captured = capsys.readouterr()

            # Verify logging message is written to stderr
            assert "Searching for MAPDL instances" in captured.err
