"""Tests for MCP tools functionality."""

from unittest.mock import Mock, patch

import pytest

from ansys.mapdl.mcp import check_mapdl_status, list_mapdl_instances, run_mapdl_command, write_comment


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
        with pytest.raises(AttributeError):
            # Should raise AttributeError when trying to access version on None
            check_mapdl_status(mock_context_no_mapdl)


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
        with pytest.raises(AttributeError):
            write_comment(mock_context_no_mapdl, "Test comment")


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
        with pytest.raises(AttributeError):
            run_mapdl_command(mock_context_no_mapdl, "/PREP7")

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
        mock_output = """Name      Status      gRPC Port      IP            PID
--------  --------  -----------  ----------  -----
MAPDL_1   Running         50052  127.0.0.1   12345
MAPDL_2   Running         50053  127.0.0.1   12346"""

        with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Verify the function returns the output from list_instances
            assert result == mock_output
            assert "MAPDL_1" in result
            assert "50052" in result

    def test_list_instances_no_instances(self):
        """Test list_mapdl_instances when no instances are found."""
        # Mock the list_instances function to return empty/no instances message
        mock_output = "No MAPDL instances found."

        with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Verify appropriate message is returned
            assert result == mock_output

    def test_list_instances_exception(self):
        """Test list_mapdl_instances handles exceptions gracefully."""
        # Mock the list_instances function to raise an exception
        with patch(
            "ansys.mapdl.mcp.mpc.list_instances", side_effect=Exception("Connection error")
        ):
            result = list_mapdl_instances()

            # Verify error is caught and returned as string
            assert "Error" in result or "error" in result.lower()
            assert isinstance(result, str)

    def test_list_instances_import_error(self):
        """Test list_mapdl_instances handles import errors gracefully."""
        # Mock the import to fail
        with patch(
            "ansys.mapdl.mcp.mpc.list_instances", side_effect=ImportError("Module not found")
        ):
            result = list_mapdl_instances()

            # Verify error is caught and returned as string
            assert "Error" in result or "error" in result.lower()
            assert isinstance(result, str)

    def test_list_instances_calls_with_long_flag(self):
        """Test that list_mapdl_instances calls list_instances with long=True."""
        mock_list_instances = Mock(return_value="Sample output")

        with patch("ansys.mapdl.mcp.mpc.list_instances", mock_list_instances):
            result = list_mapdl_instances()

            # Verify list_instances was called with long=True
            mock_list_instances.assert_called_once_with(long=True)
            assert result == "Sample output"

    def test_list_instances_multiple_instances(self):
        """Test list_mapdl_instances with multiple running instances."""
        # Mock the list_instances function with multiple instances
        mock_output = """Name          Status      gRPC Port      IP            PID      Working Directory
------------  --------  -----------  ----------  -----  ------------------------------------
MAPDL_50052   Running         50052  127.0.0.1   12345  /tmp/ansys_workdir1
MAPDL_50053   Running         50053  127.0.0.1   12346  /tmp/ansys_workdir2
MAPDL_50054   Running         50054  127.0.0.1   12347  /tmp/ansys_workdir3"""

        with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Verify all instances are included in output
            assert "MAPDL_50052" in result
            assert "MAPDL_50053" in result
            assert "MAPDL_50054" in result
            assert "50052" in result
            assert "50053" in result
            assert "50054" in result

    def test_list_instances_stderr_logging(self, capsys):
        """Test that list_mapdl_instances logs to stderr."""
        mock_output = "Sample output"

        with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=mock_output):
            result = list_mapdl_instances()

            # Capture stderr output
            captured = capsys.readouterr()

            # Verify logging message is written to stderr
            assert "Searching for MAPDL instances" in captured.err

    def test_list_instances_return_type(self):
        """Test that list_mapdl_instances always returns a string."""
        # Test with normal output
        with patch("ansys.mapdl.mcp.mpc.list_instances", return_value="Normal output"):
            result = list_mapdl_instances()
            assert isinstance(result, str)

        # Test with empty string
        with patch("ansys.mapdl.mcp.mpc.list_instances", return_value=""):
            result = list_mapdl_instances()
            assert isinstance(result, str)

        # Test with exception
        with patch("ansys.mapdl.mcp.mpc.list_instances", side_effect=Exception("Error")):
            result = list_mapdl_instances()
            assert isinstance(result, str)
