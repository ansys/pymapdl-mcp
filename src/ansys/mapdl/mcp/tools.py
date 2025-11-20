"""List of tools in PyMAPDL-MCP."""

import base64
import json
import logging
import os
import tempfile
from pathlib import Path

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from mcp.types import ImageContent, TextContent

from ansys.mapdl.mcp.mcp import AppContext, mcp

logger = logging.getLogger(__name__)


# Access type-safe lifespan context in tools
@mcp.tool()
def check_mapdl_status(ctx: Context[ServerSession, AppContext]) -> str:
    """Check the status of MAPDL initialization.

    This tool executes the /STATUS command in MAPDL and extracts comprehensive
    information from PyMAPDL's Information, Geometry, and Post_processing classes.
    It also checks whether the MAPDL instance has exited or is exiting.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
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
        # Check if MAPDL has exited
        if hasattr(mapdl, "_exited") and mapdl._exited:
            return "MAPDL instance has exited. Please reconnect or launch a new instance."

        if hasattr(mapdl, "_exiting") and mapdl._exiting:
            return "MAPDL instance is currently exiting. Please wait or launch a new instance."

        # Execute /STATUS command to verify connection
        mapdl.run("/STATUS")  # type: ignore[union-attr]

        info: dict = {}

        # Basic connection information
        info["connection"] = {
            "version": mapdl.version,
            "is_alive": mapdl.is_alive,
            "working_directory": mapdl.directory,
            "port": mapdl.port,
            "ip": mapdl.ip,
        }

        # Information class attributes
        info_class: dict = {}
        try:
            info_class["title"] = (
                mapdl.information.title if hasattr(mapdl.information, "title") else ""
            )
            info_class["jobname"] = (
                mapdl.information.jobname if hasattr(mapdl.information, "jobname") else ""
            )
            info_class["routine"] = (
                mapdl.information.routine if hasattr(mapdl.information, "routine") else ""
            )
            info_class["units"] = (
                mapdl.information.units if hasattr(mapdl.information, "units") else ""
            )
            info_class["revision"] = (
                mapdl.information.revision if hasattr(mapdl.information, "revision") else ""
            )
            info_class["product"] = (
                mapdl.information.product if hasattr(mapdl.information, "product") else ""
            )
        except Exception as e:
            logger.warning(f"Error extracting information class data: {e}")
            info_class["error"] = str(e)
        info["information"] = info_class

        # Geometry class attributes
        geometry_info: dict = {}
        try:
            # Try to get number of keypoints, lines, areas, volumes
            geometry_info["n_keypoint"] = (
                mapdl.geometry.n_keypoint if hasattr(mapdl.geometry, "n_keypoint") else 0
            )
            geometry_info["n_line"] = (
                mapdl.geometry.n_line if hasattr(mapdl.geometry, "n_line") else 0
            )
            geometry_info["n_area"] = (
                mapdl.geometry.n_area if hasattr(mapdl.geometry, "n_area") else 0
            )
            geometry_info["n_volu"] = (
                mapdl.geometry.n_volu if hasattr(mapdl.geometry, "n_volu") else 0
            )
        except Exception as e:
            logger.warning(f"Error extracting geometry data: {e}")
            geometry_info["error"] = str(e)
        info["geometry"] = geometry_info

        # Post_processing class attributes
        post_info: dict = {}
        try:
            # Try to get common post-processing information
            if hasattr(mapdl, "post_processing"):
                post_info["available"] = True
                # Check for number of result sets
                if hasattr(mapdl.post_processing, "nsets"):
                    post_info["nsets"] = mapdl.post_processing.nsets
            else:
                post_info["available"] = False
        except Exception as e:
            logger.warning(f"Error extracting post_processing data: {e}")
            post_info["error"] = str(e)
        info["post_processing"] = post_info

        # Mesh information
        mesh_info: dict = {}
        try:
            mesh_info["n_node"] = mapdl.mesh.n_node if hasattr(mapdl.mesh, "n_node") else 0
            mesh_info["n_elem"] = mapdl.mesh.n_elem if hasattr(mapdl.mesh, "n_elem") else 0
        except Exception as e:
            logger.warning(f"Error extracting mesh data: {e}")
            mesh_info["error"] = str(e)
        info["mesh"] = mesh_info

        # Return as formatted JSON
        return json.dumps(info, indent=2)

    except Exception as e:
        error_msg = f"Error checking MAPDL status: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def check_mapdl_installed() -> str:
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
        from ansys.mapdl.core.launcher import check_valid_ansys, get_default_ansys_path

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


@mcp.tool()
def write_comment(ctx: Context[ServerSession, AppContext], comment: str) -> str:
    """Write a comment in the MAPDL session.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
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


