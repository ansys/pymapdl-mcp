from typing import TYPE_CHECKING, Any

from ansys.common.mcp.helpers import logger
from fastmcp.server import Context

if TYPE_CHECKING:
    from ansys.mapdl.core import Mapdl  # pyright: ignore[reportMissingTypeStubs]


def list_instances(
    instances: bool = False, long: bool = False, cmd: bool = False, location: bool = False
) -> str:
    """
    List running MAPDL instances on the system.

    This function scans all running processes to identify ANSYS MAPDL instances
    that are using gRPC communication. It returns a formatted table with information
    about each discovered instance.

    Parameters
    ----------
    instances : bool, optional
        If True, only show main MAPDL instances (exclude child processes).
        If False, show all MAPDL-related processes. Default is False.
    long : bool, optional
        If True, enable verbose output including command line and working directory.
        This automatically sets both `cmd` and `location` to True. Default is False.
    cmd : bool, optional
        If True, include the command line arguments in the output table.
        Default is False.
    location : bool, optional
        If True, include the working directory path in the output table.
        Default is False.

    Returns
    -------
    str
        A formatted table string containing information about MAPDL instances.
        The table includes columns for process name, status, gRPC port, PID,
        and optionally command line and working directory based on the parameters.

    Notes
    -----
    - This function identifies MAPDL processes by looking for "ansys" or "mapdl"
      in the process name and the presence of "-grpc" flag in command line arguments.
    - Only processes with status RUNNING, IDLE, or SLEEPING are considered valid.
    - Main instances are distinguished from child processes by counting their children.
    - Processes that no longer exist or are zombies are silently skipped.

    Examples
    --------
    >>> # List all MAPDL processes
    >>> print(list_instances())

    >>> # List only main instances with full details
    >>> print(list_instances(instances=True, long=True))

    >>> # List with command line information
    >>> print(list_instances(cmd=True))
    """
    import psutil
    from tabulate import tabulate

    # this copied from PyMAPDL, but it will be refactored there later
    # Assuming all ansys processes have -grpc flag
    mapdl_instances = []

    def is_grpc_based(proc):
        cmdline = proc.cmdline()
        return "-grpc" in cmdline

    def get_port(proc):
        cmdline = proc.cmdline()
        if "-port" in cmdline:
            ind_grpc = cmdline.index("-port")
            return cmdline[ind_grpc + 1]
        else:
            return "N/A"

    def is_valid_process(proc):
        valid_status = proc.status() in [
            psutil.STATUS_RUNNING,
            psutil.STATUS_IDLE,
            psutil.STATUS_SLEEPING,
        ]
        valid_ansys_process = ("ansys" in proc.name().lower()) or ("mapdl" in proc.name().lower())
        return valid_status and valid_ansys_process and is_grpc_based(proc)

    for proc in psutil.process_iter():
        # Check if the process is running and not suspended
        try:
            if is_valid_process(proc):
                # Checking the number of children we infer if the process is the main process,
                # or one of the main process thread.
                if len(proc.children(recursive=True)) < 2:
                    proc.ansys_instance = False
                else:
                    proc.ansys_instance = True
                mapdl_instances.append(proc)

        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

    # printing
    if long:
        cmd = True
        location = True

    if instances:
        headers = ["Name", "Status", "gRPC port", "PID"]
    else:
        headers = ["Name", "Is Instance", "Status", "gRPC port", "PID"]

    if cmd:
        headers.append("Command line")
    if location:
        headers.append("Working directory")

    table = []
    for each_p in mapdl_instances:
        if instances and not each_p.ansys_instance:
            # Skip child processes if only printing instances
            continue

        proc_line = []
        proc_line.append(each_p.name())

        if not instances:
            proc_line.append(each_p.ansys_instance)

        proc_line.extend([each_p.status(), get_port(each_p), each_p.pid])

        if cmd:
            proc_line.append(" ".join(each_p.cmdline()))

        if location:
            try:
                proc_line.append(each_p.cwd())
            except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
                proc_line.append("N/A")

        table.append(proc_line)

    return str(tabulate(table, headers))


