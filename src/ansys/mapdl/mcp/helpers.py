import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def exception_wrapper(func: Callable[[], Any]) -> Any | str:
    """Wrap to catch exceptions and return error messages."""
    try:
        return func()
    except ImportError as e:
        error_msg = f"Error when running {str(func)}: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error listing MAPDL instances: {e}"
        logger.error(error_msg)
        return error_msg


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
