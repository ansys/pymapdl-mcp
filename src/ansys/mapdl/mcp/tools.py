"""List of tools in PyMAPDL-MCP."""

import base64
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from fastmcp.server import Context
from fastmcp.server.server import get_logger
from mcp.types import ImageContent, TextContent

# Import MAPDL at module level to avoid import during tool execution
# The import happens during server startup, before STDIO transport is active
from ansys.mapdl import core as pymapdl  # pyright: ignore[reportMissingTypeStubs]
from ansys.mapdl.mcp import app
from ansys.mapdl.mcp.helpers import connect_to_mapdl_in_persistent_python

logger = get_logger(__name__)


# Access type-safe lifespan context in tools
@app.tool()
def check_mapdl_status(ctx: Context) -> str:
    """Check the status of MAPDL initialization.

    This tool executes the /STATUS command in MAPDL and extracts comprehensive
    information from PyMAPDL's Information, Geometry, and Post_processing classes.
    It also checks whether the MAPDL instance has exited or is exiting.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.

    Returns
    -------
    str
        JSON string containing comprehensive MAPDL status information including:
        - connection: Basic connection info (version, port, ip, directory, is_alive)
        - information: Data from Information class (title, jobname, routine, units, etc.)
        - geometry: Geometry statistics (number of keypoints, lines, areas, volumes)
        - post_processing: Post-processing availability and result sets
        - mesh: Mesh statistics (number of nodes and elements)

        Returns an error message if MAPDL is not available or has exited.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."

    try:
        from ansys.mapdl.mcp.helpers import get_info

        # Check if MAPDL has exited
        if hasattr(mapdl, "_exited") and mapdl._exited:
            return "MAPDL instance has exited. Please reconnect or launch a new instance."

        if hasattr(mapdl, "_exiting") and mapdl._exiting:
            return "MAPDL instance is currently exiting. Please wait or launch a new instance."

        info = get_info(mapdl)

        # Return as formatted JSON
        return json.dumps(info, indent=2)

    except Exception as e:
        error_msg = f"Error checking MAPDL status: {str(e)}"
        logger.error(error_msg)
        return error_msg


@app.tool()
def check_mapdl_installed(ctx: Context) -> str:
    """Check if MAPDL is installed on the system.

    This tool uses PyMAPDL's check_valid_ansys function to verify if a valid
    ANSYS/MAPDL installation is available on the system.

    Returns
    -------
    str
        Status message indicating whether MAPDL is installed or not.
    """
    logger.info("Checking if MAPDL is installed...")

    try:
        from ansys.mapdl.core.launcher import (  # type: ignore
            check_valid_ansys,
            get_default_ansys_path,
        )

        is_installed = check_valid_ansys()

        if is_installed:
            logger.info("MAPDL installation found")
            return f"MAPDL is installed on this system in: {get_default_ansys_path()}"
        else:
            logger.info("MAPDL installation not found")
            return (
                "MAPDL is not installed on this system or cannot be found in the "
                "standard locations. Please ensure ANSYS/MAPDL is properly installed "
                "and the installation path is correct."
            )

    except Exception as e:
        error_msg = f"Error checking MAPDL installation: {str(e)}"
        logger.error(error_msg)
        return error_msg


@app.tool()
def write_comment(ctx: Context, comment: str) -> str:
    """Write a comment in the MAPDL session.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    comment : str
        The comment text to write in MAPDL.

    Returns
    -------
    str
        Confirmation message with the comment execution result.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."

    logger.info(f"Writing comment: {comment}")
    result = mapdl.com(f"{comment}", mute=True)  # type: ignore[union-attr]
    return f"Comment written successfully: {result}"


