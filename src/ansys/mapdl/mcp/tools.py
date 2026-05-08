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

"""List of tools in PyMAPDL-MCP."""

import base64
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from ansys.common.mcp.tools import create_custom_plot, execute_python_code
from fastmcp.server import Context
from fastmcp.tools.base import ToolResult

# Import MAPDL at module level to avoid import during tool execution
# The import happens during server startup, before STDIO transport is active
from ansys.mapdl import core as pymapdl  # pyright: ignore[reportMissingTypeStubs]
from ansys.mapdl.mcp import app
from ansys.mapdl.mcp.helpers import connect_to_mapdl_in_persistent_python, logger
from mcp.types import ImageContent, TextContent


def _text_result(text: str) -> ToolResult:
    """Wrap a plain text string in a single-content ToolResult."""
    return ToolResult([TextContent(type="text", text=text)])


# Tag applied to all tools that require an active MAPDL connection.
# These tools are disabled at startup (before MAPDL is connected) and enabled
# once a connection is established via connect_to_mapdl or launch_mapdl_session.
REQUIRES_MAPDL_TAG = "requires_mapdl"


# Access type-safe lifespan context in tools
@app.tool(tags={REQUIRES_MAPDL_TAG})
def check_mapdl_status(ctx: Context) -> ToolResult:
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
    ToolResult
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
        return _text_result(
            "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."
        )

    try:
        from ansys.mapdl.mcp.helpers import get_info

        # Check if MAPDL has exited
        if hasattr(mapdl, "_exited") and mapdl._exited:
            return _text_result(
                "MAPDL instance has exited. Please reconnect or launch a new instance."
            )

        if hasattr(mapdl, "_exiting") and mapdl._exiting:
            return _text_result(
                "MAPDL instance is currently exiting. Please wait or launch a new instance."
            )

        info = get_info(mapdl)

        return _text_result(json.dumps(info, indent=2))

    except Exception as e:
        error_msg = f"Error checking MAPDL status: {str(e)}"
        logger.error(error_msg)
        return _text_result(error_msg)


@app.tool(tags={"aali"})
def check_mapdl_installed(ctx: Context) -> ToolResult:
    """Check if MAPDL is installed on the system.

    This tool lists all ANSYS/MAPDL installations found on the system,
    including their version numbers and executable paths.

    Returns
    -------
    ToolResult
        Status message listing all found MAPDL installations, or a message
        indicating that no installation was found.
    """
    import os
    from pathlib import Path

    logger.info("Checking if MAPDL is installed...")

    try:
        from ansys.tools.common.path import (  # type: ignore
            get_available_ansys_installations,
        )

        installations = get_available_ansys_installations()

        if not installations:
            logger.info("MAPDL installation not found")
            return _text_result(
                "MAPDL is not installed on this system or cannot be found in the "
                "standard locations. Please ensure ANSYS/MAPDL is properly installed "
                "and the installation path is correct."
            )

        lines = [f"MAPDL is installed on this system. Found {len(installations)} installation(s):"]
        for version_int, base_path in installations.items():
            is_student = version_int < 0
            abs_version = abs(version_int)
            ansys_bin_path = Path(base_path) / "ansys" / "bin"
            if os.name == "nt":
                ansys_bin = ansys_bin_path / "winx64" / f"ansys{abs_version}.exe"
            else:
                ansys_bin = ansys_bin_path / f"ansys{abs_version}"
            student_label = " (Student)" if is_student else ""
            lines.append(f"  - Version {abs_version}{student_label}: {ansys_bin}")

        logger.info(f"Found {len(installations)} MAPDL installation(s)")
        return _text_result("\n".join(lines))

    except Exception as e:
        error_msg = f"Error checking MAPDL installation: {str(e)}"
        logger.error(error_msg)
        return _text_result(error_msg)


