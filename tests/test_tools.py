"""Tests for MCP tools functionality."""

import json
import logging
from unittest.mock import MagicMock, Mock, patch

import pytest
from mcp.types import ImageContent, TextContent

from ansys.mapdl.mcp.tools import (
    check_mapdl_installed,
    check_mapdl_status,
    connect_to_mapdl,
    disconnect_from_mapdl,
    launch_mapdl,
    list_mapdl_instances,
    run_mapdl_command,
    run_multiple_commands,
    screenshot,
    write_comment,
)


@pytest.mark.unit
class TestCheckMapdlStatus:
    """Tests for check_mapdl_status tool."""

    def test_check_status_with_mapdl(self, mock_context):
        """Test checking MAPDL status when MAPDL is available."""
        result = check_mapdl_status.fn(mock_context)

        assert isinstance(result, str)
        # Check for JSON structure
        import json

        data = json.loads(result)
        assert "connection" in data
        assert "information" in data
        assert "geometry" in data
        assert "post_processing" in data
        assert "mesh" in data
        assert "version" in data["connection"]

    def test_check_status_without_mapdl(self, mock_context_no_mapdl):
        """Test checking MAPDL status when MAPDL is not available."""
        result = check_mapdl_status.fn(mock_context_no_mapdl)

        # Should return helpful error message instead of raising exception
        assert isinstance(result, str)
        assert "No MAPDL connection available" in result
        assert "connect_to_mapdl" in result

    def test_check_status_with_exited_mapdl(self, mock_context):
        """Test checking status when MAPDL has exited."""
        mock_context.request_context.lifespan_context.mapdl._exited = True

        result = check_mapdl_status.fn(mock_context)

        assert isinstance(result, str)
        assert "MAPDL instance has exited" in result
        assert "reconnect or launch" in result

    def test_check_status_with_exiting_mapdl(self, mock_context):
        """Test checking status when MAPDL is exiting."""
        mock_context.request_context.lifespan_context.mapdl._exiting = True

        result = check_mapdl_status.fn(mock_context)

        assert isinstance(result, str)
        assert "MAPDL instance is currently exiting" in result

    def test_check_status_missing_information_attributes(self, mock_context):
        """Test status extraction when information class attributes are missing."""
        import json

        # Remove some information attributes
        delattr(mock_context.request_context.lifespan_context.mapdl.information, "title")
        delattr(mock_context.request_context.lifespan_context.mapdl.information, "product")

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON with default values
        data = json.loads(result)
        assert "information" in data
        assert data["information"]["title"] == ""
        assert data["information"]["product"] == ""

    def test_check_status_missing_geometry_attributes(self, mock_context):
        """Test status extraction when geometry class attributes are missing."""
        import json

        # Remove geometry attributes
        delattr(mock_context.request_context.lifespan_context.mapdl.geometry, "n_keypoint")
        delattr(mock_context.request_context.lifespan_context.mapdl.geometry, "n_line")

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON with default values
        data = json.loads(result)
        assert "geometry" in data
        assert data["geometry"]["n_keypoint"] == 0
        assert data["geometry"]["n_line"] == 0

    def test_check_status_missing_mesh_attributes(self, mock_context):
        """Test status extraction when mesh class attributes are missing."""
        import json

        # Remove mesh attributes
        delattr(mock_context.request_context.lifespan_context.mapdl.mesh, "n_node")

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON with default values
        data = json.loads(result)
        assert "mesh" in data
        assert data["mesh"]["n_node"] == 0

    def test_check_status_missing_post_processing(self, mock_context):
        """Test status extraction when post_processing is not available."""
        import json

        # Remove post_processing attribute
        delattr(mock_context.request_context.lifespan_context.mapdl, "post_processing")

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON
        data = json.loads(result)
        assert "post_processing" in data
        assert data["post_processing"]["available"] == False

    def test_check_status_information_class_exception(self, mock_context):
        """Test status extraction when information class raises exception."""
        import json

        # Make information.title raise an exception
        type(mock_context.request_context.lifespan_context.mapdl.information).title = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Information error"))
        )

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON with error field
        data = json.loads(result)
        assert "information" in data
        assert "error" in data["information"]

    def test_check_status_geometry_class_exception(self, mock_context):
        """Test status extraction when geometry class raises exception."""
        import json

        # Make geometry raise an exception
        type(mock_context.request_context.lifespan_context.mapdl.geometry).n_keypoint = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Geometry error"))
        )

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON with error field
        data = json.loads(result)
        assert "geometry" in data
        assert "error" in data["geometry"]

    def test_check_status_mesh_class_exception(self, mock_context):
        """Test status extraction when mesh class raises exception."""
        import json

        # Make mesh raise an exception
        type(mock_context.request_context.lifespan_context.mapdl.mesh).n_node = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Mesh error"))
        )

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON with error field
        data = json.loads(result)
        assert "mesh" in data
        assert "error" in data["mesh"]

    def test_check_status_post_processing_exception(self, mock_context):
        """Test status extraction when post_processing raises exception."""
        import json

        # Make post_processing.nsets raise an exception
        type(mock_context.request_context.lifespan_context.mapdl.post_processing).nsets = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Post error"))
        )

        result = check_mapdl_status.fn(mock_context)

        # Should still return valid JSON with error field
        data = json.loads(result)
        assert "post_processing" in data
        assert "error" in data["post_processing"]

    def test_check_status_all_data_present(self, mock_context):
        """Test status extraction when all data is properly available."""
        import json

        result = check_mapdl_status.fn(mock_context)

        data = json.loads(result)

        # Verify all sections are present
        assert "connection" in data
        assert "information" in data
        assert "geometry" in data
        assert "post_processing" in data
        assert "mesh" in data

        # Verify connection data
        assert data["connection"]["version"] == "2024 R2"
        assert "directory" in data["connection"]
        assert "port" in data["connection"]
        assert "ip" in data["connection"]

        # Verify information data
        assert "title" in data["information"]
        assert "jobname" in data["information"]
        assert "routine" in data["information"]

        # Verify geometry data
        assert "n_keypoint" in data["geometry"]
        assert "n_line" in data["geometry"]
        assert "n_area" in data["geometry"]
        assert "n_volu" in data["geometry"]

        # Verify mesh data
        assert "n_node" in data["mesh"]
        assert "n_elem" in data["mesh"]

        # Verify post_processing data
        assert "available" in data["post_processing"]