@app.tool()
def run_mapdl_command(ctx: Context, cmd: str) -> str:
    """Execute an arbitrary MAPDL command.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    cmd : str
        The MAPDL command to execute.

    Returns
    -------
    str
        Command execution result.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."

    result = mapdl.run(cmd)  # type: ignore[union-attr]
    return f"MAPDL command executed successfully: {result}"


@app.tool()
def run_multiple_commands(ctx: Context, commands: list[str]) -> str:
    """Execute multiple MAPDL commands in sequence using input_strings.

    This tool is optimized for running multiple commands efficiently by using
    MAPDL's input_strings method, which processes commands in batch mode.
    This is significantly faster than executing commands one by one.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    commands : list[str]
        List of MAPDL commands to execute in sequence.

    Returns
    -------
    str
        Execution result with summary of commands executed.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."

    if not commands:
        return "No commands provided. Please provide a list of commands to execute."

    if not isinstance(commands, list):  # type: ignore
        return "Commands must be provided as a list of strings."

    # Filter out empty commands
    valid_commands = [cmd.strip() for cmd in commands if cmd and cmd.strip()]

    if not valid_commands:
        return "No valid commands found after filtering empty entries."

    try:
        logger.info(f"Executing {len(valid_commands)} MAPDL commands using input_strings")

        # Use input_strings for batch command execution
        result = mapdl.input_strings(valid_commands)  # type: ignore[union-attr]

        success_msg = (
            f"Successfully executed {len(valid_commands)} MAPDL commands:\n"
            f"Commands:\n" + "\n".join(f"  {i+1}. {cmd}" for i, cmd in enumerate(valid_commands))
        )

        if result:
            success_msg += f"\n\nOutput:\n{result}"

        return success_msg

    except Exception as e:
        error_msg = (
            f"Error executing commands. Executed {len(valid_commands)} commands "
            f"but encountered error: {str(e)}\n"
            f"Commands that were attempted:\n"
            + "\n".join(f"  {i+1}. {cmd}" for i, cmd in enumerate(valid_commands))
        )
        logger.error(error_msg)
        return error_msg


@app.tool()
def launch_mapdl(
    ctx: Context,
    exec_file: str | None = None,
    port: int | None = None,
    run_location: str | None = None,
    nproc: int | None = None,
    additional_switches: str = "",
) -> str:
    """Launch a new MAPDL instance.

    This tool starts a new MAPDL instance using PyMAPDL's launch_mapdl function.
    The launched instance will be automatically connected and stored in the context
    for subsequent operations. The instance can be closed using the disconnect_from_mapdl tool.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    exec_file : str, optional
        The path to the MAPDL executable. If None, PyMAPDL will attempt to find
        the MAPDL executable automatically.
    port : int, optional
        The gRPC port for MAPDL to listen on. If None, a default port will be used.
    run_location : str, optional
        The directory where MAPDL will run and store files. If None, a temporary
        directory will be created.
    nproc : int | None, optional
        Number of processors to use. Default is None. MAPDL will decide based on
        available resources.
    additional_switches : str, optional
        Additional command line switches to pass to MAPDL. Default is empty string.

    Returns
    -------
    str
        Launch status message with MAPDL version and connection information.
    """
    logger.info("Launching new MAPDL instance...")

    try:
        # Check if there's already a connection
        if ctx.request_context.lifespan_context.mapdl is not None:
            return (
                f"Already connected to MAPDL at "
                f"{ctx.request_context.lifespan_context.mapdl._ip}:"
                f"{ctx.request_context.lifespan_context.mapdl._port}. "
                f"Please disconnect first using disconnect_from_mapdl tool."
            )

        # Launch new MAPDL instance
        kwargs: dict[str, Any] = {
            "nproc": nproc,
            "loglevel": "INFO",
            "port": port,
        }

        if exec_file is not None:
            kwargs["exec_file"] = exec_file

        if run_location is not None:
            kwargs["run_location"] = run_location

        if additional_switches:
            kwargs["additional_switches"] = additional_switches

        # Launch MAPDL - import already done at module level
        mapdl = pymapdl.launch_mapdl(**kwargs)

        # Store in context for later use
        ctx.request_context.lifespan_context.mapdl = mapdl

        logger.info(f"MAPDL launched successfully at {mapdl.ip}:{mapdl.port}!")
        return (
            f"Successfully launched MAPDL at {mapdl.ip}:{mapdl.port}\n"
            f"MAPDL Version: {mapdl.version}\n"
            f"Working Directory: {mapdl.directory}\n"
        )

    except Exception as e:
        error_msg = f"Failed to launch MAPDL: {str(e)}"
        logger.error(error_msg)
        return error_msg