@app.tool(tags={REQUIRES_MAPDL_TAG})
def run_mapdl_command(ctx: Context, cmd: str, comment: str = "", header: str = "") -> ToolResult:
    """Execute an arbitrary MAPDL command.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    cmd : str
        The MAPDL command to execute.
    comment : str, optional
        An optional comment to include before the command execution. Default is empty string.
    header : str, optional
        An optional header to include before the command execution. Default is empty string.

    Returns
    -------
    ToolResult
        Command execution result.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return _text_result(
            "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."
        )

    if header:
        mapdl.com(f"# {header}", mute=True)  # type: ignore[union-attr]
    if comment:
        for each_line in comment.splitlines():
            mapdl.com(f"{each_line}", mute=True)  # type: ignore[union-attr]

    result = mapdl.run(cmd)  # type: ignore[union-attr]
    return _text_result(f"MAPDL command executed successfully: {result}")


@app.tool(tags={"aali", REQUIRES_MAPDL_TAG})
def run_multiple_commands(
    ctx: Context, commands: list[str], comment: str = "", header: str = ""
) -> ToolResult:
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
    comment : str, optional
        An optional comment to include before the command execution. Default is empty string.
    header : str, optional
        An optional header to include before the command execution. Default is empty string.

    Returns
    -------
    ToolResult
        Execution result with summary of commands executed.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return _text_result(
            "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."
        )

    if not commands:
        return _text_result("No commands provided. Please provide a list of commands to execute.")

    if not isinstance(commands, list):  # type: ignore
        return _text_result("Commands must be provided as a list of strings.")

    # Filter out empty commands
    valid_commands = [cmd.strip() for cmd in commands if cmd and cmd.strip()]

    if not valid_commands:
        return _text_result("No valid commands found after filtering empty entries.")

    try:
        logger.info(f"Executing {len(valid_commands)} MAPDL commands using input_strings")

        if header:
            mapdl.com(f"# {header}", mute=True)  # type: ignore[union-attr]
        if comment:
            for each_line in comment.splitlines():
                mapdl.com(f"{each_line}", mute=True)  # type: ignore[union-attr]

        # Use input_strings for batch command execution
        result = mapdl.input_strings(valid_commands)  # type: ignore[union-attr]

        success_msg = (
            f"Successfully executed {len(valid_commands)} MAPDL commands:\n"
            f"Commands:\n" + "\n".join(f"  {i + 1}. {cmd}" for i, cmd in enumerate(valid_commands))
        )

        if result:
            success_msg += f"\n\nOutput:\n{result}"

        return ToolResult(
            [
                TextContent(type="text", text="True"),
                TextContent(type="text", text=success_msg),
            ],
            structured_content={
                "success": True,
                "commands_executed": valid_commands,
                "output": result or "",
            },
        )

    except Exception as e:
        error_msg = (
            f"Error executing commands. Executed {len(valid_commands)} commands "
            f"but encountered error: {str(e)}\n"
            f"Commands that were attempted:\n"
            + "\n".join(f"  {i + 1}. {cmd}" for i, cmd in enumerate(valid_commands))
        )
        logger.error(error_msg)
        return ToolResult([TextContent(type="text", text=error_msg)])


@app.tool(tags={"aali", "locked_connection"})
async def launch_mapdl_session(
    ctx: Context,
    exec_file: str | None = None,
    port: int | None = None,
    run_location: str | None = None,
    nproc: int | None = None,
    additional_switches: str = "",
) -> ToolResult:
    """Launch a new MAPDL instance.

    This tool starts a new MAPDL instance using PyMAPDL's launch_mapdl function.
    The launched instance will be automatically connected and stored in the context
    for subsequent operations. The instance can be closed using the disconnect_from_mapdl tool.
    Once you are connected to the launched instance, other tools become available
    to interact with it, such as run_mapdl_command, check_mapdl_status, screenshot, and more.

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
    ToolResult
        Launch status message with MAPDL version and connection information.
    """
    logger.info("Launching new MAPDL instance...")

    try:
        # Check if there's already a connection
        if ctx.request_context.lifespan_context.mapdl is not None:
            return _text_result(
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

        await ctx.enable_components(tags={REQUIRES_MAPDL_TAG})
        logger.info(f"MAPDL launched successfully at {mapdl.ip}:{mapdl.port}!")
        return _text_result(
            f"Successfully launched MAPDL at {mapdl.ip}:{mapdl.port}\n"
            f"MAPDL Version: {mapdl.version}\n"
            f"Working Directory: {mapdl.directory}\n"
        )

    except Exception as e:
        error_msg = f"Failed to launch MAPDL: {str(e)}"
        logger.error(error_msg)
        return _text_result(error_msg)


@app.tool(tags={"aali", "locked_connection"})
async def connect_to_mapdl(ctx: Context, port: int = 50052, ip: str = "localhost") -> ToolResult:
    """Connect to an existing MAPDL instance.

    This tool establishes a connection to a running MAPDL instance using the
    provided port and IP address. The connection is stored for subsequent
    operations and can be closed using the disconnect_from_mapdl tool.
    Once you are connected to the MAPDL instance, other tools become available
    to interact with it, such as run_mapdl_command, check_mapdl_status, screenshot, and more.

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
    ToolResult
        Connection status message with MAPDL version information.
    """
    logger.info(f"Connecting to MAPDL instance at {ip}:{port}...")

    try:
        # Check if there's already a connection
        if ctx.request_context.lifespan_context.mapdl is not None:
            return _text_result(
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

        await ctx.enable_components(tags={REQUIRES_MAPDL_TAG})
        logger.info(f"Connected to MAPDL successfully at {ip}:{port}!")
        return _text_result(
            f"Successfully connected to MAPDL at {ip}:{port}\nMAPDL Version: {mapdl.version}\n"
        )

    except Exception as e:
        error_msg = f"Failed to connect to MAPDL at {ip}:{port}: {str(e)}"
        logger.error(error_msg)
        return _text_result(error_msg)


@app.tool(tags={"aali", "locked_connection", REQUIRES_MAPDL_TAG})
async def disconnect_from_mapdl(ctx: Context) -> ToolResult:
    """Disconnect from the dynamically connected MAPDL instance.

    This tool closes the connection to the MAPDL instance that was established
    using the connect_to_mapdl tool and releases the associated resources.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.

    Returns
    -------
    ToolResult
        Disconnection status message.
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return _text_result("No MAPDL connection to disconnect.")

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

        await ctx.disable_components(tags={REQUIRES_MAPDL_TAG})
        logger.info("Disconnected successfully!")
        return _text_result(f"Successfully disconnected from MAPDL at {ip}:{port}")

    except Exception as e:
        error_msg = f"Error during disconnect: {str(e)}"
        logger.error(error_msg)
        # Still clear the reference even if disconnect failed
        ctx.request_context.lifespan_context.mapdl = None
        return _text_result(error_msg)


