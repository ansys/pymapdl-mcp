import logging
from typing import TYPE_CHECKING, Any

from fastmcp.server import Context

if TYPE_CHECKING:
    from ansys.mapdl.core import Mapdl  # pyright: ignore[reportMissingTypeStubs]

logger = logging.getLogger(__name__)


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


def create_pool(
    ctx: "Context",
    n_instances: int = 1,
    exec_file: str | None = None,
    run_location: str | None = None,
    jobname: str = "file",
    nproc: int = 2,
    ram: int | None = None,
    override: bool = False,
    additional_switches: str = "",
    clear_on_connect: bool = True,
    remove_temp_dir_on_exit: bool = False,
    start_timeout: int = 45,
    ip: str | list[str] | None = None,
    port: int | list[int] | None = None,
    start_instance: bool = True,
    cleanup_on_exit: bool = True,
    nicknames: list[str] | None = None,
    loglevel: str = "INFO",
) -> str:
    """Create a MapdlPool and store it in context.

    This internal method handles pool creation for both launch_mapdl and
    connect_to_mapdl tools, reducing code duplication.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    n_instances : int
        Number of MAPDL instances in the pool.
    exec_file : str, optional
        The path to the MAPDL executable.
    run_location : str, optional
        The directory where MAPDL will run.
    jobname : str
        The jobname for MAPDL instances.
    nproc : int
        Number of processors to use.
    ram : int, optional
        Amount of RAM to allocate.
    override : bool
        Whether to override existing files.
    additional_switches : str
        Additional command line switches.
    clear_on_connect : bool
        Whether to clear on connect.
    remove_temp_dir_on_exit : bool
        Whether to remove temp directory on exit.
    start_timeout : int
        Timeout for starting instances.
    ip : str | list[str], optional
        IP address(es) for remote connections.
    port : int | list[int], optional
        Port(s) for remote connections.
    start_instance : bool
        Whether to start new instances (True) or connect to existing (False).
    cleanup_on_exit : bool
        Whether to cleanup on exit.
    nicknames : list[str], optional
        List of nicknames for instances.
    loglevel: str
        Logging level for MAPDL instances.

    Returns
    -------
    str
        Success message with pool information.
    """
    from ansys.mapdl.core import MapdlPool  # pyright: ignore[reportMissingTypeStubs]

    logger.info(f"Creating MAPDL pool with {n_instances} instance(s)...")

    # Check if pool already exists
    if hasattr(ctx, "pool") and ctx.pool is not None:
        n_existing = len(ctx.pool)
        return (
            f"MAPDL pool already exists with {n_existing} instance(s). "
            f"Use disconnect_from_mapdl to clear the pool before launching new instances."
        )

    # Validate nicknames
    if nicknames is not None:
        if len(nicknames) != n_instances:
            return (
                f"Error: Number of nicknames ({len(nicknames)}) "
                f"must match n_instances ({n_instances})"
            )

        # Check for duplicate nicknames
        if len(nicknames) != len(set(nicknames)):
            return "Error: Duplicate nicknames are not allowed"

    try:
        # Create the pool - MapdlPool handles validation and defaults
        from ansys.mapdl.core.launcher import LOCALHOST, MAPDL_DEFAULT_PORT

        if port is None:
            port = MAPDL_DEFAULT_PORT

        if ip is None:
            ip = LOCALHOST

        list_ips = ip if isinstance(ip, list) else [ip]
        list_ports = port if isinstance(port, list) else [port]

        pool = MapdlPool(
            n_instances=n_instances,
            exec_file=exec_file,
            run_location=run_location,
            jobname=jobname,
            nproc=nproc,
            ram=ram,
            override=override,
            additional_switches=additional_switches,
            start_instance=start_instance,
            clear_on_connect=clear_on_connect,
            remove_temp_dir_on_exit=remove_temp_dir_on_exit,
            start_timeout=start_timeout,
            ip=list_ips,
            port=list_ports,
            cleanup_on_exit=cleanup_on_exit,
            restart_failed=True,  # Enable auto-restart for failed instances
            loglevel=loglevel,
        )

        # Store pool in context
        ctx.pool = pool

        # Set up nicknames if provided
        if nicknames is not None:
            for idx, nickname in enumerate(nicknames):
                ctx.instance_nicknames[nickname] = idx

        # Build success message
        lines = [
            f"Successfully launched {n_instances} MAPDL instance(s)",
            f"Pool size: {len(pool)}",
        ]

        # Show first instance details
        if len(pool) > 0:
            first_instance = pool[0]
            nickname_str = f' (nickname: "{nicknames[0]}")' if nicknames else ""
            lines.append(f"  Instance 0{nickname_str}: {first_instance.ip}:{first_instance.port}")

        logger.info(f"MAPDL pool created successfully with {len(pool)} instance(s)")
        return "\n".join(lines)

    except Exception as e:
        error_msg = f"Failed to create MAPDL pool: {str(e)}"
        logger.error(error_msg)
        return error_msg