@pytest.mark.unit
class TestCheckMapdlInstalled:
    """Tests for check_mapdl_installed tool."""

    def test_check_installed_true(self):
        """Test checking MAPDL installation when MAPDL is installed."""
        with patch("ansys.mapdl.core.launcher.check_valid_ansys", return_value=True), patch(
            "ansys.mapdl.core.launcher.get_default_ansys_path",
            return_value="/usr/ansys_inc/v242/ansys/bin/ansys242",
        ):
            result = check_mapdl_installed.fn(MagicMock())

            assert isinstance(result, str)
            assert "MAPDL is installed" in result
            assert "/usr/ansys_inc/v242/ansys/bin/ansys242" in result

    def test_check_installed_false(self):
        """Test checking MAPDL installation when MAPDL is not installed."""
        with patch("ansys.mapdl.core.launcher.check_valid_ansys", return_value=False):
            result = check_mapdl_installed.fn(MagicMock())

            assert isinstance(result, str)
            assert "MAPDL is not installed" in result
            assert "cannot be found" in result
            assert "properly installed" in result

    def test_check_installed_exception(self):
        """Test error handling when checking MAPDL installation fails."""
        with patch(
            "ansys.mapdl.core.launcher.check_valid_ansys",
            side_effect=Exception("System error"),
        ):
            result = check_mapdl_installed.fn(MagicMock())

            assert isinstance(result, str)
            assert "Error checking MAPDL installation" in result
            assert "System error" in result

    def test_check_installed_no_ansys_env(self):
        """Test checking installation when ANSYS environment variables not set."""
        with patch(
            "ansys.mapdl.core.launcher.check_valid_ansys",
            side_effect=EnvironmentError("ANSYS environment not configured"),
        ):
            result = check_mapdl_installed.fn(MagicMock())

            assert isinstance(result, str)
            assert "Error checking MAPDL installation" in result
            assert "ANSYS environment not configured" in result

    def test_check_installed_import_error(self):
        """Test handling import errors gracefully."""
        with patch(
            "ansys.mapdl.core.launcher.check_valid_ansys",
            side_effect=ImportError("Failed to import MAPDL module"),
        ):
            result = check_mapdl_installed.fn(MagicMock())

            assert isinstance(result, str)
            assert "Error checking MAPDL installation" in result
            assert "Failed to import MAPDL module" in result

    def test_check_installed_with_custom_path(self):
        """Test checking installation with custom ANSYS path."""
        custom_path = "/opt/ansys/v251/ansys/bin/ansys251"
        with patch("ansys.mapdl.core.launcher.check_valid_ansys", return_value=True), patch(
            "ansys.mapdl.core.launcher.get_default_ansys_path", return_value=custom_path
        ):
            result = check_mapdl_installed.fn(MagicMock())

            assert "MAPDL is installed" in result
            assert custom_path in result

    def test_check_installed_logging(self):
        """Test that check_mapdl_installed logs messages."""
        with patch("ansys.mapdl.core.launcher.check_valid_ansys", return_value=True), patch(
            "ansys.mapdl.core.launcher.get_default_ansys_path",
            return_value="/usr/ansys_inc/v242/ansys/bin/ansys242",
        ):
            output = check_mapdl_installed.fn(MagicMock())

            # Verify logging messages
            assert (
                "MAPDL is installed on this system in: /usr/ansys_inc/v242/ansys/bin/ansys242"
                in output
            )

    def test_check_not_installed_logging(self):
        """Test that check_mapdl_installed logs when not installed."""
        with patch("ansys.mapdl.core.launcher.check_valid_ansys", return_value=False):
            output = check_mapdl_installed.fn(MagicMock())

            assert "MAPDL is not installed on this system or cannot be found in the " in output
            assert "standard locations. Please ensure ANSYS/MAPDL is properly installed " in output
            assert "and the installation path is correct." in output


@pytest.mark.unit
class TestWriteComment:
    """Tests for write_comment tool."""

    def test_write_comment_success(self, mock_context):
        """Test writing a comment successfully."""
        comment = "This is a test comment"
        result = write_comment.fn(mock_context, comment)

        assert isinstance(result, str)
        assert "Comment written successfully" in result

        # Verify that MAPDL's com method was called
        mock_context.request_context.lifespan_context.mapdl.com.assert_called_once()
        call_args = mock_context.request_context.lifespan_context.mapdl.com.call_args
        assert comment in call_args[0][0]

    def test_write_comment_empty_string(self, mock_context):
        """Test writing an empty comment."""
        result = write_comment.fn(mock_context, "")

        assert isinstance(result, str)
        assert "Comment written successfully" in result

    def test_write_comment_special_characters(self, mock_context):
        """Test writing a comment with special characters."""
        comment = "Comment with special chars: !@#$%^&*()"
        result = write_comment.fn(mock_context, comment)

        assert isinstance(result, str)
        assert "Comment written successfully" in result

    def test_write_comment_without_mapdl(self, mock_context_no_mapdl):
        """Test writing a comment when MAPDL is not available."""
        result = write_comment.fn(mock_context_no_mapdl, "Test comment")

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
        result = run_mapdl_command.fn(mock_context, command)

        assert isinstance(result, str)
        assert "MAPDL command executed successfully" in result

        # Verify that MAPDL's run method was called
        mock_context.request_context.lifespan_context.mapdl.run.assert_called_once_with(command)

    def test_run_command_with_arguments(self, mock_context):
        """Test running a MAPDL command with arguments."""
        command = "K,1,0,0,0"
        result = run_mapdl_command.fn(mock_context, command)

        assert isinstance(result, str)
        assert "MAPDL command executed successfully" in result

    def test_run_command_without_mapdl(self, mock_context_no_mapdl):
        """Test running a command when MAPDL is not available."""
        result = run_mapdl_command.fn(mock_context_no_mapdl, "/PREP7")

        # Should return helpful error message instead of raising exception
        assert isinstance(result, str)
        assert "No MAPDL connection available" in result
        assert "connect_to_mapdl" in result

    def test_run_multiple_commands(self, mock_context):
        """Test running multiple MAPDL commands sequentially."""
        commands = ["/PREP7", "ET,1,SOLID185", "MP,EX,1,200E9"]

        for cmd in commands:
            result = run_mapdl_command.fn(mock_context, cmd)
            assert "MAPDL command executed successfully" in result

        # Verify all commands were called
        assert mock_context.request_context.lifespan_context.mapdl.run.call_count == len(commands)