@app.tool()
def list_mapdl_instances(ctx: Context) -> ToolResult:
    """List all MAPDL instances running on the local machine and any remotely connected instance.

    This tool uses PyMAPDL CLI's list_instances function to discover
    MAPDL instances running on the machine by scanning for active gRPC
    servers and their associated metadata. It also includes any remotely
    connected MAPDL instance that was established via the connect_to_mapdl tool.

    Returns
    -------
    ToolResult
        Formatted table containing information about all running MAPDL instances
        including their names, status, gRPC ports, IP addresses, PIDs, and
        working directories. If a remote instance is connected, it is listed in a
        separate section below the local instances.
    """
    logger.info("Searching for MAPDL instances using PyMAPDL CLI...")

    from tabulate import tabulate

    from ansys.mapdl.mcp.helpers import list_instances

    # Use PyMAPDL CLI's list_instances function with long=True for detailed output
    local_table = list_instances(long=True, instances=True)

    # Also include any remotely connected instance from the current session context
    mapdl = ctx.request_context.lifespan_context.mapdl
    if mapdl is not None and not mapdl.is_local:
        remote_headers = ["IP", "Port", "Status", "Version", "Working directory"]
        remote_row = [
            mapdl.ip,
            mapdl.port,
            mapdl.check_status,
            mapdl.version,
            str(mapdl.directory),
        ]
        remote_table = tabulate([remote_row], remote_headers)
        return _text_result(f"{local_table}\n\nRemotely connected instance:\n{remote_table}")

    return _text_result(local_table)


@app.tool(tags={"aali", REQUIRES_MAPDL_TAG})
def screenshot(
    ctx: Context,
    commands: str = "",
) -> ToolResult:
    """Capture a screenshot of the current MAPDL graphics window.

    This tool captures the current state of the MAPDL graphics window after using
    MAPDL native plotting commands. Use this tool for all standard MAPDL plots.

    MAPDL Native Plot Commands (use with screenshot):
    - Geometry: APLOT, LPLOT, KPLOT, VPLOT
    - Mesh: EPLOT, NPLOT
    - Post-processing: PLNSOL, PLESOL, PLDISP

    For custom matplotlib or PyVista plots, use the custom_plot tool instead.

    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.
    commands : str, optional
        Optional MAPDL commands to execute before taking the screenshot.
        Avoid running commands that are not related to plotting or visualization.
        This can be used to set up the plot or visualization before capturing.
        Avoid running long or complex commands that may delay the screenshot.
        Default is empty string.

    Returns
    -------
    ToolResult
        A result containing:
        - TextContent with the screenshot file path
        - ImageContent with the base64-encoded image data
    """
    mapdl = ctx.request_context.lifespan_context.mapdl

    if mapdl is None:
        return _text_result(
            "No MAPDL connection available. Use connect_to_mapdl tool to establish a connection."
        )

    try:
        logger.info("Capturing MAPDL screenshot...")

        # Create a temporary file with .png extension
        temp_fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="mapdl_screenshot_")

        # Close the file descriptor as MAPDL will write to the path
        os.close(temp_fd)

        if commands:
            mapdl.input_string(commands)  # type: ignore[union-attr]

        # Capture screenshot directly to the temporary location
        screenshot_path = mapdl.screenshot(savefig=temp_path)  # type: ignore[union-attr]

        # Verify file was created
        image_path = Path(screenshot_path)
        if not image_path.exists():
            error_msg = f"Screenshot file not found: {screenshot_path}"
            logger.error(error_msg)
            return _text_result(error_msg)

        # Read image data
        # Ignoring PTH123 since the file is created by MAPDL
        with open(screenshot_path, "rb") as f:  # noqa: PTH123
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

        return ToolResult(
            [
                TextContent(type="text", text=f"Screenshot saved to: {screenshot_path}"),
                ImageContent(type="image", data=base64_data, mimeType=mime_type),
            ]
        )

    except Exception as e:
        if "temp_path" in locals() and Path(temp_path).exists():  # type: ignore
            Path(temp_path).unlink()  # pyright: ignore[reportPossiblyUnboundVariable]

        error_msg = f"Failed to capture screenshot: {str(e)}"
        logger.error(error_msg)
        return _text_result(error_msg)