@app.tool()
def connect_to_mapdl(ctx: Context, port: int = 50052, ip: str = "localhost") -> str:
    """Connect to an existing MAPDL instance.

    This tool establishes a connection to a running MAPDL instance using the
    provided port and IP address. The connection is stored for subsequent
    operations and can be closed using the disconnect_from_mapdl tool.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    port : int, optional
        The gRPC port where MAPDL is listening. Default is 50052.
    ip : str, optional
        The IP address where MAPDL is running. Default is "localhost".

    Returns
    -------
    str
        Connection status message with MAPDL version information.
    """
    logger.info(f"Connecting to MAPDL instance at {ip}:{port}...")

    try:
        # Check if there's already a connection
        if ctx.request_context.lifespan_context.mapdl is not None:
            return (
                f"Already connected to MAPDL at "
                f"{ctx.request_context.lifespan_context.mapdl._ip}:"
                f"{ctx.request_context.lifespan_context.mapdl._port}. "
                f"Please disconnect first using disconnect_from_mapdl tool."
            )

        # Connect to existing MAPDL instance
        mapdl = pymapdl.Mapdl(
            start_instance=False,
            ip=ip,
            port=port,
            cleanup_on_exit=False,  # Don't clean up since we didn't launch it
            loglevel="INFO",
        )

        # Store in context for later use
        ctx.request_context.lifespan_context.mapdl = mapdl

        logger.info(f"Connected to MAPDL successfully at {ip}:{port}!")
        return (
            f"Successfully connected to MAPDL at {ip}:{port}\n" f"MAPDL Version: {mapdl.version}\n"
        )

    except Exception as e:
        error_msg = f"Failed to connect to MAPDL at {ip}:{port}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@app.tool()
def disconnect_from_mapdl(ctx: Context) -> str:
    """Disconnect from the dynamically connected MAPDL instance.

    This tool closes the connection to the MAPDL instance that was established
    using the connect_to_mapdl tool and releases the associated resources.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Disconnection status message.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return "No MAPDL connection to disconnect."

    try:
        ip = mapdl._ip
        port = mapdl._port
        logger.info(f"Disconnecting from MAPDL at {ip}:{port}...")

        # Exit the MAPDL connection
        # Just disconnect the client
        mapdl.exit()
        del mapdl

        # Clear from context
        ctx.request_context.lifespan_context.mapdl = None

        logger.info("Disconnected successfully!")
        return f"Successfully disconnected from MAPDL at {ip}:{port}"

    except Exception as e:
        error_msg = f"Error during disconnect: {str(e)}"
        logger.error(error_msg)
        # Still clear the reference even if disconnect failed
        ctx.request_context.lifespan_context.mapdl = None
        return error_msg


@app.tool()
def list_mapdl_instances() -> str:
    """List all MAPDL instances running on the local machine.

    This tool uses PyMAPDL CLI's list_instances function to discover
    MAPDL instances running on the machine by scanning for active gRPC
    servers and their associated metadata.

    Returns
    -------
    str
        Formatted table containing information about all running MAPDL instances
        including their names, status, gRPC ports, IP addresses, PIDs, and
        working directories.
    """
    logger.info("Searching for MAPDL instances using PyMAPDL CLI...")

    from ansys.mapdl.mcp.helpers import list_instances

    # Use PyMAPDL CLI's list_instances function with long=True for detailed output
    return list_instances(long=True, instances=True)


@app.tool()
def screenshot(
    ctx: Context,
) -> list[TextContent | ImageContent]:
    """Capture a screenshot of the current MAPDL graphics window.

    This tool captures the current state of the MAPDL graphics window after using
    MAPDL native plotting commands. Use this tool for all standard MAPDL plots as
    they provide interactive plots that are directly accessible.

    MAPDL Native Plot Commands (use with screenshot):
    - Geometry: aplot(), lplot(), kplot(), vplot()
    - Mesh: eplot(), nplot()
    - Post-processing: plnsol(), plesol(), pldisp()
    - Post-processing object: mapdl.post_processing.plot_nodal_solution(), etc.

    For custom matplotlib or PyVista plots, use the create_custom_plot tool instead.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.

    Returns
    -------
    list[TextContent | ImageContent]
        A list containing:
        - TextContent with the screenshot file path
        - ImageContent with the base64-encoded image data
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return [
            TextContent(
                type="text",
                text=(
                    "No MAPDL connection available. "
                    "Use connect_to_mapdl tool to establish a connection."
                ),
            )
        ]

    try:
        logger.info("Capturing MAPDL screenshot...")

        # Create a temporary file with .png extension
        temp_fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="mapdl_screenshot_")

        # Close the file descriptor as MAPDL will write to the path
        os.close(temp_fd)

        # Capture screenshot directly to the temporary location
        screenshot_path = mapdl.screenshot(savefig=temp_path)  # type: ignore[union-attr]

        # Verify file was created
        image_path = Path(screenshot_path)
        if not image_path.exists():
            error_msg = f"Screenshot file not found: {screenshot_path}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]

        # Read image data
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Encode to base64
        base64_data = base64.b64encode(image_data).decode("utf-8")

        # Determine mime type based on file extension
        mime_type = "image/png"  # Default to PNG
        if image_path.suffix.lower() in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif image_path.suffix.lower() == ".bmp":
            mime_type = "image/bmp"
        elif image_path.suffix.lower() == ".gif":
            mime_type = "image/gif"

        logger.info(f"Screenshot captured successfully: {screenshot_path}")

        # Return both text (file path) and image content
        return [
            TextContent(type="text", text=f"Screenshot saved to: {screenshot_path}"),
            ImageContent(type="image", data=base64_data, mimeType=mime_type),
        ]

    except Exception as e:
        if "temp_path" in locals() and Path(temp_path).exists():  # type: ignore
            Path(temp_path).unlink()  # pyright: ignore[reportPossiblyUnboundVariable]

        error_msg = f"Failed to capture screenshot: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]


