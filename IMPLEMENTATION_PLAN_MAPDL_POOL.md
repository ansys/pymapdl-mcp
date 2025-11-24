# Implementation Plan: Multiple MAPDL Instances Support using MapdlPool

**Date:** November 24, 2025
**Project:** pymapdl-mcp
**Objective:** Transform the MCP server to manage multiple MAPDL instances using PyMAPDL's `MapdlPool` class

---

## Table of Contents

1. [Overview](#overview)
2. [Core Architecture Changes](#core-architecture-changes)
3. [Connection & Launch Tools Modifications](#connection--launch-tools-modifications)
4. [Instance Selection Mechanism](#instance-selection-mechanism)
5. [Update All Existing Tools](#update-all-existing-tools)
6. [New Tools to Add](#new-tools-to-add)
7. [Implementation Phases](#implementation-phases)
8. [Backward Compatibility Strategy](#backward-compatibility-strategy)
9. [Key Design Decisions](#key-design-decisions)
10. [Error Handling](#error-handling)
11. [Example Usage Scenarios](#example-usage-scenarios)
12. [Files to Modify](#files-to-modify)
13. [Technical Details](#technical-details)

---

## Overview

Transform the pymapdl-mcp server from managing a single MAPDL instance to managing multiple instances through PyMAPDL's `MapdlPool` class. The pool will be **transparent to users** while enabling instance-specific operations through optional naming/indexing.

### Key Requirements

- Use `MapdlPool` object from PyMAPDL library
- Create pool on first connection/launch
- Manage pool through user interaction
- Exit pool at the end of session
- Default to first instance unless name/index specified
- Allow instance access by numbering or nickname
- Pass instance identifier to all MCP tools
- Keep pool object hidden from user awareness

### MapdlPool Reference

Source: https://github.com/ansys/pymapdl/blob/main/src/ansys/mapdl/core/pool.py

---

## Core Architecture Changes

### 1.1 Update Application Context (`src/ansys/mapdl/mcp/mcp.py`)

**Current State:**
```python
@dataclass
class AppContext:
    """Application context with typed dependencies.

    Attributes
    ----------
    mapdl : Optional[Any]
        MAPDL instance connection. Using Any to avoid type issues with MAPDL variants.
    """
    mapdl: Optional[Any] = None
```

**New Structure:**
```python
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class AppContext:
    """Application context with typed dependencies.

    Attributes
    ----------
    pool : Optional[Any]
        MapdlPool instance managing multiple MAPDL connections.
        Using Any to avoid type issues with MapdlPool.
    instance_nicknames : Dict[str, int]
        Mapping of user-defined nicknames to pool indices.
    default_instance_index : int
        Index of the default instance to use when none specified.
    """
    pool: Optional[Any] = None  # MapdlPool instance
    instance_nicknames: Dict[str, int] = field(default_factory=dict)
    default_instance_index: int = 0

    @property
    def mapdl(self) -> Optional[Any]:
        """Returns the default MAPDL instance for backward compatibility.

        Returns
        -------
        Optional[Any]
            The default MAPDL instance from the pool, or None if pool not initialized.
        """
        if self.pool is not None and len(self.pool) > 0:
            try:
                return self.pool[self.default_instance_index]
            except (IndexError, TypeError):
                return None
        return None
```

### 1.2 Update Lifespan Management (`src/ansys/mapdl/mcp/mcp.py`)

**Current Implementation:**
```python
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    context = AppContext()
    try:
        logger.info("MCP Server initialized. Use connect_to_mapdl to establish a connection.")
        yield context

    finally:
        # Cleanup on shutdown
        if context.mapdl is not None:
            try:
                logger.info("Disconnecting from MAPDL...")
                context.mapdl.exit()
                logger.info("MAPDL disconnect complete")
            except Exception as e:
                logger.error(f"Error during MAPDL disconnect: {e}")
```

**Updated Implementation:**
```python
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context.

    Parameters
    ----------
    server : FastMCP
        The FastMCP server instance.

    Yields
    ------
    AppContext
        Application context for storing MapdlPool and instance management.
    """
    context = AppContext()
    try:
        logger.info("MCP Server initialized. Use connect_to_mapdl or launch_mapdl to establish connections.")
        yield context

    finally:
        # Cleanup on shutdown - exit entire pool
        if context.pool is not None:
            try:
                logger.info("Shutting down MAPDL pool...")
                context.pool.exit(block=True)
                logger.info("MAPDL pool shutdown complete")
            except Exception as e:
                logger.error(f"Error during MAPDL pool shutdown: {e}")

        # Clear nicknames
        context.instance_nicknames.clear()
```

---

## Connection & Launch Tools Modifications

### 2.0 Add Internal Helper Methods (`src/ansys/mapdl/mcp/helpers.py`)

**New Internal Methods:**

These methods encapsulate pool creation and instance exit logic to reduce code duplication:

```python
def create_pool(
    ctx: Context[ServerSession, AppContext],
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
        Path to MAPDL executable.
    run_location : str, optional
        Working directory for MAPDL.
    jobname : str
        MAPDL jobname.
    nproc : int
        Number of processors per instance.
    ram : int, optional
        Total size in megabytes of the workspace (memory).
    override : bool
        Attempts to delete the lock file at the run_location.
    additional_switches : str
        Additional command line switches.
    clear_on_connect : bool
        Clear MAPDL on connection.
    remove_temp_dir_on_exit : bool
        Delete temporary directory on exit.
    start_timeout : int
        Maximum allowable time to connect to the MAPDL server.
    ip : str | list[str], optional
        IP address(es) for connecting to existing instances.
    port : int | list[int], optional
        Port(s) for connecting to existing instances.
    start_instance : bool
        Whether to launch new instances (True) or connect to existing (False).
    cleanup_on_exit : bool
        Whether to clean up on exit (True for launched, False for connected).

    Returns
    -------
    str
        Success message with pool information, or error message.
    """
    from ansys.mapdl.core import MapdlPool

    # Check if pool already exists
    if ctx.request_context.lifespan_context.pool is not None:
        action = "launch" if start_instance else "connect to"
        return (
            f"MAPDL pool already exists with {len(ctx.request_context.lifespan_context.pool)} instance(s). "
            f"Use disconnect_from_mapdl to clear the pool before {action}ing new instances."
        )

    try:
        # Build kwargs for MapdlPool
        kwargs: dict[str, Any] = {
            "n_instances": n_instances,
            "jobname": jobname,
            "nproc": nproc,
            "loglevel": "INFO",
            "start_instance": start_instance,
            "cleanup_on_exit": cleanup_on_exit,
        }

        if exec_file is not None:
            kwargs["exec_file"] = exec_file

        if run_location is not None:
            kwargs["run_location"] = run_location

        if ram is not None:
            kwargs["ram"] = ram

        if override:
            kwargs["override"] = override

        if additional_switches:
            kwargs["additional_switches"] = additional_switches

        if not clear_on_connect:
            kwargs["clear_on_connect"] = clear_on_connect

        if remove_temp_dir_on_exit:
            kwargs["remove_temp_dir_on_exit"] = remove_temp_dir_on_exit

        if start_timeout != 45:
            kwargs["start_timeout"] = start_timeout

        if ip is not None:
            kwargs["ip"] = ip

        if port is not None:
            kwargs["port"] = port

        # Create the pool
        pool = MapdlPool(**kwargs)

        # Store in context
        ctx.request_context.lifespan_context.pool = pool

        # Use pool's internal names for nicknames
        # MapdlPool has a _names callable that generates names
        for i in range(len(pool)):
            nickname = pool._names(i) if hasattr(pool, '_names') else f"Instance_{i}"
            ctx.request_context.lifespan_context.instance_nicknames[nickname] = i

        # Build response message
        action = "launched" if start_instance else "connected to"
        msg = f"Successfully {action} {n_instances} MAPDL instance(s)\n"
        msg += f"Pool size: {len(pool)}\n"

        for i in range(len(pool)):
            instance = pool[i]
            nickname = pool._names(i) if hasattr(pool, '_names') else f"Instance_{i}"
            msg += f"  Instance {i} (nickname: \"{nickname}\"): {instance.ip}:{instance.port}\n"
            msg += f"    Version: {instance.version}\n"
            if start_instance:
                msg += f"    Directory: {instance.directory}\n"

        logger.info(f"MAPDL pool {action} successfully!")
        return msg

    except Exception as e:
        action = "launch" if start_instance else "connect to"
        error_msg = f"Failed to {action} MAPDL pool: {str(e)}"
        logger.error(error_msg)
        return error_msg


def exit_instance(
    ctx: Context[ServerSession, AppContext],
    instance: str | int | None = None,
) -> str:
    """Exit a specific MAPDL instance or the entire pool.

    This internal method handles instance disconnection for the
    disconnect_from_mapdl tool. If exiting the last instance in the pool,
    it clears the pool object.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int | None
        Instance to exit (None = entire pool, int = index, str = nickname).

    Returns
    -------
    str
        Success message or error message.
    """
    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool to disconnect."

    try:
        if instance is None:
            # Disconnect entire pool
            logger.info("Disconnecting from entire MAPDL pool...")
            pool.exit(block=True)

            # Clear context
            ctx.request_context.lifespan_context.pool = None
            ctx.request_context.lifespan_context.instance_nicknames.clear()
            ctx.request_context.lifespan_context.default_instance_index = 0

            logger.info("Disconnected successfully!")
            return "Successfully disconnected from entire MAPDL pool"

        else:
            # Disconnect specific instance
            idx = resolve_instance_index(ctx, instance)
            if idx is None:
                available = list_available_instances(ctx)
                return f"Instance '{instance}' not found. Available instances:\n{available}"

            mapdl_instance = pool[idx]
            if mapdl_instance is None:
                return f"Instance {idx} is already disconnected"

            ip = mapdl_instance._ip
            port = mapdl_instance._port

            # Exit the specific instance
            mapdl_instance.exit()
            pool._instances[idx] = None

            # Remove nickname if it exists
            nickname_to_remove = None
            for nick, index in ctx.request_context.lifespan_context.instance_nicknames.items():
                if index == idx:
                    nickname_to_remove = nick
                    break

            if nickname_to_remove:
                del ctx.request_context.lifespan_context.instance_nicknames[nickname_to_remove]

            # Check if this was the last active instance
            active_instances = [inst for inst in pool._instances if inst is not None]
            if not active_instances:
                # Clear the pool if no instances remain
                logger.info("Last instance exited. Clearing pool.")
                ctx.request_context.lifespan_context.pool = None
                ctx.request_context.lifespan_context.instance_nicknames.clear()
                ctx.request_context.lifespan_context.default_instance_index = 0
                return f"Successfully disconnected instance {idx} at {ip}:{port}. Pool cleared (last instance)."

            return f"Successfully disconnected instance {idx} at {ip}:{port}"

    except Exception as e:
        error_msg = f"Error during disconnect: {str(e)}"
        logger.error(error_msg)
        return error_msg
```

### 2.1 Update `launch_mapdl` Tool (`src/ansys/mapdl/mcp/tools.py`)

**Current Behavior:**
- Launches a single instance and stores in `context.mapdl`

**New Behavior:**

Uses `create_pool()` helper method to launch instances. Defaults to 1 instance to maintain
backward compatibility, but uses MapdlPool infrastructure internally.

```python
@mcp.tool()
def launch_mapdl(
    ctx: Context[ServerSession, AppContext],
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
) -> str:
    """Launch a new MAPDL instance.

    This tool starts a new MAPDL instance using PyMAPDL's MapdlPool infrastructure.
    The launched instance will be automatically connected and stored in the context
    for subsequent operations. The instance can be closed using the disconnect_from_mapdl tool.

    By default, this launches a single instance, making it work as before for single-instance
    workflows. The implementation uses MapdlPool internally for consistency.

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
    jobname : str, optional
        MAPDL jobname. Defaults to 'file'.
    nproc : int, optional
        Number of processors to use. Default is 2.
    ram : int, optional
        Total size in megabytes of the workspace (memory) used for the initial
        allocation. To force a fixed size throughout the run, specify a negative
        number. Default is None (2 GB is used).
    override : bool, optional
        Attempts to delete the lock file at the run_location. Useful when a prior
        MAPDL session has exited prematurely and the lock file has not been deleted.
        Default is False.
    additional_switches : str, optional
        Additional command line switches to pass to MAPDL (e.g., "-p aa_r" for
        academic research license). Default is empty string.
    clear_on_connect : bool, optional
        Clear MAPDL on connection. Default is True.
    remove_temp_dir_on_exit : bool, optional
        When True, the directory created to launch MAPDL will be deleted when
        MAPDL is exited. Default is False.
    start_timeout : int, optional
        Maximum allowable time to connect to the MAPDL server in seconds.
        Default is 45 seconds.

    Returns
    -------
    str
        Launch status message with MAPDL version and connection information.
    """
    from ansys.mapdl.mcp.helpers import create_pool

    logger.info("Launching new MAPDL instance...")

    # Build kwargs for create_pool
    kwargs: dict[str, Any] = {
        "ctx": ctx,
        "n_instances": 1,
        "exec_file": exec_file,
        "run_location": run_location,
        "jobname": jobname,
        "nproc": nproc,
        "additional_switches": additional_switches,
        "start_instance": True,
        "cleanup_on_exit": True,
    }

    if ram is not None:
        kwargs["ram"] = ram
    if override:
        kwargs["override"] = override
    if not clear_on_connect:
        kwargs["clear_on_connect"] = clear_on_connect
    if remove_temp_dir_on_exit:
        kwargs["remove_temp_dir_on_exit"] = remove_temp_dir_on_exit
    if start_timeout != 45:
        kwargs["start_timeout"] = start_timeout

    return create_pool(**kwargs)
```

### 2.2 Update `connect_to_mapdl` Tool (`src/ansys/mapdl/mcp/tools.py`)

**Current Behavior:**
- Connects to single instance at given IP:port

**New Behavior:**

Uses `create_pool()` helper method to connect to existing instances. Defaults to single
instance connection to maintain backward compatibility, but uses MapdlPool infrastructure internally.

```python
@mcp.tool()
def connect_to_mapdl(
    ctx: Context[ServerSession, AppContext],
    port: int = 50052,
    ip: str = "localhost",
) -> str:
    """Connect to an existing MAPDL instance.

    This tool establishes a connection to a running MAPDL instance using the
    provided port and IP address. The connection is stored for subsequent
    operations and can be closed using the disconnect_from_mapdl tool.

    By default, this connects to a single instance, making it work as before for
    single-instance workflows. The implementation uses MapdlPool internally for consistency.

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
    from ansys.mapdl.mcp.helpers import create_pool

    logger.info(f"Connecting to MAPDL instance at {ip}:{port}...")

    return create_pool(
        ctx=ctx,
        n_instances=1,
        ip=ip,
        port=port,
        start_instance=False,
        cleanup_on_exit=False,
    )
```

### 2.3 Update `disconnect_from_mapdl` Tool (`src/ansys/mapdl/mcp/tools.py`)

**New Behavior:**

Uses `exit_instance()` helper method to handle disconnection. Supports disconnecting
the entire pool (default) or a specific instance. Clears the pool when the last instance exits.

```python
@mcp.tool()
def disconnect_from_mapdl(ctx: Context[ServerSession, AppContext]) -> str:
    """Disconnect from the default MAPDL instance.

    This tool closes the connection to the default MAPDL instance and releases
    the associated resources. The default instance is determined by the
    default_instance_index in the application context.

    If this is the last remaining instance in the pool, the pool will be
    automatically cleared.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Disconnection status message.
    """
    from ansys.mapdl.mcp.helpers import exit_instance

    # Exit the default instance (uses default_instance_index from context)
    default_idx = ctx.request_context.lifespan_context.default_instance_index
    return exit_instance(ctx, instance=default_idx)
```

---

## Instance Selection Mechanism

### 3.1 Add Helper Functions (`src/ansys/mapdl/mcp/helpers.py`)

**Note:** The `create_pool()` and `exit_instance()` methods are defined in section 2.0 above.

```python
def resolve_instance_index(
    ctx: Context[ServerSession, AppContext],
    instance: str | int | None = None
) -> int | None:
    """Resolve instance identifier to pool index.

    Parameters
    ----------
    ctx : Context
        MCP context containing pool and nicknames.
    instance : str | int | None
        Instance identifier:
        - None: Returns default instance index
        - int: Returns the integer if valid
        - str: Looks up nickname in instance_nicknames

    Returns
    -------
    int | None
        Pool index, or None if instance not found.
    """
    lifespan_ctx = ctx.request_context.lifespan_context
    pool = lifespan_ctx.pool

    if pool is None:
        return None

    # If None, return default
    if instance is None:
        return lifespan_ctx.default_instance_index

    # If int, validate and return
    if isinstance(instance, int):
        if 0 <= instance < len(pool._instances):
            return instance
        return None

    # If str, look up nickname
    if isinstance(instance, str):
        return lifespan_ctx.instance_nicknames.get(instance)

    return None


def get_mapdl_instance(
    ctx: Context[ServerSession, AppContext],
    instance: str | int | None = None
) -> tuple[Any | None, str]:
    """Get MAPDL instance from pool.

    Parameters
    ----------
    ctx : Context
        MCP context containing pool.
    instance : str | int | None
        Instance identifier (nickname, index, or None for default).

    Returns
    -------
    tuple[Any | None, str]
        (mapdl_instance, identifier_description)
        Returns (None, error_message) if instance not found.

    Examples
    --------
    >>> mapdl, desc = get_mapdl_instance(ctx, "solver1")
    >>> if mapdl is None:
    ...     return desc  # Error message
    >>> # Use mapdl instance
    """
    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return None, "No MAPDL pool available. Use launch_mapdl or connect_to_mapdl first."

    idx = resolve_instance_index(ctx, instance)

    if idx is None:
        available = list_available_instances(ctx)
        return None, f"Instance '{instance}' not found. Available instances:\n{available}"

    mapdl_instance = pool[idx]

    if mapdl_instance is None:
        return None, f"Instance {idx} is not available (disconnected or failed)"

    # Check if instance has exited
    if hasattr(mapdl_instance, "_exited") and mapdl_instance._exited:
        return None, f"Instance {idx} has exited. Please reconnect or launch a new instance."

    if hasattr(mapdl_instance, "_exiting") and mapdl_instance._exiting:
        return None, f"Instance {idx} is currently exiting. Please wait or launch a new instance."

    # Build description
    nickname = find_nickname(ctx, idx)
    desc = f"instance {idx}"
    if nickname:
        desc += f' ("{nickname}")'

    return mapdl_instance, desc


def list_available_instances(ctx: Context[ServerSession, AppContext]) -> str:
    """List all available instances in the pool.

    Parameters
    ----------
    ctx : Context
        MCP context containing pool.

    Returns
    -------
    str
        Formatted list of available instances.
    """
    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No pool initialized"

    lines = []
    for i, instance in enumerate(pool._instances):
        if instance is None:
            status = "disconnected"
        elif hasattr(instance, "_exited") and instance._exited:
            status = "exited"
        else:
            status = "active"

        nickname = find_nickname(ctx, i)
        nickname_str = f' ("{nickname}")' if nickname else ""

        lines.append(f"  {i}{nickname_str}: {status}")

    return "\n".join(lines) if lines else "No instances"


def find_nickname(ctx: Context[ServerSession, AppContext], index: int) -> str | None:
    """Find nickname for given index.

    Parameters
    ----------
    ctx : Context
        MCP context containing pool.
    index : int
        Instance index.

    Returns
    -------
    str | None
        Nickname if found, None otherwise.
    """
    for nick, idx in ctx.request_context.lifespan_context.instance_nicknames.items():
        if idx == index:
            return nick
    return None
```

---

## Update All Existing Tools

### 4.1 Pattern for Updating Tools

All tools that currently access `mapdl` need to be updated with this pattern:

```python
@mcp.tool()
def tool_name(
    ctx: Context[ServerSession, AppContext],
    # ... existing parameters ...
    instance: str | int | None = None,  # NEW PARAMETER
) -> str:
    """Tool description.

    Parameters
    ----------
    # ... existing parameter docs ...
    instance : str | int | None, optional
        Instance identifier. Can be instance index (int), nickname (str),
        or None to use the default instance.

    Returns
    -------
    str
        Result description.
    """
    # OLD: mapdl = ctx.request_context.lifespan_context.mapdl
    # NEW:
    mapdl, instance_desc = get_mapdl_instance(ctx, instance)

    if mapdl is None:
        return instance_desc  # Error message

    # Rest of tool implementation remains the same
    # ...
```

### 4.2 Tools to Update

The following tools in `src/ansys/mapdl/mcp/tools.py` need the instance parameter:

1. **`check_mapdl_status`** - Check status of specific instance
2. **`write_comment`** - Write comment in specific instance
3. **`run_mapdl_command`** - Run command on specific instance
4. **`run_multiple_commands`** - Run multiple commands on specific instance
5. **`screenshot`** - Capture screenshot from specific instance

Example for `run_mapdl_command`:

```python
@mcp.tool()
def run_mapdl_command(
    ctx: Context[ServerSession, AppContext],
    cmd: str,
    instance: str | int | None = None,
) -> str:
    """Execute an arbitrary MAPDL command on a specific instance.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    cmd : str
        The MAPDL command to execute.
    instance : str | int | None, optional
        Instance identifier. Can be instance index (int), nickname (str),
        or None to use the default instance. Default is None.

    Returns
    -------
    str
        Command execution result.
    """
    from ansys.mapdl.mcp.helpers import get_mapdl_instance

    mapdl, instance_desc = get_mapdl_instance(ctx, instance)

    if mapdl is None:
        return instance_desc

    logger.info(f"Running command on {instance_desc}: {cmd}")
    result = mapdl.run(cmd)
    return f"MAPDL command executed successfully on {instance_desc}: {result}"
```

---

## New Tools to Add

**Note on Future Tools:**

The `create_pool()` and `exit_instance()` methods are currently implemented as **internal helper functions**
in `helpers.py` to reduce code duplication between `launch_mapdl` and `connect_to_mapdl`.

In the future, `create_pool` may be exposed as an MCP tool to allow users to:
- Create pools with multiple instances directly
- Specify custom nicknames
- Connect to multiple remote instances at once

For now, these remain internal to keep the API simple and maintain backward compatibility.

### 5.1 `list_pool_instances` Tool

```python
@mcp.tool()
def list_pool_instances(ctx: Context[ServerSession, AppContext]) -> str:
    """List all MAPDL instances in the pool with their status and nicknames.

    This tool provides an overview of all instances in the current MapdlPool,
    including their index, nickname (if assigned), IP address, port, and status.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.

    Returns
    -------
    str
        Formatted table of pool instances with their details.
    """
    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool initialized. Use launch_mapdl or connect_to_mapdl first."

    from ansys.mapdl.mcp.helpers import find_nickname

    lines = []
    lines.append(f"MAPDL Pool: {len(pool)} instance(s)\n")
    lines.append(f"Default instance: {ctx.request_context.lifespan_context.default_instance_index}\n")
    lines.append("-" * 80)

    for i, instance in enumerate(pool._instances):
        nickname = find_nickname(ctx, i)
        nickname_str = f' ("{nickname}")' if nickname else ""

        if instance is None:
            lines.append(f"Instance {i}{nickname_str}: DISCONNECTED")
        elif hasattr(instance, "_exited") and instance._exited:
            lines.append(f"Instance {i}{nickname_str}: EXITED")
        else:
            status = "ACTIVE" if not instance.locked else "BUSY"
            lines.append(f"Instance {i}{nickname_str}: {status}")
            lines.append(f"  IP: {instance.ip}")
            lines.append(f"  Port: {instance.port}")
            lines.append(f"  Version: {instance.version}")
            lines.append(f"  Directory: {instance.directory}")

        lines.append("")

    return "\n".join(lines)
```

### 5.2 `set_default_instance` Tool

```python
@mcp.tool()
def set_default_instance(
    ctx: Context[ServerSession, AppContext],
    instance: str | int,
) -> str:
    """Set the default instance for operations without explicit instance specification.

    This tool allows you to change which instance is used by default when
    other tools are called without specifying an instance parameter.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : str | int
        Instance identifier. Can be instance index (int) or nickname (str).

    Returns
    -------
    str
        Confirmation message with new default instance.
    """
    from ansys.mapdl.mcp.helpers import resolve_instance_index, find_nickname

    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool initialized. Use launch_mapdl or connect_to_mapdl first."

    idx = resolve_instance_index(ctx, instance)

    if idx is None:
        from ansys.mapdl.mcp.helpers import list_available_instances
        available = list_available_instances(ctx)
        return f"Instance '{instance}' not found. Available instances:\n{available}"

    # Check if instance is available
    mapdl_instance = pool[idx]
    if mapdl_instance is None:
        return f"Cannot set default to instance {idx}: instance is disconnected"

    if hasattr(mapdl_instance, "_exited") and mapdl_instance._exited:
        return f"Cannot set default to instance {idx}: instance has exited"

    # Set new default
    ctx.request_context.lifespan_context.default_instance_index = idx

    nickname = find_nickname(ctx, idx)
    nickname_str = f' ("{nickname}")' if nickname else ""

    return f"Default instance set to {idx}{nickname_str}"
```

### 5.3 `assign_nickname` Tool

```python
@mcp.tool()
def assign_nickname(
    ctx: Context[ServerSession, AppContext],
    instance: int,
    nickname: str,
) -> str:
    """Assign or update a nickname for an instance.

    Nicknames provide a convenient way to reference instances by name
    instead of numeric index.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    instance : int
        Instance index to assign nickname to.
    nickname : str
        The nickname to assign. Must be unique.

    Returns
    -------
    str
        Confirmation message.
    """
    pool = ctx.request_context.lifespan_context.pool

    if pool is None:
        return "No MAPDL pool initialized. Use launch_mapdl or connect_to_mapdl first."

    # Validate instance index
    if not isinstance(instance, int):
        return f"Instance must be an integer index, got {type(instance).__name__}"

    if instance < 0 or instance >= len(pool._instances):
        return f"Instance index {instance} out of range. Valid range: 0-{len(pool._instances)-1}"

    # Validate instance exists
    mapdl_instance = pool[instance]
    if mapdl_instance is None:
        return f"Cannot assign nickname to instance {instance}: instance is disconnected"

    # Check for existing nickname
    existing_nicknames = ctx.request_context.lifespan_context.instance_nicknames

    # Check if nickname already exists for a different instance
    if nickname in existing_nicknames and existing_nicknames[nickname] != instance:
        return f"Nickname '{nickname}' already assigned to instance {existing_nicknames[nickname]}"

    # Remove old nickname for this instance if it exists
    old_nickname = None
    for nick, idx in list(existing_nicknames.items()):
        if idx == instance and nick != nickname:
            old_nickname = nick
            del existing_nicknames[nick]

    # Assign new nickname
    existing_nicknames[nickname] = instance

    msg = f"Assigned nickname '{nickname}' to instance {instance}"
    if old_nickname:
        msg += f" (replaced old nickname '{old_nickname}')"

    return msg
```

### 5.4 `remove_nickname` Tool

```python
@mcp.tool()
def remove_nickname(
    ctx: Context[ServerSession, AppContext],
    nickname: str,
) -> str:
    """Remove a nickname from an instance.

    Parameters
    ----------
    ctx : Context[ServerSession, AppContext]
        The MCP context containing server session and application context.
    nickname : str
        The nickname to remove.

    Returns
    -------
    str
        Confirmation message.
    """
    existing_nicknames = ctx.request_context.lifespan_context.instance_nicknames

    if nickname not in existing_nicknames:
        return f"Nickname '{nickname}' not found"

    instance_idx = existing_nicknames[nickname]
    del existing_nicknames[nickname]

    return f"Removed nickname '{nickname}' from instance {instance_idx}"
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)

**Goal:** Update core architecture without breaking existing functionality

1. **Update `AppContext` dataclass** (`mcp.py`)
   - Add pool, instance_nicknames, default_instance_index fields
   - Add backward-compatible `mapdl` property
   - Test that existing code still works

2. **Update `app_lifespan`** (`mcp.py`)
   - Modify cleanup to exit pool
   - Update logging messages

3. **Add helper functions** (`helpers.py`)
   - Implement `resolve_instance_index()`
   - Implement `get_mapdl_instance()`
   - Implement `list_available_instances()`
   - Implement `find_nickname()`
   - Implement `create_pool()` (internal method for launch/connect)
   - Implement `exit_instance()` (internal method for disconnect)
   - Add unit tests

4. **Update imports**
   - Add `MapdlPool` import where needed
   - Update type hints

### Phase 2: Connection Management (Days 3-4)

**Goal:** Enable pool creation and management

1. **Update `launch_mapdl` tool** (`tools.py`)
   - Add n_instances and nicknames parameters
   - Create MapdlPool instead of single instance
   - Test launching with 1, 2, and multiple instances

2. **Update `connect_to_mapdl` tool** (`tools.py`)
   - Support connecting to multiple instances
   - Add nicknames parameter
   - Test connecting to existing instances

3. **Update `disconnect_from_mapdl` tool** (`tools.py`)
   - Add instance parameter
   - Support disconnecting specific instances or entire pool
   - Test partial and full disconnection

4. **Add instance management tools** (`tools.py`)
   - Implement `list_pool_instances`
   - Implement `set_default_instance`
   - Implement `assign_nickname`
   - Implement `remove_nickname`
   - Add tests for each

### Phase 3: Tool Updates (Days 5-6)

**Goal:** Update all existing tools to support instance parameter

1. **Update tools in order of importance:**
   - `check_mapdl_status` ✓
   - `run_mapdl_command` ✓
   - `run_multiple_commands` ✓
   - `write_comment` ✓
   - `screenshot` ✓

2. **For each tool:**
   - Add instance parameter with default None
   - Replace direct mapdl access with `get_mapdl_instance()`
   - Update docstring
   - Add instance info to response messages
   - Add test cases for instance parameter

3. **Update all context tools** (`contexts.py`)
   - No changes needed (they don't access mapdl directly)

### Phase 4: Testing & Documentation (Days 7-8)

**Goal:** Ensure quality and provide clear documentation

1. **Update existing tests**
   - Update `test_basic.py` for new context structure
   - Update `test_tools.py` for instance parameter
   - Update `test_integration.py` for pool usage
   - Add backward compatibility tests

2. **Add new test files**
   - `test_pool_management.py` - Pool creation, connection, disconnection
   - `test_multi_instance.py` - Multiple instance operations
   - `test_instance_selection.py` - Instance resolution and selection
   - `test_nicknames.py` - Nickname assignment and usage

3. **Update documentation**
   - Update `README.md` with multi-instance examples
   - Add migration guide for existing users
   - Document new tools
   - Add troubleshooting section

4. **Code review and refinement**
   - Review all changes
   - Ensure consistent error messages
   - Optimize performance
   - Check code style and formatting

---

## Backward Compatibility Strategy

### Maintaining Existing Workflows

1. **Single Instance Default**
   - When `n_instances=1` (default), behavior is nearly identical to old version
   - `context.mapdl` property returns first instance for backward compatibility
   - Tools without instance parameter use default instance

2. **Transparent Migration**
   - Old code: `launch_mapdl()` → creates pool with 1 instance
   - Old code: `run_mapdl_command(ctx, "PREP7")` → runs on default instance
   - No breaking changes to tool signatures (new parameters are optional)

3. **Deprecation Path** (Optional for future)
   - Keep `context.mapdl` property indefinitely (no removal planned)
   - Document preferred approach (using instance parameter) in examples
   - Add warnings only if truly needed

### Testing Backward Compatibility

```python
def test_backward_compatibility():
    """Ensure single-instance workflows still work."""
    # Launch single instance (old style)
    launch_mapdl(ctx)

    # Use tools without instance parameter (old style)
    run_mapdl_command(ctx, "PREP7")
    check_mapdl_status(ctx)

    # Access via context.mapdl property (old style)
    assert ctx.request_context.lifespan_context.mapdl is not None
```

---

## Key Design Decisions

### 9.1 Pool Initialization

**Decision:** Pool created lazily on first connection/launch

**Rationale:**
- Avoids unnecessary pool creation overhead
- Allows flexible configuration based on user needs
- Follows principle of least surprise

**Implementation:**
- First call to `launch_mapdl` or `connect_to_mapdl` creates pool
- Subsequent calls fail with clear error (must disconnect first)
- Default pool size is 1 for backward compatibility

### 9.2 Instance Identification

**Decision:** Three ways to reference instances

**Methods:**
1. **Index (int):** Direct array index (0, 1, 2, ...)
   - Fast, direct access
   - Matches MapdlPool internal structure
   - Good for programmatic use

2. **Nickname (str):** User-defined names
   - Human-friendly ("meshing", "solving", "postproc")
   - Easier to remember and use
   - Good for interactive use

3. **None:** Default instance (index 0)
   - Backward compatible
   - Simplifies single-instance workflows
   - No explicit specification needed

**Rationale:**
- Flexibility for different use cases
- Supports both interactive and programmatic workflows
- Clear and intuitive

### 9.3 Pool vs Individual Access

**Decision:** Hide MapdlPool from users

**What Users See:**
- "Instance 0", "Instance 1", "my_nickname"
- Instance-specific operations
- Pool as a collection of instances

**What Users DON'T See:**
- `MapdlPool` object directly
- Pool methods like `.map()`, `.run_batch()`
- Internal pool state

**Rationale:**
- Simpler mental model
- Focus on individual instances
- Easier to understand and use
- Matches MCP tool-based interaction model

**Alternative Considered:**
- Expose pool methods as MCP tools
- Decision: Not needed for v1, can add later if requested

### 9.4 Nickname Management

**Decision:** Nicknames managed through context, not pool

**Storage:** `context.instance_nicknames: Dict[str, int]`

**Rules:**
- One nickname per instance (latest wins)
- Nicknames must be unique across pool
- Case-sensitive
- Can be changed/removed anytime

**Rationale:**
- MapdlPool doesn't have built-in nickname support
- Nicknames are user-facing convenience
- Easy to implement and manage
- Clear ownership (context owns mappings)

### 9.5 Error Handling Philosophy

**Decision:** Clear, actionable error messages with context

**Pattern:**
```python
if error_condition:
    # Explain what went wrong
    # Show what's available
    # Suggest next action
    return f"Error: {problem}. Available: {options}. Try: {suggestion}"
```

**Examples:**
- Instance not found → List available instances
- Pool not initialized → Show how to initialize
- Nickname conflict → Show existing assignment

**Rationale:**
- Users should never be stuck
- Errors are learning opportunities
- Reduce support burden

---

## Error Handling

### 10.1 Common Error Scenarios

#### Pool Not Initialized
```python
"No MAPDL pool available. Use launch_mapdl or connect_to_mapdl to initialize."
```

#### Instance Not Found
```python
"Instance 'solver1' not found. Available instances:
  0 ("meshing"): active
  1: active
  2 ("postproc"): active"
```

#### Instance Disconnected
```python
"Instance 2 is not available (disconnected). Use list_pool_instances to see status."
```

#### Instance Exited
```python
"Instance 0 has exited. Please reconnect or launch a new instance."
```

#### Invalid Instance Index
```python
"Instance index 5 out of range. Valid range: 0-2"
```

#### Duplicate Nickname
```python
"Nickname 'solver' already assigned to instance 1. Choose a different nickname or remove the existing one first."
```

#### Pool Already Exists
```python
"MAPDL pool already exists with 3 instance(s). Use disconnect_from_mapdl to clear the pool before launching new instances."
```

#### Nickname/Index Mismatch
```python
"Error: Number of nicknames (2) must match n_instances (3)"
```

### 10.2 Error Handling Best Practices

1. **Always return string** - Never raise exceptions in tools
2. **Be specific** - Tell exactly what went wrong
3. **Show state** - Display current pool/instance status
4. **Suggest action** - Guide user to resolution
5. **Be consistent** - Use same patterns across all tools

---

## Example Usage Scenarios

### Scenario 1: Single Instance (Backward Compatible)

```python
# Launch one instance with expanded parameters - works exactly as before
>>> launch_mapdl(
...     exec_file=None,
...     run_location="/path/to/working/dir",
...     jobname="my_analysis",
...     nproc=4,
...     ram=4096,
...     override=False,
...     additional_switches="-p aa_r",
...     start_timeout=60
... )
"Successfully launched 1 MAPDL instance(s)
Pool size: 1
  Instance 0 (nickname: "Instance_0"): 127.0.0.1:50052
    Version: 24.2
    Directory: /path/to/working/dir"

# Run commands - no instance parameter needed (uses default instance)
>>> run_mapdl_command(cmd="PREP7")
"MAPDL command executed successfully on instance 0: ..."

>>> check_mapdl_status()
"{"connection": {...}, "information": {...}}"

>>> screenshot()
[TextContent(...), ImageContent(...)]

# Disconnect from the default instance (instance 0)
>>> disconnect_from_mapdl()
"Successfully disconnected instance 0 at 127.0.0.1:50052. Pool cleared (last instance)."
```

### Scenario 2: Multiple Instances with Indices

```python
# Launch pool with 3 instances
>>> launch_mapdl(n_instances=3, nproc=2)
"Successfully launched 3 MAPDL instance(s)
Pool size: 3
  Instance 0: 127.0.0.1:50052
    Version: 24.2
    Directory: C:\\Users\\...\\Instance_0
  Instance 1: 127.0.0.1:50053
    Version: 24.2
    Directory: C:\\Users\\...\\Instance_1
  Instance 2: 127.0.0.1:50054
    Version: 24.2
    Directory: C:\\Users\\...\\Instance_2"

# List instances
>>> list_pool_instances()
"MAPDL Pool: 3 instance(s)
Default instance: 0
--------------------------------------------------------------------------------
Instance 0: ACTIVE
  IP: 127.0.0.1
  Port: 50052
  Version: 24.2
  Directory: C:\\Users\\...\\Instance_0

Instance 1: ACTIVE
  IP: 127.0.0.1
  Port: 50053
  Version: 24.2
  Directory: C:\\Users\\...\\Instance_1

Instance 2: ACTIVE
  IP: 127.0.0.1
  Port: 50054
  Version: 24.2
  Directory: C:\\Users\\...\\Instance_2"

# Run commands on specific instances
>>> run_mapdl_command(cmd="PREP7", instance=0)
"MAPDL command executed successfully on instance 0: ..."

>>> run_mapdl_command(cmd="/SOLU", instance=1)
"MAPDL command executed successfully on instance 1: ..."

>>> run_mapdl_command(cmd="POST1", instance=2)
"MAPDL command executed successfully on instance 2: ..."

# Set different default
>>> set_default_instance(instance=1)
"Default instance set to 1"

# Now commands without instance go to instance 1
>>> run_mapdl_command(cmd="SOLVE")
"MAPDL command executed successfully on instance 1: ..."
```

### Scenario 3: Multiple Instances with Nicknames

```python
# Launch pool with nicknames
>>> launch_mapdl(
...     n_instances=3,
...     nproc=2,
...     nicknames=["meshing", "solving", "postproc"]
... )
"Successfully launched 3 MAPDL instance(s)
Pool size: 3
  Instance 0 (nickname: "meshing"): 127.0.0.1:50052
    Version: 24.2
    Directory: C:\\Users\\...\\Instance_0
  Instance 1 (nickname: "solving"): 127.0.0.1:50053
    Version: 24.2
    Directory: C:\\Users\\...\\Instance_1
  Instance 2 (nickname: "postproc"): 127.0.0.1:50054
    Version: 24.2
    Directory: C:\\Users\\...\\Instance_2"

# Use nicknames to run commands
>>> run_mapdl_command(cmd="PREP7", instance="meshing")
"MAPDL command executed successfully on instance 0 ("meshing"): ..."

>>> run_mapdl_command(cmd="/SOLU", instance="solving")
"MAPDL command executed successfully on instance 1 ("solving"): ..."

>>> screenshot(instance="postproc")
[TextContent(...), ImageContent(...)]

# Set default by nickname
>>> set_default_instance(instance="solving")
"Default instance set to 1 ("solving")"

# Assign new nickname to existing instance
>>> assign_nickname(instance=2, nickname="results")
"Assigned nickname 'results' to instance 2 (replaced old nickname 'postproc')"
```

### Scenario 4: Connect to Existing Instances

```python
# Connect to multiple running instances
>>> connect_to_mapdl(
...     ip=["192.168.1.10", "192.168.1.11", "192.168.1.12"],
...     port=[50052, 50052, 50052],
...     nicknames=["remote1", "remote2", "remote3"]
... )
"Successfully connected to 3 MAPDL instance(s)
Pool size: 3
  Instance 0 (nickname: "remote1"): 192.168.1.10:50052
    Version: 24.2
  Instance 1 (nickname: "remote2"): 192.168.1.11:50052
    Version: 24.2
  Instance 2 (nickname: "remote3"): 192.168.1.12:50052
    Version: 24.2"

# Use remote instances
>>> check_mapdl_status(instance="remote1")
"{...}"

>>> run_multiple_commands(
...     commands=["PREP7", "ET,1,SOLID185", "MP,EX,1,200E9"],
...     instance="remote2"
... )
"Successfully executed 3 MAPDL commands on instance 1 ("remote2"):..."
```

### Scenario 5: Partial Disconnection

```python
# Launch 3 instances
>>> launch_mapdl(n_instances=3, nicknames=["inst1", "inst2", "inst3"])
"Successfully launched 3 MAPDL instance(s)..."

# Disconnect instance 1
>>> disconnect_from_mapdl(instance=1)
"Successfully disconnected instance 1 at 127.0.0.1:50053"

# List instances - shows instance 1 as disconnected
>>> list_pool_instances()
"MAPDL Pool: 3 instance(s)
Default instance: 0
--------------------------------------------------------------------------------
Instance 0 ("inst1"): ACTIVE
  IP: 127.0.0.1
  Port: 50052
  ...

Instance 1: DISCONNECTED

Instance 2 ("inst3"): ACTIVE
  IP: 127.0.0.1
  Port: 50054
  ..."

# Disconnect entire pool
>>> disconnect_from_mapdl()
"Successfully disconnected from entire MAPDL pool"
```

---

## Files to Modify

### Modified Files

1. **`src/ansys/mapdl/mcp/mcp.py`**
   - Update `AppContext` dataclass
   - Update `app_lifespan` function
   - Update imports

2. **`src/ansys/mapdl/mcp/tools.py`**
   - Update `launch_mapdl` tool
   - Update `connect_to_mapdl` tool
   - Update `disconnect_from_mapdl` tool
   - Update `check_mapdl_status` tool
   - Update `write_comment` tool
   - Update `run_mapdl_command` tool
   - Update `run_multiple_commands` tool
   - Update `screenshot` tool
   - Add `list_pool_instances` tool
   - Add `set_default_instance` tool
   - Add `assign_nickname` tool
   - Add `remove_nickname` tool

3. **`src/ansys/mapdl/mcp/helpers.py`**
   - Add `create_pool` function (internal method)
   - Add `exit_instance` function (internal method)
   - Add `resolve_instance_index` function
   - Add `get_mapdl_instance` function
   - Add `list_available_instances` function
   - Add `find_nickname` function

4. **`tests/test_basic.py`**
   - Update context fixtures
   - Add pool-related tests
   - Update assertion checks

5. **`tests/test_tools.py`**
   - Update tool tests for instance parameter
   - Add multi-instance test cases

6. **`tests/test_integration.py`**
   - Update integration tests for pool
   - Add multi-instance integration tests

7. **`README.md`**
   - Add multi-instance documentation
   - Add usage examples
   - Update feature list

### New Files

1. **`tests/test_pool_management.py`**
   - Tests for pool creation, connection, disconnection
   - Tests for pool lifecycle

2. **`tests/test_multi_instance.py`**
   - Tests for multi-instance operations
   - Tests for concurrent instance usage

3. **`tests/test_instance_selection.py`**
   - Tests for instance resolution
   - Tests for nickname handling

4. **`tests/test_nicknames.py`**
   - Tests for nickname assignment
   - Tests for nickname conflicts
   - Tests for nickname removal

5. **`MIGRATION_GUIDE.md`** (Optional)
   - Guide for migrating from single to multi-instance
   - Breaking changes (if any)
   - Best practices

---

## Technical Details

### MapdlPool Key Attributes and Methods

Based on analysis of `ansys.mapdl.core.pool.MapdlPool`:

#### Attributes
- `_instances: List[Mapdl | None]` - List of MAPDL instances
- `_n_instances: int` - Number of instances in pool
- `_ips: List[str]` - IP addresses of instances
- `_ports: List[int]` - Ports of instances
- `_names: Callable[[int], str]` - Function to generate instance names
- `_active: bool` - Whether pool is active
- `_spawning_i: int` - Counter for spawning instances
- `_exiting_i: int` - Counter for exiting instances

#### Methods
- `__init__(n_instances, ip, port, start_instance, ...)` - Initialize pool
- `__len__()` - Return number of active instances
- `__getitem__(key: int)` - Get instance by index
- `__iter__()` - Iterate through active instances
- `exit(block=False)` - Exit all instances
- `next_available(return_index=False)` - Get next available instance
- `next(return_index=False)` - Context manager for instance

#### Properties
- `ready: bool` - True if all instances are ready
- `_spawning: bool` - True if spawning instances
- `_exiting: bool` - True if exiting instances

### Instance State Management

Each MAPDL instance in the pool has:
- `locked: bool` - Whether instance is locked for exclusive use
- `_busy: bool` - Whether instance is currently processing
- `_exited: bool` - Whether instance has exited
- `_exiting: bool` - Whether instance is exiting
- `ip: str` - IP address
- `port: int` - Port number
- `version: str` - MAPDL version
- `directory: str` - Working directory

### Context Manager Pattern

MapdlPool supports context manager for safe instance access:

```python
with pool.next() as mapdl:
    # mapdl is locked and marked as busy
    mapdl.prep7()
    # Commands run on this specific instance
# mapdl is automatically unlocked and marked as not busy
```

We will use `get_mapdl_instance()` helper instead of context manager for simplicity in MCP tools.

### Thread Safety Considerations

MapdlPool uses threading internally:
- Instance spawning is threaded
- Instance exiting is threaded
- Pool monitoring runs in background thread (if `restart_failed=True`)

For MCP server:
- Each tool call is sequential
- No concurrent access to same instance expected
- Can leverage pool's internal thread safety
- No additional locking needed in MCP layer

### Performance Considerations

1. **Pool Creation:** Takes time proportional to `n_instances`
   - Each instance launches in separate thread
   - `wait=True` blocks until all ready
   - Progress bar shows status

2. **Instance Access:** O(1) by index
   - Direct array access: `pool[i]`
   - Nickname lookup: O(n) dict lookup (acceptable for small n)

3. **Instance Availability:** May need to wait
   - `next_available()` loops until instance free
   - In MCP context, instances rarely locked (no concurrent use)

### Error Recovery

MapdlPool has built-in recovery:
- `restart_failed=True` monitors and restarts failed instances
- We will use `restart_failed=True` by default
- Failed instances show in `list_pool_instances` as "exited"
- User can reconnect or pool auto-restarts

---

## Appendix: Code Examples

### Complete Example: Launch and Use Pool

```python
# 1. Launch pool with 3 instances
result = launch_mapdl(
    n_instances=3,
    nproc=2,
    nicknames=["mesh", "solve", "post"]
)
# "Successfully launched 3 MAPDL instance(s)..."

# 2. List instances
result = list_pool_instances()
# Shows all 3 instances with nicknames

# 3. Run commands on different instances in parallel (conceptually)
result1 = run_multiple_commands(
    commands=["PREP7", "ET,1,SOLID185", "MP,EX,1,200E9"],
    instance="mesh"
)

result2 = run_mapdl_command(cmd="/SOLU", instance="solve")

result3 = check_mapdl_status(instance="post")

# 4. Set default instance
result = set_default_instance(instance="solve")

# 5. Commands without instance go to default
result = run_mapdl_command(cmd="SOLVE")
# Runs on "solve" instance

# 6. Cleanup
result = disconnect_from_mapdl()
# Exits entire pool
```

### Complete Example: Connect to Remote Pool

```python
# 1. Connect to existing remote instances
result = connect_to_mapdl(
    ip=["node1.cluster", "node2.cluster", "node3.cluster"],
    port=[50052, 50052, 50052],
    nicknames=["node1", "node2", "node3"]
)

# 2. Distribute work across nodes
commands_mesh = ["PREP7", "ET,1,SOLID185", ...]
commands_solve = ["/SOLU", "SOLVE", ...]
commands_post = ["POST1", ...]

result1 = run_multiple_commands(commands_mesh, instance="node1")
result2 = run_multiple_commands(commands_solve, instance="node2")
result3 = run_multiple_commands(commands_post, instance="node3")

# 3. Disconnect from all
result = disconnect_from_mapdl()
```

---

## Summary

This implementation plan provides a comprehensive roadmap for adding multi-instance MAPDL support to pymapdl-mcp using MapdlPool. The design prioritizes:

1. **Backward Compatibility** - Existing single-instance workflows continue to work unchanged
2. **Code Reusability** - Internal `create_pool()` and `exit_instance()` methods reduce duplication
3. **User-Friendly Interface** - Simple, intuitive instance selection (index/nickname/default)
4. **Transparency** - Pool hidden from users in single-instance mode, focus on instances
5. **Flexibility** - Support for local and remote instances, multiple configurations
6. **Robustness** - Clear error messages, automatic pool cleanup when last instance exits

### Key Design Decisions

- **Internal Methods**: `create_pool()` and `exit_instance()` are internal helper functions that:
  - Reduce code duplication between `launch_mapdl` and `connect_to_mapdl`
  - Handle pool lifecycle management (creation, exit, cleanup)
  - Use MapdlPool's built-in naming for nicknames
  - May become MCP tools in the future for advanced multi-instance workflows

- **Automatic Pool Cleanup**: When the last MAPDL instance in the pool is exited, the pool object
  is automatically cleared from the context

- **Default Behavior**: Single instance remains the default for backward compatibility, with
  MapdlPool infrastructure used internally for consistency

The phased implementation approach ensures steady progress while maintaining working code at each stage. Testing and documentation are integral parts of the process, ensuring high quality and usability.

**Estimated Timeline:** 8 working days for complete implementation, testing, and documentation.

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1 implementation (core infrastructure and internal methods)
3. Iterative development with testing at each phase
4. Final integration and documentation