def get_info(mapdl: "Mapdl") -> dict[str, str | dict[str, Any]]:
    """
    Get information from the MAPDL instance.

    Parameters
    ----------
    mapdl : Mapdl
        MAPDL instance

    Returns
    -------
    dict[str, str | dict[str, Any]]
        Dictionary containing MAPDL information
    """
    info: dict[str, str | dict[str, Any]] = {}

    # Basic connection information
    info["connection"] = {
        "name": mapdl.name,
        "ip": mapdl.ip,
        "port": mapdl.port,
        "version": mapdl.version,
        "directory": str(mapdl.directory),
        "status": mapdl.check_status.title(),
        "is_local": mapdl.is_local,
        "jobname": mapdl.jobname,
        "platform": mapdl.platform,
    }

    # Information class attributes
    info_class: dict[str, str] = {}
    try:
        info_class["title"] = mapdl.information.title if hasattr(mapdl.information, "title") else ""
        info_class["jobname"] = (
            mapdl.information.jobname if hasattr(mapdl.information, "jobname") else ""
        )
        info_class["routine"] = (
            mapdl.information.routine if hasattr(mapdl.information, "routine") else ""
        )
        info_class["units"] = mapdl.information.units if hasattr(mapdl.information, "units") else ""
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
    geometry_info: dict[str, int | str] = {}
    try:
        # Try to get number of keypoints, lines, areas, volumes
        geometry_info["n_keypoint"] = (
            mapdl.geometry.n_keypoint if hasattr(mapdl.geometry, "n_keypoint") else 0
        )
        geometry_info["n_line"] = mapdl.geometry.n_line if hasattr(mapdl.geometry, "n_line") else 0
        geometry_info["n_area"] = mapdl.geometry.n_area if hasattr(mapdl.geometry, "n_area") else 0
        geometry_info["n_volu"] = mapdl.geometry.n_volu if hasattr(mapdl.geometry, "n_volu") else 0
    except Exception as e:
        logger.warning(f"Error extracting geometry data: {e}")
        geometry_info["error"] = str(e)
    info["geometry"] = geometry_info

    # Post_processing class attributes
    post_info: dict[str, str | int | bool] = {}
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
    mesh_info: dict[str, int | str] = {}
    try:
        mesh_info["n_node"] = mapdl.mesh.n_node if hasattr(mapdl.mesh, "n_node") else 0
        mesh_info["n_elem"] = mapdl.mesh.n_elem if hasattr(mapdl.mesh, "n_elem") else 0
    except Exception as e:
        logger.warning(f"Error extracting mesh data: {e}")
        mesh_info["error"] = str(e)
    info["mesh"] = mesh_info

    return info


def connect_to_mapdl_in_persistent_python(
    ctx: Context,
) -> Any:
    """Connect to the MAPDL instance in the persistent Python session.

    This tool connects to the MAPDL instance from within the persistent Python session.
    It assumes that the persistent session has already been created.


    Parameters
    ----------
    ctx : Context
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Connection status message.
    """
    session = ctx.request_context.lifespan_context.python_session

    if session is None:
        return "No Python session available. The persistent Python session was not initialized."

    try:
        # Check if already connected
        if session.metadata.get("mapdl", None) is not None:
            mapdl = session.metadata["mapdl"]
            return (
                f"Already connected to persistent PyMAPDL session with MAPDL at "
                f"{mapdl._ip}:{mapdl._port}."
            )

        # First, check if MAPDL is available in lifespan context
        mapdl_instance = ctx.request_context.lifespan_context.mapdl
        if mapdl_instance is None:
            return (
                "No MAPDL instance available in lifespan context. "
                "Please launch or connect to MAPDL first using launch_mapdl"
                "or connect_to_mapdl tool."
            )

        connection_code = f"""
# Connect to the persistent MAPDL instance
from ansys.mapdl.core import Mapdl  # pyright: ignore[reportMissingTypeStubs]

mapdl = Mapdl(
    start_instance=False,
    ip='{mapdl_instance.ip}',
    port={mapdl_instance.port},
    cleanup_on_exit=False,
)
        """
        session.execute(connection_code)

        # Store in persistent session
        session.metadata["mapdl"] = mapdl_instance

        logger.info(
            "Connected to persistent PyMAPDL session successfully at"
            f" {mapdl_instance.ip}:{mapdl_instance.port}!"
        )

    except Exception as e:
        error_msg = f"Failed to connect to MAPDL in the persistent PyMAPDL session: {str(e)}"
        logger.error(error_msg)

    return session.metadata.get("mapdl", None)