####################################################################################################
# Tools that uses the PythonPersistentSession


@app.tool()
def run_python_code (
    ctx: Context,
    code: str,
    timeout: int = 60,
) -> str:
    """Execute arbitrary Python code in the persistent Python session.

    This tool should be used for custom Python code execution, particularly for:
    - Custom data processing and analysis
    - Creating custom matplotlib plots not available in MAPDL
    - Advanced PyVista visualizations beyond MAPDL's native capabilities
    - NumPy/Pandas data manipulation and custom visualization

    NOTE: For MAPDL native plotting (aplot, lplot, kplot, post_processing plots, etc.),
    use the normal MAPDL session commands with the screenshot tool instead, as they
    provide interactive plots that are directly accessible.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    code : str
        The Python code to execute.
    timeout : int, optional
        Maximum time in seconds to allow for code execution. Default is 60 seconds.

    Returns
    -------
    str
        Execution result or error message. Returns JSON for structured output
        compatible with both stdio and http transports.
    """
    session = ctx.request_context.lifespan_context.python_session

    if session is None:
        return json.dumps(
            {
                "success": False,
                "error": "No Python session available. The persistent Python session was not initialized.",  # noqa: E501
            },
            ensure_ascii=False,
        )

    # Check if MAPDL is connected in the persistent session
    mapdl_instance = session.metadata.get("mapdl", None)
    if mapdl_instance is None:
        mapdl_instance = connect_to_mapdl_in_persistent_python(ctx)

    if mapdl_instance is None:
        return json.dumps(
            {
                "success": False,
                "error": "An error occurred while connecting to MAPDL in the persistent Python session. Please, restart the session and try again.",  # noqa: E501
            },
            ensure_ascii=False,
        )
    try:
        # Sanitize the input code to remove problematic Unicode characters
        # This prevents encoding issues on Windows systems with limited charsets
        sanitized_code = _sanitize_output(code)

        logger.info(f"Executing Python code in persistent session:\n{sanitized_code}")

        # Execute code in persistent session
        # The 'mapdl' object is already stored in session.metadata and should be accessible
        result = session.execute(sanitized_code, timeout=timeout)

        # Parse the result which should be a dict with 'success', 'stdout', 'stderr', 'error'
        if isinstance(result, dict):
            # Result is already a structured dict from PersistentPythonSession
            # Sanitize stdout and stderr to handle encoding issues
            stdout = _sanitize_output(result.get("stdout", ""))
            stderr = _sanitize_output(result.get("stderr", ""))

            if result.get("success"):
                return json.dumps(
                    {
                        "success": True,
                        "stdout": stdout,
                        "stderr": stderr,
                        "message": "Python code executed successfully",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            else:
                # Execution failed - provide detailed error information
                error_msg = result.get("error", "Unknown error occurred")
                error_msg = _sanitize_output(error_msg)
                return json.dumps(
                    {"success": False, "stdout": stdout, "stderr": stderr, "error": error_msg},
                    ensure_ascii=False,
                    indent=2,
                )
        else:
            # Fallback if result is not a dict
            return json.dumps(
                {
                    "success": True,
                    "stdout": _sanitize_output(str(result)) if result else "",
                    "stderr": "",
                    "message": "Python code executed successfully",
                },
                ensure_ascii=False,
                indent=2,
            )

    except TimeoutError:
        error_dict = {
            "success": False,
            "error": f"Python code execution timed out after {timeout} seconds",
        }
        logger.error(error_dict["error"])
        return json.dumps(error_dict, ensure_ascii=False)

    except Exception as e:
        error_dict = {"success": False, "error": f"Error executing Python code: {str(e)}"}
        logger.error(error_dict["error"])
        return json.dumps(error_dict, ensure_ascii=False)


@app.tool()
def create_custom_plot(
    ctx: Context,
    plot_code: str,
    plot_type: str = "matplotlib",
    return_base64: bool = True,
    timeout: int = 60,
) -> list[TextContent | ImageContent]:
    """Create a custom plot using matplotlib or PyVista in the persistent Python session.

    This tool is specifically designed for creating custom plots that are NOT available
    in MAPDL's native plotting capabilities. Use this when you need:
    - Custom matplotlib visualizations (line plots, bar charts, histograms, etc.)
    - Advanced PyVista 3D visualizations beyond MAPDL defaults
    - Combined data from multiple sources
    - Custom data processing with visualization

    IMPORTANT: For standard MAPDL plots (aplot, lplot, kplot, post_processing plots),
    use the normal MAPDL commands with the screenshot tool instead for interactive plots.

    The persistent Python session has pre-configured matplotlib (Agg backend) and
    PyVista (off-screen rendering) with helper functions:
    - save_matplotlib_plot(filename, return_base64, dpi)
    - save_plot(plotter, filename, return_base64)

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    plot_code : str
        Python code to create the plot. Should use matplotlib.pyplot or PyVista.
        For matplotlib, the code should create the figure/plot but NOT call plt.show().
        Use the save_matplotlib_plot() or save_plot() helper functions to return the plot.
    plot_type : str, optional
        Type of plot: "matplotlib" or "pyvista". Default is "matplotlib".
    return_base64 : bool, optional
        If True, returns base64-encoded image data. If False, saves to file. Default is True.
    timeout : int, optional
        Maximum time in seconds for plot generation. Default is 60 seconds.

    Returns
    -------
    list[TextContent | ImageContent]
        A list containing:
        - TextContent with the plot creation status message
        - ImageContent with the base64-encoded image data (if successful and return_base64=True)

    Examples
    --------
    Create a custom matplotlib line plot:
    >>> plot_code = '''
    ... import matplotlib.pyplot as plt
    ... import numpy as np
    ...
    ... # Extract data from MAPDL
    ... displacements = mapdl.get_array("NODE", item1="U", it1num="Y")
    ...
    ... # Create custom plot
    ... plt.figure(figsize=(10, 6))
    ... plt.plot(displacements)
    ... plt.xlabel("Node Number")
    ... plt.ylabel("Displacement (m)")
    ... plt.title("Custom Displacement Plot")
    ... plt.grid(True)
    ...
    ... # Save and return
    ... result = save_matplotlib_plot(return_base64=True, dpi=150)
    ... print(result)
    ... '''
    >>> create_custom_plot(ctx, plot_code, plot_type="matplotlib")
    """
    session = ctx.request_context.lifespan_context.python_session

    if session is None:
        return [
            TextContent(
                type="text",
                text="No Python session available. The persistent Python session was not initialized.",
            )
        ]

    # Check if MAPDL is connected in the persistent session
    mapdl_instance = session.metadata.get("mapdl", None)
    if mapdl_instance is None:
        connect_to_mapdl_in_persistent_python(ctx)
        return [
            TextContent(
                type="text",
                text="An error occurred while connecting to MAPDL in the persistent Python session. Please, restart the session and try again.",
            )
        ]

    try:
        logger.info(f"Creating custom {plot_type} plot in persistent session")

        # Sanitize the plot code to remove problematic Unicode characters
        # This prevents encoding issues on Windows systems with limited charsets
        sanitized_plot_code = _sanitize_output(plot_code)

        # Execute the plot code
        result = session.execute(sanitized_plot_code, timeout=timeout)

        # Parse the result
        if isinstance(result, dict):
            stdout = _sanitize_output(result.get("stdout", ""))
            stderr = _sanitize_output(result.get("stderr", ""))

            if result.get("success"):
                # Try to extract plot data from stdout
                # The helper functions return data URI format: "data:image/png;base64,<base64_string>"
                plot_data = stdout.strip()

                # Check if the output contains a base64 data URI
                if "data:image/png;base64," in plot_data:
                    # Extract the base64 part
                    base64_data = plot_data.split("data:image/png;base64,")[1].strip()

                    return [
                        TextContent(
                            type="text",
                            text=f"Custom {plot_type} plot created successfully",
                        ),
                        ImageContent(type="image", data=base64_data, mimeType="image/png"),
                    ]
                elif plot_data.startswith("Plot saved to"):
                    # File path returned
                    return [
                        TextContent(
                            type="text",
                            text=f"Custom {plot_type} plot created successfully\n{plot_data}",
                        )
                    ]
                else:
                    # Unexpected output format
                    return [
                        TextContent(
                            type="text",
                            text=f"Plot created but unexpected output format:\n{stdout}",
                        )
                    ]
            else:
                error_msg = result.get("error", "Unknown error occurred")
                error_msg = _sanitize_output(error_msg)
                return [
                    TextContent(
                        type="text",
                        text=f"Error creating custom {plot_type} plot: {error_msg}\nStdout: {stdout}\nStderr: {stderr}",
                    )
                ]
        else:
            # Fallback if result is not a dict
            return [
                TextContent(
                    type="text",
                    text=f"Unexpected result format: {_sanitize_output(str(result)) if result else 'No result'}",
                )
            ]

    except TimeoutError:
        error_msg = f"Plot creation timed out after {timeout} seconds"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        error_msg = f"Error creating custom plot: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]


def _sanitize_output(text: str) -> str:
    """Sanitize output text to handle encoding issues.

    This function removes or replaces problematic Unicode characters that can cause
    encoding issues on Windows systems with limited character sets (e.g., charmap).

    Parameters
    ----------
    text : str
        The text to sanitize.

    Returns
    -------
    str
        The sanitized text with problematic characters removed or replaced.
    """
    if not isinstance(text, str):
        return text

    # Replace common problematic Unicode characters with ASCII alternatives
    replacements = {
        # Checkmarks and crosses
        "\u2713": "[OK]",  # checkmark
        "\u2717": "[X]",  # cross
        # Box drawing characters
        "\u2514": "\\",  # box drawing
        "\u2502": "|",  # box drawing
        "\u2500": "-",  # box drawing
        "\u2510": "\\",  # box drawing
        "\u250c": "/",  # box drawing
        "\u2518": "/",  # box drawing
        # Block elements
        "\u2588": "#",  # block
        "\u2589": "#",  # block
        "\u258a": "#",  # block
        "\u258c": "|",  # block
        "\u2590": "|",  # block
        # Superscript and subscript characters
        "\u00b9": "^1",  # superscript 1
        "\u00b2": "^2",  # superscript 2
        "\u00b3": "^3",  # superscript 3
        "\u2074": "^4",  # superscript 4
        "\u2075": "^5",  # superscript 5
        "\u2076": "^6",  # superscript 6
        "\u2077": "^7",  # superscript 7
        "\u2078": "^8",  # superscript 8
        "\u2079": "^9",  # superscript 9
        "\u2070": "^0",  # superscript 0
        # Other commonly problematic characters
        "\u2022": "*",  # bullet
        "\u2023": "*",  # triangular bullet
        "\u2219": "*",  # bullet operator
        "\u00a0": " ",  # non-breaking space
        "\u200b": "",  # zero-width space
        "\u200c": "",  # zero-width non-joiner
        "\u200d": "",  # zero-width joiner
        "\ufeff": "",  # zero-width no-break space
    }

    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)

    # Remove any remaining characters that can't be encoded in ascii
    try:
        # Try to encode as ASCII to check for problematic characters
        text.encode("ascii")
    except UnicodeEncodeError:
        # If there are non-ASCII characters, replace them with a replacement character
        text = text.encode("ascii", errors="replace").decode("ascii")

    return text