def exit_instance(
    ctx: "Context",
    instance: str | int | None = None,
) -> str:
    """Exit a specific MAPDL instance or the entire pool.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int | None
        Instance identifier (index or nickname). If None, exits entire pool.

    Returns
    -------
    str
        Success or error message.
    """
    pool = ctx.pool

    if pool is None:
        return "No MAPDL pool available. Nothing to disconnect."

    try:
        # Exit entire pool if no instance specified
        if instance is None:
            logger.info("Exiting entire MAPDL pool...")
            pool.exit()
            ctx.pool = None
            ctx.instance_nicknames.clear()
            ctx.default_instance_index = 0
            logger.info("Successfully disconnected from entire MAPDL pool")
            return "Successfully disconnected from entire MAPDL pool"

        # Exit specific instance
        idx = resolve_instance_index(ctx, instance)
        if idx is None:
            available = list_available_instances(ctx)
            return f"Instance '{instance}' not found. Available instances:\n{available}"

        # Get instance info before exiting
        try:
            mapdl_instance = pool[idx]
            ip = mapdl_instance.ip
            port = mapdl_instance.port
        except (IndexError, AttributeError):
            ip = "unknown"
            port = "unknown"

        # Exit the specific instance
        if hasattr(pool, "_instances") and idx < len(pool._instances):
            if pool._instances[idx] is not None:
                pool._instances[idx].exit()
                pool._instances[idx] = None

        # Remove nickname if exists
        nickname_to_remove = find_nickname(ctx, idx)
        if nickname_to_remove:
            del ctx.instance_nicknames[nickname_to_remove]

        # Check if pool is now empty
        remaining = sum(1 for inst in pool._instances if inst is not None)
        if remaining == 0:
            logger.info("Pool is now empty, clearing pool object")
            ctx.pool = None
            ctx.instance_nicknames.clear()
            ctx.default_instance_index = 0
            return (
                f"Successfully disconnected instance {idx} at {ip}:{port}. "
                f"Pool cleared (last instance)."
            )

        logger.info(f"Successfully disconnected instance {idx}")
        return f"Successfully disconnected instance {idx} at {ip}:{port}"

    except Exception as e:
        error_msg = f"Error during disconnect: {str(e)}"
        logger.error(error_msg)
        return error_msg


def resolve_instance_index(
    ctx: "Context",
    instance: str | int | None = None,
) -> int | None:
    """Resolve instance identifier to pool index.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int | None
        Instance identifier (index, nickname, or None for default).

    Returns
    -------
    int | None
        Pool index if found, None otherwise.
    """
    pool = ctx.pool

    if pool is None:
        return None

    # None means use default
    if instance is None:
        default_idx: int = ctx.default_instance_index
        return default_idx

    # Integer means direct index
    if isinstance(instance, int):
        if 0 <= instance < len(pool._instances):
            return instance
        return None

    # String means nickname lookup
    if isinstance(instance, str):
        idx_result: int | None = ctx.instance_nicknames.get(instance)
        return idx_result

    return None


def get_mapdl_instance(
    ctx: "Context",
    instance: str | int | None = None,
) -> tuple[Any | None, str]:
    """Get MAPDL instance from pool.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int | None
        Instance identifier (index, nickname, or None for default).

    Returns
    -------
    tuple[Any | None, str]
        Tuple of (MAPDL instance or None, description string).
        Description is for error messages and logging.
    """
    pool = ctx.pool

    if pool is None:
        return (
            None,
            "No MAPDL pool available. Use launch_mapdl or connect_to_mapdl to initialize.",
        )

    # Resolve index
    idx = resolve_instance_index(ctx, instance)

    if idx is None:
        available = list_available_instances(ctx)
        return None, f"Instance '{instance}' not found. Available instances:\n{available}"

    # Get instance from pool
    try:
        mapdl_instance = pool[idx]

        # Check if instance has exited
        if mapdl_instance.exited:
            return None, f"Instance {idx} has exited. Please reconnect or launch a new instance."

        if mapdl_instance.exiting:
            return (
                None,
                f"Instance {idx} is currently exiting. Please wait or launch a new instance.",
            )

        # Build description
        nickname = find_nickname(ctx, idx)
        nickname_str = f' ("{nickname}")' if nickname else ""
        desc = f"instance {idx}{nickname_str}"

        return mapdl_instance, desc

    except (IndexError, KeyError):
        return (
            None,
            (
                f"Instance {idx} is not available (disconnected). "
                f"Use list_pool_instances to see status."
            ),
        )


def list_available_instances(ctx: "Context") -> str:
    """List all available instances in the pool.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Formatted list of available instances.
    """
    pool = ctx.pool

    if pool is None:
        return "No pool"

    lines = []
    for idx in range(len(pool._instances)):
        if pool._instances[idx] is not None:
            nickname = find_nickname(ctx, idx)
            nickname_str = f' ("{nickname}")' if nickname else ""
            try:
                status = "active" if not pool._instances[idx].exited else "exited"
            except AttributeError:
                status = "active"
            lines.append(f"  {idx}{nickname_str}: {status}")

    return "\n".join(lines) if lines else "No instances"


def find_nickname(ctx: "Context", index: int) -> str | None:
    """Find nickname for given index.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    index : int
        Pool index.

    Returns
    -------
    str | None
        Nickname if found, None otherwise.
    """
    for nickname, idx in ctx.instance_nicknames.items():
        if idx == index:
            nickname_result: str = nickname
            return nickname_result
    return None