####################################################################################################
# Tools that uses the PythonPersistentSession


@app.tool(tags={REQUIRES_MAPDL_TAG})
async def run_python_code(
    ctx: Context,
    code: str,
    timeout: int = 60,
) -> ToolResult:
    """Execute arbitrary Python and PyMAPDL code in the persistent Python session.

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
    ToolResult
        Execution result or error message.

    Examples
    --------
    Execute simple Python code to compute a value:
    >>> code = '''
    ... result = sum([i**2 for i in range(10)])
    ... print(f"Sum of squares: {result}")
    ... '''
    >>> run_python_code(ctx, code)

    Execute PyMAPDL code:
    >>> code = '''
    ... displacements = mapdl.get_array("NODE", item1="U", it1num="Y")
    ... print(f"Displacements: {displacements}")
    ... '''
    >>> run_python_code(ctx, code)
    """
    session = ctx.request_context.lifespan_context.python_session

    if session is None:
        return _text_result(
            json.dumps(
                {
                    "success": False,
                    "error": "No Python session available. The persistent Python session was not initialized.",  # noqa: E501
                },
                ensure_ascii=False,
            )
        )

    # Check if MAPDL is connected in the persistent session
    mapdl_instance = session.metadata.get("mapdl", None)
    if mapdl_instance is None or isinstance(mapdl_instance, str):
        mapdl_instance = connect_to_mapdl_in_persistent_python(ctx)

    if mapdl_instance is None or isinstance(mapdl_instance, str):
        try:
            mapdl_instance = connect_to_mapdl_in_persistent_python(ctx)
        except Exception as e:
            error_msg = f"Failed to connect to MAPDL in persistent Python session: {str(e)}"
            logger.error(error_msg)
            return _text_result(
                json.dumps(
                    {"success": False, "error": error_msg},
                    ensure_ascii=False,
                    indent=2,
                )
            )

    result: str = await execute_python_code(
        ctx=ctx,
        code=code,
        timeout=timeout,
    )
    return _text_result(result)


@app.tool(tags={"aali", REQUIRES_MAPDL_TAG})
def custom_plot(
    ctx: Context,
    plot_code: str,
    plot_type: str = "matplotlib",
    timeout: int = 60,
) -> ToolResult:
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
    - save_matplotlib_plot(filename, dpi)
    - save_plot(plotter, filename)

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
    timeout : int, optional
        Maximum time in seconds for plot generation. Default is 60 seconds.

    Returns
    -------
    ToolResult
        A result containing:
        - TextContent with the plot creation status message
        - ImageContent with the base64-encoded image data if successful

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
    ... result = save_matplotlib_plot(dpi=150)
    ... print(result)
    ... '''
    >>> custom_plot(ctx, plot_code, plot_type="matplotlib")
    """
    session = ctx.request_context.lifespan_context.python_session

    if session is None:
        return _text_result(
            "No Python session available. The persistent Python session was not initialized."
        )

    # Check if MAPDL is connected in the persistent session
    mapdl_instance = session.metadata.get("mapdl", None)
    if mapdl_instance is None or isinstance(mapdl_instance, str):
        mapdl_instance = connect_to_mapdl_in_persistent_python(ctx)

    if mapdl_instance is None or isinstance(mapdl_instance, str):
        if isinstance(mapdl_instance, str):
            error_msg = mapdl_instance
        else:
            error_msg = "An error occurred while connecting to MAPDL in the persistent Python session. Please, restart the session and try again."  # noqa: E501
        return _text_result(f"Failed to connect to MAPDL in persistent Python session: {error_msg}")

    result: list[TextContent | ImageContent] | str = create_custom_plot(
        ctx=ctx,
        plot_code=plot_code,
        plot_type=plot_type,
        timeout=timeout,
    )
    if isinstance(result, str):
        return _text_result(result)
    return ToolResult(result)
