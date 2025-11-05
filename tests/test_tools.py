"""Tests for MCP tools functionality."""

import pytest

from ansys.mapdl.mcp import check_mapdl_status, run_mapdl_command, write_comment


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