@pytest.mark.unit
class TestRunMultipleCommands:
    """Tests for run_multiple_commands tool."""

    def test_run_multiple_commands_success(self, mock_context):
        """Test running multiple MAPDL commands successfully."""
        commands = ["/PREP7", "ET,1,SOLID185", "MP,EX,1,200E9"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = (
            "Commands executed"
        )

        result = run_multiple_commands.fn(mock_context, commands)

        assert isinstance(result, str)
        assert "Successfully executed 3 MAPDL commands" in result
        assert "/PREP7" in result
        assert "ET,1,SOLID185" in result
        assert "MP,EX,1,200E9" in result

        # Verify that MAPDL's input_strings method was called
        mock_context.request_context.lifespan_context.mapdl.input_strings.assert_called_once_with(
            commands
        )

    def test_run_multiple_commands_with_output(self, mock_context):
        """Test running multiple commands with MAPDL output."""
        commands = ["/PREP7", "ET,1,SOLID185"]
        output = "Element type 1 defined"
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = output

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 2 MAPDL commands" in result
        assert "Output:" in result
        assert output in result

    def test_run_multiple_commands_empty_list(self, mock_context):
        """Test running multiple commands with an empty list."""
        result = run_multiple_commands.fn(mock_context, [])

        assert "No commands provided" in result

    def test_run_multiple_commands_not_list(self, mock_context):
        """Test running multiple commands with non-list input."""
        result = run_multiple_commands.fn(mock_context, "not a list")

        assert "Commands must be provided as a list" in result

    def test_run_multiple_commands_with_empty_strings(self, mock_context):
        """Test running multiple commands with some empty strings."""
        commands = ["/PREP7", "", "ET,1,SOLID185", "  ", "MP,EX,1,200E9"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        result = run_multiple_commands.fn(mock_context, commands)

        # Should only execute non-empty commands
        assert "Successfully executed 3 MAPDL commands" in result
        assert "/PREP7" in result
        assert "ET,1,SOLID185" in result
        assert "MP,EX,1,200E9" in result

        # Verify input_strings was called with filtered commands
        call_args = mock_context.request_context.lifespan_context.mapdl.input_strings.call_args[0][
            0
        ]
        assert len(call_args) == 3
        assert "" not in call_args
        assert "  " not in call_args

    def test_run_multiple_commands_all_empty(self, mock_context):
        """Test running multiple commands when all are empty."""
        commands = ["", "  ", "\t", "\n"]

        result = run_multiple_commands.fn(mock_context, commands)

        assert "No valid commands found" in result

    def test_run_multiple_commands_without_mapdl(self, mock_context_no_mapdl):
        """Test running multiple commands when MAPDL is not available."""
        commands = ["/PREP7", "ET,1,SOLID185"]
        result = run_multiple_commands.fn(mock_context_no_mapdl, commands)

        # Should return helpful error message instead of raising exception
        assert isinstance(result, str)
        assert "No MAPDL connection available" in result
        assert "connect_to_mapdl" in result

    def test_run_multiple_commands_single_command(self, mock_context):
        """Test running a single command through multiple commands."""
        commands = ["/PREP7"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 1 MAPDL commands" in result
        assert "/PREP7" in result

    def test_run_multiple_commands_with_whitespace(self, mock_context):
        """Test running commands with leading/trailing whitespace."""
        commands = ["  /PREP7  ", "\tET,1,SOLID185\n", " MP,EX,1,200E9 "]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 3 MAPDL commands" in result

        # Verify whitespace was stripped
        call_args = mock_context.request_context.lifespan_context.mapdl.input_strings.call_args[0][
            0
        ]
        assert call_args[0] == "/PREP7"
        assert call_args[1] == "ET,1,SOLID185"
        assert call_args[2] == "MP,EX,1,200E9"

    def test_run_multiple_commands_error_handling(self, mock_context):
        """Test error handling when command execution fails."""
        commands = ["/PREP7", "INVALID_COMMAND", "ET,1,SOLID185"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.side_effect = Exception(
            "Invalid command syntax"
        )

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Error executing commands" in result
        assert "Invalid command syntax" in result
        assert "Commands that were attempted:" in result
        assert "/PREP7" in result
        assert "INVALID_COMMAND" in result
        assert "ET,1,SOLID185" in result

    def test_run_multiple_commands_large_batch(self, mock_context):
        """Test running a large batch of commands."""
        # Create 100 commands
        commands = [f"K,{i},0,0,0" for i in range(1, 101)]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 100 MAPDL commands" in result
        # Verify input_strings was called with all commands
        call_args = mock_context.request_context.lifespan_context.mapdl.input_strings.call_args[0][
            0
        ]
        assert len(call_args) == 100

    def test_run_multiple_commands_with_comments(self, mock_context):
        """Test running multiple commands including comments."""
        commands = [
            "/COM, Starting analysis",
            "/PREP7",
            "/COM, Define element",
            "ET,1,SOLID185",
        ]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 4 MAPDL commands" in result
        assert all(cmd in result for cmd in commands)

    def test_run_multiple_commands_special_characters(self, mock_context):
        """Test running commands with special characters."""
        commands = [
            "/PREP7",
            "MP,EX,1,2.0E11",
            "MP,PRXY,1,0.3",
            "R,1,0.01,0.01,0.01",
        ]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 4 MAPDL commands" in result
        assert all(cmd in result for cmd in commands)

    def test_run_multiple_commands_sequential_execution(self, mock_context):
        """Test that commands are executed in the correct sequence."""
        commands = ["CMD1", "CMD2", "CMD3"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        run_multiple_commands.fn(mock_context, commands)

        # Verify input_strings was called with commands in correct order
        call_args = mock_context.request_context.lifespan_context.mapdl.input_strings.call_args[0][
            0
        ]
        assert call_args == commands

    def test_run_multiple_commands_no_output(self, mock_context):
        """Test running commands that produce no output."""
        commands = ["/PREP7", "ET,1,SOLID185"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 2 MAPDL commands" in result
        # Should not have "Output:" section when result is empty
        assert result.count("Output:") == 0

    def test_run_multiple_commands_none_output(self, mock_context):
        """Test running commands that return None."""
        commands = ["/PREP7", "ET,1,SOLID185"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = None

        result = run_multiple_commands.fn(mock_context, commands)

        assert "Successfully executed 2 MAPDL commands" in result
        # Should not have "Output:" section when result is None
        assert "Output:" not in result

    def test_run_multiple_commands_stderr_logging(self, mock_context):
        """Test that run_multiple_commands logs messages."""
        commands = ["/PREP7", "ET,1,SOLID185"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.return_value = ""

        output = run_multiple_commands.fn(mock_context, commands)

        # Verify logging messages
        assert "Successfully executed 2 MAPDL commands" in output

    def test_run_multiple_commands_error_handling(self, mock_context):
        """Test that command errors are properly handled and reported in return value."""
        commands = ["/PREP7", "INVALID"]
        mock_context.request_context.lifespan_context.mapdl.input_strings.side_effect = Exception(
            "Test error"
        )

        result = run_multiple_commands.fn(mock_context, commands)

        # Verify error message is in the return value
        assert isinstance(result, str)
        assert "Error executing commands" in result
        assert "Test error" in result


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
            result = list_mapdl_instances.fn()

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
            result = list_mapdl_instances.fn()

            # Verify appropriate message is returned
            assert result == mock_output

    def test_list_instances_calls_with_long_flag(self):
        """Test that list_mapdl_instances calls list_instances with long=True."""
        mock_list_instances = Mock(return_value="Sample output")

        with patch("ansys.mapdl.mcp.helpers.list_instances", mock_list_instances):
            result = list_mapdl_instances.fn()

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
            result = list_mapdl_instances.fn()

            # Verify all instances are included in output
            assert "ansys" in result
            assert "50052" in result

    def test_list_instances_return_value_propagation(self):
        """Test that list_mapdl_instances correctly propagates the return value from helpers.list_instances."""
        mock_output = "Sample output with instance information"
        with patch("ansys.mapdl.mcp.helpers.list_instances", return_value=mock_output) as mock_list:
            result = list_mapdl_instances.fn()

            # Verify the helper function was called with correct parameters
            mock_list.assert_called_once_with(long=True)

            # Verify the result is correctly propagated
            assert result == mock_output


@pytest.mark.unit
class TestConnectToMapdl:
    """Tests for connect_to_mapdl tool."""

    def test_connect_default_parameters(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with default parameters."""
        # Create a mock MAPDL instance
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052

        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
            result = connect_to_mapdl.fn(mock_context_no_mapdl)

            # Verify successful connection
            assert isinstance(result, str)
            assert "Successfully connected to MAPDL" in result
            assert "localhost:50052" in result
            assert "2024 R2" in result

            # Verify MAPDL was stored in context
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl == mock_mapdl

    def test_connect_custom_port(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with custom port."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R1"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50053

        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl) as mock_mapdl_class:
            result = connect_to_mapdl.fn(mock_context_no_mapdl, port=50053)

            # Verify connection with custom port
            assert "Successfully connected to MAPDL" in result
            assert "localhost:50053" in result

            # Verify Mapdl was called with correct parameters
            mock_mapdl_class.assert_called_once_with(
                start_instance=False,
                ip="localhost",
                port=50053,
                cleanup_on_exit=False,
                loglevel="INFO",
            )

    def test_connect_custom_ip(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with custom IP address."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "192.168.1.100"
        mock_mapdl._port = 50052

        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl) as mock_mapdl_class:
            result = connect_to_mapdl.fn(mock_context_no_mapdl, ip="192.168.1.100")

            # Verify connection with custom IP
            assert "Successfully connected to MAPDL" in result
            assert "192.168.1.100:50052" in result

            # Verify Mapdl was called with correct parameters
            mock_mapdl_class.assert_called_once_with(
                start_instance=False,
                ip="192.168.1.100",
                port=50052,
                cleanup_on_exit=False,
                loglevel="INFO",
            )

    def test_connect_custom_ip_and_port(self, mock_context_no_mapdl):
        """Test connecting to MAPDL with both custom IP and port."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "10.0.0.50"
        mock_mapdl._port = 50099

        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl) as mock_mapdl_class:
            result = connect_to_mapdl.fn(mock_context_no_mapdl, port=50099, ip="10.0.0.50")

            # Verify connection with custom parameters
            assert "Successfully connected to MAPDL" in result
            assert "10.0.0.50:50099" in result

            # Verify Mapdl was called with correct parameters
            mock_mapdl_class.assert_called_once_with(
                start_instance=False,
                ip="10.0.0.50",
                port=50099,
                cleanup_on_exit=False,
                loglevel="INFO",
            )

    def test_connect_already_connected(self, mock_context):
        """Test connecting when already connected."""
        # Context already has a MAPDL connection
        result = connect_to_mapdl.fn(mock_context)

        # Verify appropriate error message
        assert "Already connected to MAPDL" in result
        assert "disconnect first" in result

    def test_connect_connection_error(self, mock_context_no_mapdl):
        """Test handling connection errors."""
        with patch("ansys.mapdl.core.Mapdl", side_effect=Exception("Connection refused")):
            result = connect_to_mapdl.fn(mock_context_no_mapdl, port=50052, ip="localhost")

            # Verify error message is returned
            assert "Failed to connect to MAPDL" in result
            assert "Connection refused" in result

            # Verify context remains empty
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is None

    def test_connect_network_error(self, mock_context_no_mapdl):
        """Test handling network errors during connection."""
        with patch("ansys.mapdl.core.Mapdl", side_effect=ConnectionError("Network unreachable")):
            result = connect_to_mapdl.fn(mock_context_no_mapdl, port=50052, ip="192.168.1.999")

            # Verify error message
            assert "Failed to connect to MAPDL" in result
            assert "Network unreachable" in result

    def test_connect_timeout_error(self, mock_context_no_mapdl):
        """Test handling timeout errors during connection."""
        with patch("ansys.mapdl.core.Mapdl", side_effect=TimeoutError("Connection timed out")):
            result = connect_to_mapdl.fn(mock_context_no_mapdl)

            # Verify timeout error is handled
            assert "Failed to connect to MAPDL" in result
            assert "Connection timed out" in result

    def test_connect_stores_mapdl_in_context(self, mock_context_no_mapdl):
        """Test that connected MAPDL instance is properly stored in context."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052

        # Verify context starts with no MAPDL
        assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is None

        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
            result = connect_to_mapdl.fn(mock_context_no_mapdl)

            # Verify successful connection
            assert "Successfully connected" in result

            # Verify MAPDL is stored in context
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is not None
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl == mock_mapdl

    def test_connect_result_message(self, mock_context_no_mapdl):
        """Test that connect_to_mapdl returns informative success message."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052

        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
            result = connect_to_mapdl.fn(mock_context_no_mapdl)

            # Verify the result contains connection information
            assert isinstance(result, str)
            assert "Successfully connected to MAPDL at localhost:50052" in result
            assert "2024 R2" in result


@pytest.mark.unit
class TestDisconnectFromMapdl:
    """Tests for disconnect_from_mapdl tool."""

    def test_disconnect_success(self, mock_context):
        """Test disconnecting from MAPDL successfully."""
        # Set up IP and port attributes on mock MAPDL
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052

        # Store reference to check exit was called
        mapdl_ref = mock_context.request_context.lifespan_context.mapdl

        result = disconnect_from_mapdl.fn(mock_context)

        # Verify successful disconnection
        assert isinstance(result, str)
        assert "Successfully disconnected from MAPDL" in result
        assert "localhost:50052" in result

        # Verify exit was called on the original object
        mapdl_ref.exit.assert_called_once()

        # Verify MAPDL was removed from context
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_no_connection(self, mock_context_no_mapdl):
        """Test disconnecting when no connection exists."""
        result = disconnect_from_mapdl.fn(mock_context_no_mapdl)

        # Verify appropriate message
        assert "No MAPDL connection to disconnect" in result

    def test_disconnect_clears_context(self, mock_context):
        """Test that disconnect properly clears the context."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052

        # Verify MAPDL exists before disconnect
        assert mock_context.request_context.lifespan_context.mapdl is not None

        disconnect_from_mapdl.fn(mock_context)

        # Verify MAPDL is cleared after disconnect
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_error_during_exit(self, mock_context):
        """Test handling errors during disconnection."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052
        mock_context.request_context.lifespan_context.mapdl.exit.side_effect = Exception(
            "Disconnection error"
        )

        result = disconnect_from_mapdl.fn(mock_context)

        # Verify error message is returned
        assert "Error during disconnect" in result
        assert "Disconnection error" in result

        # Verify context is still cleared even on error
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_connection_lost(self, mock_context):
        """Test disconnecting when connection is already lost."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052
        mock_context.request_context.lifespan_context.mapdl.exit.side_effect = ConnectionError(
            "Connection already closed"
        )

        result = disconnect_from_mapdl.fn(mock_context)

        # Verify error is handled gracefully
        assert "Error during disconnect" in result
        assert "Connection already closed" in result

        # Context should still be cleared
        assert mock_context.request_context.lifespan_context.mapdl is None

    def test_disconnect_return_message(self, mock_context):
        """Test that disconnect_from_mapdl returns informative message."""
        mock_context.request_context.lifespan_context.mapdl._ip = "localhost"
        mock_context.request_context.lifespan_context.mapdl._port = 50052

        result = disconnect_from_mapdl.fn(mock_context)

        # Verify the result contains disconnection information
        assert isinstance(result, str)
        assert "Successfully disconnected from MAPDL at localhost:50052" in result

    def test_disconnect_custom_ip_port(self, mock_context):
        """Test disconnecting from MAPDL with custom IP and port."""
        mock_context.request_context.lifespan_context.mapdl._ip = "192.168.1.100"
        mock_context.request_context.lifespan_context.mapdl._port = 50053

        result = disconnect_from_mapdl.fn(mock_context)

        # Verify disconnection message includes custom IP and port
        assert "Successfully disconnected from MAPDL at 192.168.1.100:50053" in result


@pytest.mark.unit
class TestLaunchMapdl:
    """Tests for launch_mapdl tool."""

    def test_launch_default_parameters(self, mock_context_no_mapdl):
        """Test launching MAPDL with default parameters."""
        # Create a mock MAPDL instance
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50052
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.directory = "/tmp/ansys_mapdl_1234"

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl) as mock_launch:
            result = launch_mapdl.fn(mock_context_no_mapdl)

            # Verify successful launch
            assert isinstance(result, str)
            assert "Successfully launched MAPDL" in result
            assert "127.0.0.1:50052" in result
            assert "2024 R2" in result
            assert "/tmp/ansys_mapdl_1234" in result

            # Verify launch_mapdl was called with correct parameters
            mock_launch.assert_called_once_with(nproc=2, loglevel="INFO")

            # Verify MAPDL was stored in context
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl == mock_mapdl

    def test_launch_custom_nproc(self, mock_context_no_mapdl):
        """Test launching MAPDL with custom number of processors."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50052
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.directory = "/tmp/ansys_mapdl_1234"

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl) as mock_launch:
            result = launch_mapdl.fn(mock_context_no_mapdl, nproc=4)

            # Verify successful launch
            assert "Successfully launched MAPDL" in result

            # Verify launch_mapdl was called with correct nproc
            mock_launch.assert_called_once_with(nproc=4, loglevel="INFO")

    def test_launch_custom_exec_file(self, mock_context_no_mapdl):
        """Test launching MAPDL with custom executable path."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50052
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.directory = "/tmp/ansys_mapdl_1234"

        exec_path = "/usr/ansys_inc/v242/ansys/bin/ansys242"

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl) as mock_launch:
            result = launch_mapdl.fn(mock_context_no_mapdl, exec_file=exec_path)

            # Verify successful launch
            assert "Successfully launched MAPDL" in result

            # Verify launch_mapdl was called with exec_file
            mock_launch.assert_called_once_with(nproc=2, loglevel="INFO", exec_file=exec_path)

    def test_launch_custom_run_location(self, mock_context_no_mapdl):
        """Test launching MAPDL with custom working directory."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50052
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.directory = "/custom/working/dir"

        run_loc = "/custom/working/dir"

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl) as mock_launch:
            result = launch_mapdl.fn(mock_context_no_mapdl, run_location=run_loc)

            # Verify successful launch
            assert "Successfully launched MAPDL" in result
            assert "/custom/working/dir" in result

            # Verify launch_mapdl was called with run_location
            mock_launch.assert_called_once_with(nproc=2, loglevel="INFO", run_location=run_loc)

    def test_launch_with_additional_switches(self, mock_context_no_mapdl):
        """Test launching MAPDL with additional command line switches."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50052
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.directory = "/tmp/ansys_mapdl_1234"

        switches = "-smp"

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl) as mock_launch:
            result = launch_mapdl.fn(mock_context_no_mapdl, additional_switches=switches)

            # Verify successful launch
            assert "Successfully launched MAPDL" in result

            # Verify launch_mapdl was called with additional_switches
            mock_launch.assert_called_once_with(
                nproc=2, loglevel="INFO", additional_switches=switches
            )

    def test_launch_all_custom_parameters(self, mock_context_no_mapdl):
        """Test launching MAPDL with all custom parameters."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R1"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50053
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50053
        mock_mapdl.directory = "/custom/work/dir"

        exec_path = "/usr/ansys_inc/v241/ansys/bin/ansys241"
        run_loc = "/custom/work/dir"
        switches = "-smp -db 1024"

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl) as mock_launch:
            result = launch_mapdl.fn(
                mock_context_no_mapdl,
                exec_file=exec_path,
                run_location=run_loc,
                nproc=8,
                additional_switches=switches,
            )

            # Verify successful launch
            assert "Successfully launched MAPDL" in result
            assert "127.0.0.1:50053" in result
            assert "2024 R1" in result

            # Verify launch_mapdl was called with all parameters
            mock_launch.assert_called_once_with(
                nproc=8,
                loglevel="INFO",
                exec_file=exec_path,
                run_location=run_loc,
                additional_switches=switches,
            )

    def test_launch_already_connected(self, mock_context):
        """Test launching when already connected to MAPDL."""
        # Context already has a MAPDL connection
        result = launch_mapdl.fn(mock_context)

        # Verify appropriate error message
        assert "Already connected to MAPDL" in result
        assert "disconnect first" in result

    def test_launch_error(self, mock_context_no_mapdl):
        """Test handling launch errors."""
        with patch(
            "ansys.mapdl.core.launch_mapdl",
            side_effect=Exception("MAPDL executable not found"),
        ):
            result = launch_mapdl.fn(mock_context_no_mapdl)

            # Verify error message is returned
            assert "Failed to launch MAPDL" in result
            assert "MAPDL executable not found" in result

            # Verify context remains empty
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is None

    def test_launch_license_error(self, mock_context_no_mapdl):
        """Test handling license errors during launch."""
        with patch(
            "ansys.mapdl.core.launch_mapdl",
            side_effect=Exception("No ANSYS license available"),
        ):
            result = launch_mapdl.fn(mock_context_no_mapdl)

            # Verify error message
            assert "Failed to launch MAPDL" in result
            assert "No ANSYS license available" in result

    def test_launch_stores_mapdl_in_context(self, mock_context_no_mapdl):
        """Test that launched MAPDL instance is properly stored in context."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50052
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.directory = "/tmp/ansys_mapdl_1234"

        # Verify context starts with no MAPDL
        assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is None

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl):
            result = launch_mapdl.fn(mock_context_no_mapdl)

            # Verify successful launch
            assert "Successfully launched MAPDL" in result

            # Verify MAPDL is stored in context
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl is not None
            assert mock_context_no_mapdl.request_context.lifespan_context.mapdl == mock_mapdl

    def test_launch_result_message(self, mock_context_no_mapdl):
        """Test that launch_mapdl returns informative success message."""
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "127.0.0.1"
        mock_mapdl._port = 50052
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.directory = "/tmp/ansys_mapdl_1234"

        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl):
            result = launch_mapdl.fn(mock_context_no_mapdl)

            # Verify the result contains launch information
            assert isinstance(result, str)
            assert "Successfully launched MAPDL at 127.0.0.1:50052" in result
            assert "2024 R2" in result
            assert "/tmp/ansys_mapdl_1234" in result


@pytest.mark.unit
class TestConnectionLifecycle:
    """Tests for the full connection lifecycle."""

    def test_connect_use_disconnect_workflow(self, mock_context_no_mapdl):
        """Test complete workflow: connect, use, disconnect."""
        # Create mock MAPDL
        mock_mapdl = MagicMock()
        mock_mapdl.name = "MAPDL"
        mock_mapdl.status = "Running"
        mock_mapdl.version = 24.2
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052
        mock_mapdl.is_alive = True
        mock_mapdl.is_local = True
        mock_mapdl.port = 50052
        mock_mapdl.ip = "localhost"
        mock_mapdl.directory = "/tmp/test"
        mock_mapdl.platform = "linux"
        mock_mapdl.jobname = "file"
        mock_mapdl.check_status = "running"
        mock_mapdl._exited = False
        mock_mapdl._exiting = False

        mock_mapdl.com = MagicMock(return_value="Comment written")
        mock_mapdl.run = MagicMock(return_value="Command executed")
        # Add required class mocks
        mock_mapdl.information = MagicMock()
        mock_mapdl.information.title = ""
        mock_mapdl.information.jobname = ""
        mock_mapdl.information.routine = ""
        mock_mapdl.information.units = ""
        mock_mapdl.information.revision = ""
        mock_mapdl.information.product = ""
        mock_mapdl.geometry = MagicMock()
        mock_mapdl.geometry.n_keypoint = 0
        mock_mapdl.geometry.n_line = 0
        mock_mapdl.geometry.n_area = 0
        mock_mapdl.geometry.n_volu = 0
        mock_mapdl.post_processing = MagicMock()
        mock_mapdl.post_processing.nsets = 0
        mock_mapdl.mesh = MagicMock()
        mock_mapdl.mesh.n_node = 0
        mock_mapdl.mesh.n_elem = 0

        # Step 1: Connect
        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
            result = connect_to_mapdl.fn(mock_context_no_mapdl)
            assert "Successfully connected" in result

        # Step 2: Use MAPDL
        status = check_mapdl_status.fn(mock_context_no_mapdl)
        status_data = json.loads(status)
        assert "connection" in status_data
        assert status_data["connection"]["version"] == 24.2

        comment_result = write_comment.fn(mock_context_no_mapdl, "Test comment")
        assert "Comment written successfully" in comment_result

        command_result = run_mapdl_command.fn(mock_context_no_mapdl, "/PREP7")
        assert "MAPDL command executed successfully" in command_result

        # Step 3: Disconnect
        result = disconnect_from_mapdl.fn(mock_context_no_mapdl)
        assert "Successfully disconnected" in result

        # Step 4: Verify connection is cleared
        status_after = check_mapdl_status.fn(mock_context_no_mapdl)
        assert "No MAPDL connection available" in status_after

    def test_reconnect_after_disconnect(self, mock_context_no_mapdl):
        """Test that we can reconnect after disconnecting."""
        mock_mapdl1 = MagicMock()
        mock_mapdl1.version = "2024 R2"
        mock_mapdl1._ip = "localhost"
        mock_mapdl1._port = 50052

        mock_mapdl2 = MagicMock()
        mock_mapdl2.version = "2024 R1"
        mock_mapdl2._ip = "localhost"
        mock_mapdl2._port = 50053

        # First connection
        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl1):
            result = connect_to_mapdl.fn(mock_context_no_mapdl, port=50052)
            assert "Successfully connected" in result
            assert "50052" in result

        # Disconnect
        disconnect_from_mapdl.fn(mock_context_no_mapdl)

        # Second connection with different parameters
        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl2):
            result = connect_to_mapdl.fn(mock_context_no_mapdl, port=50053)
            assert "Successfully connected" in result
            assert "50053" in result

    def test_tools_without_connection(self, mock_context_no_mapdl):
        """Test that tools return appropriate messages without connection."""
        # Check status without connection
        status = check_mapdl_status.fn(mock_context_no_mapdl)
        assert "No MAPDL connection available" in status

        # Try to write comment without connection
        comment_result = write_comment.fn(mock_context_no_mapdl, "Test")
        assert "No MAPDL connection available" in comment_result

        # Try to run command without connection
        command_result = run_mapdl_command.fn(mock_context_no_mapdl, "/PREP7")
        assert "No MAPDL connection available" in command_result


@pytest.mark.unit
class TestLaunchWorkflow:
    """Tests for launch and usage workflow."""

    def test_launch_use_disconnect_workflow(self, mock_context_no_mapdl):
        """Test complete workflow: launch, use, disconnect."""
        # Create mock MAPDL
        mock_mapdl = MagicMock()
        mock_mapdl.name = "MAPDL"
        mock_mapdl.check_status = "Running"
        mock_mapdl.version = "2024 R2"
        mock_mapdl.ip = "127.0.0.1"
        mock_mapdl.port = 50052
        mock_mapdl.jobname = "file"
        mock_mapdl.directory = "/tmp/ansys_mapdl_1234"
        mock_mapdl.is_alive = True
        mock_mapdl.is_local = True
        mock_mapdl._exited = False
        mock_mapdl._exiting = False
        mock_mapdl.platform = "linux"

        mock_mapdl.com = MagicMock(return_value="Comment written")
        mock_mapdl.run = MagicMock(return_value="Command executed")
        # Add required class mocks
        mock_mapdl.information = MagicMock()
        mock_mapdl.information.title = ""
        mock_mapdl.information.jobname = ""
        mock_mapdl.information.routine = ""
        mock_mapdl.information.units = ""
        mock_mapdl.information.revision = ""
        mock_mapdl.information.product = ""
        mock_mapdl.geometry = MagicMock()
        mock_mapdl.geometry.n_keypoint = 0
        mock_mapdl.geometry.n_line = 0
        mock_mapdl.geometry.n_area = 0
        mock_mapdl.geometry.n_volu = 0
        mock_mapdl.post_processing = MagicMock()
        mock_mapdl.post_processing.nsets = 0
        mock_mapdl.mesh = MagicMock()
        mock_mapdl.mesh.n_node = 0
        mock_mapdl.mesh.n_elem = 0

        # Step 1: Launch
        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl):
            result = launch_mapdl.fn(mock_context_no_mapdl, nproc=4)
            assert "Successfully launched MAPDL" in result

        # Step 2: Use MAPDL
        status = check_mapdl_status.fn(mock_context_no_mapdl)
        status_data = json.loads(status)
        assert "connection" in status_data
        assert status_data["connection"]["version"] == "2024 R2"

        comment_result = write_comment.fn(mock_context_no_mapdl, "Test comment")
        assert "Comment written successfully" in comment_result

        command_result = run_mapdl_command.fn(mock_context_no_mapdl, "/PREP7")
        assert "MAPDL command executed successfully" in command_result

        # Step 3: Disconnect
        result = disconnect_from_mapdl.fn(mock_context_no_mapdl)
        assert "Successfully disconnected" in result

        # Step 4: Verify connection is cleared
        status_after = check_mapdl_status.fn(mock_context_no_mapdl)
        assert "No MAPDL connection available" in status_after

    def test_launch_after_disconnect(self, mock_context_no_mapdl):
        """Test that we can launch after disconnecting."""
        mock_mapdl1 = MagicMock()
        mock_mapdl1.version = "2024 R2"
        mock_mapdl1._ip = "127.0.0.1"
        mock_mapdl1._port = 50052
        mock_mapdl1.ip = "127.0.0.1"
        mock_mapdl1.port = 50052
        mock_mapdl1.directory = "/tmp/ansys_mapdl_1234"

        mock_mapdl2 = MagicMock()
        mock_mapdl2.version = "2024 R1"
        mock_mapdl2._ip = "127.0.0.1"
        mock_mapdl2._port = 50053
        mock_mapdl2.ip = "127.0.0.1"
        mock_mapdl2.port = 50053
        mock_mapdl2.directory = "/tmp/ansys_mapdl_5678"

        # First launch
        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl1):
            result = launch_mapdl.fn(mock_context_no_mapdl, nproc=2)
            assert "Successfully launched MAPDL" in result
            assert "50052" in result

        # Disconnect
        disconnect_from_mapdl.fn(mock_context_no_mapdl)

        # Second launch
        with patch("ansys.mapdl.core.launch_mapdl", return_value=mock_mapdl2):
            result = launch_mapdl.fn(mock_context_no_mapdl, nproc=4)
            assert "Successfully launched MAPDL" in result
            assert "50053" in result

    def test_cannot_launch_when_connected(self, mock_context_no_mapdl):
        """Test that launching fails when already connected."""
        # First, connect to an existing instance
        mock_mapdl = MagicMock()
        mock_mapdl.version = "2024 R2"
        mock_mapdl._ip = "localhost"
        mock_mapdl._port = 50052

        with patch("ansys.mapdl.core.Mapdl", return_value=mock_mapdl):
            connect_result = connect_to_mapdl.fn(mock_context_no_mapdl)
            assert "Successfully connected" in connect_result

        # Now try to launch - should fail
        launch_result = launch_mapdl.fn(mock_context_no_mapdl)
        assert "Already connected to MAPDL" in launch_result
        assert "disconnect first" in launch_result


@pytest.mark.unit
class TestScreenshot:
    """Tests for screenshot tool."""

    def test_screenshot_success_png(self, mock_context, tmp_path):
        """Test capturing a screenshot successfully with PNG format."""
        from mcp.types import ImageContent, TextContent

        # Create a fake PNG image file
        screenshot_path = tmp_path / "screenshot.png"
        fake_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        screenshot_path.write_bytes(fake_image_data)

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify result is a list
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify text content
        text_content = result[0]
        assert isinstance(text_content, TextContent)
        assert text_content.type == "text"
        assert "Screenshot saved to:" in text_content.text
        assert str(screenshot_path) in text_content.text

        # Verify image content
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        assert image_content.type == "image"
        assert image_content.mimeType == "image/png"
        assert image_content.data is not None
        assert len(image_content.data) > 0

        # Verify base64 encoding is correct
        import base64

        decoded_data = base64.b64decode(image_content.data)
        assert decoded_data == fake_image_data

    def test_screenshot_success_jpeg(self, mock_context, tmp_path):
        """Test capturing a screenshot with JPEG format."""
        from mcp.types import ImageContent, TextContent

        # Create a fake JPEG image file
        screenshot_path = tmp_path / "screenshot.jpg"
        fake_image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        screenshot_path.write_bytes(fake_image_data)

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify result structure
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify MIME type is correct for JPEG
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        assert image_content.mimeType == "image/jpeg"

    def test_screenshot_success_jpeg_extension(self, mock_context, tmp_path):
        """Test capturing a screenshot with .jpeg extension."""
        from mcp.types import ImageContent

        # Create a fake image file with .jpeg extension
        screenshot_path = tmp_path / "screenshot.jpeg"
        fake_image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        screenshot_path.write_bytes(fake_image_data)

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify MIME type is correct for .jpeg extension
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        assert image_content.mimeType == "image/jpeg"

    def test_screenshot_success_bmp(self, mock_context, tmp_path):
        """Test capturing a screenshot with BMP format."""
        from mcp.types import ImageContent

        # Create a fake BMP image file
        screenshot_path = tmp_path / "screenshot.bmp"
        fake_image_data = b"BM\x00\x00\x00\x00\x00\x00\x00\x00"
        screenshot_path.write_bytes(fake_image_data)

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify MIME type is correct for BMP
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        assert image_content.mimeType == "image/bmp"

    def test_screenshot_success_gif(self, mock_context, tmp_path):
        """Test capturing a screenshot with GIF format."""
        from mcp.types import ImageContent

        # Create a fake GIF image file
        screenshot_path = tmp_path / "screenshot.gif"
        fake_image_data = b"GIF89a\x00\x00\x00\x00"
        screenshot_path.write_bytes(fake_image_data)

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify MIME type is correct for GIF
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        assert image_content.mimeType == "image/gif"

    def test_screenshot_without_mapdl(self, mock_context_no_mapdl):
        """Test screenshot when MAPDL is not available."""
        from mcp.types import TextContent

        result = screenshot.fn(mock_context_no_mapdl)

        # Verify error message is returned
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "No MAPDL connection available" in result[0].text
        assert "connect_to_mapdl" in result[0].text

    def test_screenshot_file_not_found(self, mock_context):
        """Test screenshot when the generated file is not found."""
        from mcp.types import TextContent

        # Mock MAPDL screenshot to return a non-existent path
        nonexistent_path = "/tmp/nonexistent_screenshot.png"
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = (
            nonexistent_path
        )

        result = screenshot.fn(mock_context)

        # Verify error message is returned
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Screenshot file not found" in result[0].text
        assert nonexistent_path in result[0].text

    def test_screenshot_mapdl_error(self, mock_context):
        """Test screenshot when MAPDL raises an error."""
        from mcp.types import TextContent

        # Mock MAPDL screenshot to raise an exception
        mock_context.request_context.lifespan_context.mapdl.screenshot.side_effect = Exception(
            "Graphics window not available"
        )

        result = screenshot.fn(mock_context)

        # Verify error message is returned
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Failed to capture screenshot" in result[0].text
        assert "Graphics window not available" in result[0].text

    def test_screenshot_permission_error(self, mock_context, tmp_path):
        """Test screenshot when file cannot be read due to permissions."""
        from mcp.types import TextContent

        # Create a screenshot file
        screenshot_path = tmp_path / "screenshot.png"
        screenshot_path.write_bytes(b"fake image data")

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        # Mock the file open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = screenshot.fn(mock_context)

            # Verify error message is returned
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Failed to capture screenshot" in result[0].text
            assert "Permission denied" in result[0].text

    def test_screenshot_base64_encoding(self, mock_context, tmp_path):
        """Test that screenshot data is properly base64 encoded."""
        import base64

        from mcp.types import ImageContent

        # Create a fake image with known content
        screenshot_path = tmp_path / "screenshot.png"
        original_data = b"This is test image data with special chars: \x00\x01\x02\xff"
        screenshot_path.write_bytes(original_data)

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Get the image content
        image_content = result[1]
        assert isinstance(image_content, ImageContent)

        # Verify base64 encoding
        decoded_data = base64.b64decode(image_content.data)
        assert decoded_data == original_data

    def test_screenshot_large_image(self, mock_context, tmp_path):
        """Test screenshot with a large image file."""
        from mcp.types import ImageContent

        # Create a larger fake image (1MB)
        screenshot_path = tmp_path / "screenshot.png"
        large_image_data = b"\x89PNG" + b"\x00" * (1024 * 1024)
        screenshot_path.write_bytes(large_image_data)

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify screenshot succeeds with large file
        assert isinstance(result, list)
        assert len(result) == 2
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        assert len(image_content.data) > 0

    def test_screenshot_empty_file(self, mock_context, tmp_path):
        """Test screenshot with an empty file."""
        from mcp.types import ImageContent

        # Create an empty file
        screenshot_path = tmp_path / "screenshot.png"
        screenshot_path.write_bytes(b"")

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify screenshot handles empty file
        assert isinstance(result, list)
        assert len(result) == 2
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        # Empty file should produce empty base64 string
        assert image_content.data == ""

    def test_screenshot_calls_mapdl_method(self, mock_context, tmp_path):
        """Test that screenshot actually calls MAPDL's screenshot method."""
        # Create a fake image file
        screenshot_path = tmp_path / "screenshot.png"
        screenshot_path.write_bytes(b"fake image")

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        screenshot.fn(mock_context)

        # Verify MAPDL's screenshot method was called
        mock_context.request_context.lifespan_context.mapdl.screenshot.assert_called_once()

    def test_screenshot_unknown_extension_defaults_to_png(self, mock_context, tmp_path):
        """Test that unknown file extensions default to PNG MIME type."""
        from mcp.types import ImageContent

        # Create a file with unknown extension
        screenshot_path = tmp_path / "screenshot.xyz"
        screenshot_path.write_bytes(b"fake image data")

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify it defaults to PNG
        image_content = result[1]
        assert isinstance(image_content, ImageContent)
        assert image_content.mimeType == "image/png"

    def test_screenshot_case_insensitive_extension(self, mock_context, tmp_path):
        """Test that file extension matching is case-insensitive."""
        from mcp.types import ImageContent

        # Create files with uppercase extensions
        for ext, expected_mime in [
            (".PNG", "image/png"),
            (".JPG", "image/jpeg"),
            (".JPEG", "image/jpeg"),
            (".BMP", "image/bmp"),
            (".GIF", "image/gif"),
        ]:
            screenshot_path = tmp_path / f"screenshot{ext}"
            screenshot_path.write_bytes(b"fake image")

            mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
                screenshot_path
            )

            result = screenshot.fn(mock_context)
            image_content = result[1]
            assert isinstance(image_content, ImageContent)
            assert image_content.mimeType == expected_mime

    def test_screenshot_result_structure(self, mock_context, tmp_path):
        """Test that screenshot returns proper result structure."""
        # Create a fake image file
        screenshot_path = tmp_path / "screenshot.png"
        screenshot_path.write_bytes(b"fake image")

        # Mock MAPDL screenshot method
        mock_context.request_context.lifespan_context.mapdl.screenshot.return_value = str(
            screenshot_path
        )

        result = screenshot.fn(mock_context)

        # Verify result structure
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], TextContent)
        assert isinstance(result[1], ImageContent)
        assert str(screenshot_path) in result[0].text

    def test_screenshot_error_message(self, mock_context):
        """Test that screenshot returns proper error message on failure."""
        # Mock MAPDL screenshot to raise an exception
        mock_context.request_context.lifespan_context.mapdl.screenshot.side_effect = Exception(
            "Test error"
        )

        result = screenshot.fn(mock_context)

        # Verify error is in the return value
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Failed to capture screenshot" in result[0].text
        assert "Test error" in result[0].text