@mcp.tool()
def run_mapdl_command(ctx: Context[ServerSession, AppContext], cmd: str) -> str:
    """Execute an arbitrary MAPDL command.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
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


@mcp.tool()
def run_multiple_commands(ctx: Context[ServerSession, AppContext], commands: list[str]) -> str:
    """Execute multiple MAPDL commands in sequence using input_strings.

    This tool is optimized for running multiple commands efficiently by using
    MAPDL's input_strings method, which processes commands in batch mode.
    This is significantly faster than executing commands one by one.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
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

    if not isinstance(commands, list):
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


@mcp.tool()
def launch_mapdl(
    ctx: Context[ServerSession, AppContext],
    exec_file: str | None = None,
    run_location: str | None = None,
    nproc: int = 2,
    additional_switches: str = "",
) -> str:
    """Launch a new MAPDL instance.

    This tool starts a new MAPDL instance using PyMAPDL's launch_mapdl function.
    The launched instance will be automatically connected and stored in the context
    for subsequent operations. The instance can be closed using the disconnect_from_mapdl tool.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    exec_file : str, optional
        The path to the MAPDL executable. If None, PyMAPDL will attempt to find
        the MAPDL executable automatically.
    run_location : str, optional
        The directory where MAPDL will run and store files. If None, a temporary
        directory will be created.
    nproc : int, optional
        Number of processors to use. Default is 2.
    additional_switches : str, optional
        Additional command line switches to pass to MAPDL. Default is empty string.

    Returns
    -------
    str
        Launch status message with MAPDL version and connection information.
    """
    from ansys.mapdl.core import launch_mapdl

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
        kwargs = {
            "nproc": nproc,
            "loglevel": "INFO",
        }

        if exec_file is not None:
            kwargs["exec_file"] = exec_file

        if run_location is not None:
            kwargs["run_location"] = run_location

        if additional_switches:
            kwargs["additional_switches"] = additional_switches

        mapdl = launch_mapdl(**kwargs)

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


@mcp.tool()
def connect_to_mapdl(
    ctx: Context[ServerSession, AppContext], port: int = 50052, ip: str = "localhost"
) -> str:
    """Connect to an existing MAPDL instance.

    This tool establishes a connection to a running MAPDL instance using the
    provided port and IP address. The connection is stored for subsequent
    operations and can be closed using the disconnect_from_mapdl tool.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
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
    from ansys.mapdl.core import Mapdl

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
        mapdl = Mapdl(
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


@mcp.tool()
def disconnect_from_mapdl(ctx: Context[ServerSession, AppContext]) -> str:
    """Disconnect from the dynamically connected MAPDL instance.

    This tool closes the connection to the MAPDL instance that was established
    using the connect_to_mapdl tool and releases the associated resources.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
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


@mcp.tool()
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
    return list_instances(long=True)


@mcp.tool()
def screenshot(
    ctx: Context[ServerSession, AppContext],
) -> list[TextContent | ImageContent]:
    """Capture a screenshot of the current MAPDL graphics window.

    This tool captures the current state of the MAPDL graphics window and returns
    both the file path and the image data encoded in base64 format for display
    in the MCP client.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
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
        if (
            "temp_path" in locals() and Path(temp_path).exists()
        ):  # pyright: ignore[reportPossiblyUnboundVariable]
            Path(temp_path).unlink()  # pyright: ignore[reportPossiblyUnboundVariable]

        error_msg = f"Failed to capture screenshot: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
