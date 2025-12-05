"""Lifespan and CLI entry for the MCP server with startup options."""

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ansys.common.mcp import (
    PyAnsysBaseMCP,
    get_logger,
)
from ansys.common.mcp.context import PyAnsysBaseAppContext
from ansys.common.mcp.helpers import PersistentPythonSession

logger = get_logger(__name__)


@dataclass
class PyMAPDLAppContext(PyAnsysBaseAppContext):
    """Application context with typed dependencies and CLI options.

    Attributes
    ----------
    pool : Optional[Any]
        MapdlPool instance managing multiple MAPDL connections.
        Using Any to avoid type issues with MapdlPool.
    instance_nicknames : Dict[str, int]
        Mapping of user-defined nicknames to pool indices.
    default_instance_index : int
        Index of the default instance to use when none specified.
    transport_type : str
        Transport type used for the MCP server (e.g. 'stdio').
    mapdl_ip : str
        IP/hostname of MAPDL instance.
    mapdl_port : int
        gRPC port where MAPDL is listening.
    connect_on_startup : bool
        Whether to attempt connecting to MAPDL during startup.
    """

    pool: Optional[Any] = None  # MapdlPool instance
    instance_nicknames: Dict[str, int] = field(default_factory=dict)
    default_instance_index: int = 0
    transport_type: str = "stdio"
    mapdl_ip: str = "127.0.0.1"
    mapdl_port: int = 50052
    connect_on_startup: bool = False

    @property
    def mapdl(self) -> Optional[Any]:
        """Returns the default MAPDL instance for backward compatibility.

        Returns
        -------
        Optional[Any]
            The default MAPDL instance from the pool, or None if no pool exists.
        """
        if self.pool is not None and len(self.pool) > 0:
            try:
                return self.pool[self.default_instance_index]
            except (IndexError, KeyError):
                return None
        return None
   
    @property
    def product_instance(self) -> Optional[Any]:
        """Returns the default MAPDL instance for backward compatibility.

        Returns
        -------
        Optional[Any]
            The default MAPDL instance from the pool, or None if no pool exists.
        """
        return self.mapdl
    
    @product_instance.setter
    def product_instance(self, value: Any) -> None:
        """Setter for product_instance (no-op, use pool directly)."""
        pass


@dataclass
class PyMAPDLMCPState:
    """State holder for MCP server."""

    lock_connection: bool = False


mcp_state = PyMAPDLMCPState()


class PyMAPDLMCP(PyAnsysBaseMCP):
    """FastMCP server for managing MAPDL instances."""

    def create_context(self) -> PyMAPDLAppContext:
        """
        Create a new application context.

        Returns
        -------
        PyMAPDLAppContext
            The application context for managing MAPDL instances.
        """
        python_session=PersistentPythonSession(
            python_executable=self.python_executable,
            working_directory=self.working_directory,
        )
        self.context = PyMAPDLAppContext(
            python_session=python_session,
            command_history=[],
        )

        # Populate context from CLI config on server if available
        cli_cfg = getattr(self.server, "_cli_config", None)

        if cli_cfg is not None:
            self.context.transport_type = cli_cfg.get("transport_type", self.context.transport_type)
            self.context.mapdl_ip = cli_cfg.get("mapdl_ip", self.context.mapdl_ip)
            self.context.mapdl_port = cli_cfg.get("mapdl_port", self.context.mapdl_port)
            self.context.connect_on_startup = cli_cfg.get("connect_on_startup", self.context.connect_on_startup)

        return self.context

    def product_startup(self):
        """
        PyMAPDLMCP specific startup actions.
        """
        logger.info("PyMAPDLMCP server starting up...")
        # Attempt an initial connection if requested and using stdio transport
        if self.context.connect_on_startup and self.context.transport_type == "stdio":
            mcp_state.lock_connection = True

            logger.info(
                "MCP Server initialized. Attempting MAPDL connection on startup to %s:%s",
                self.context.mapdl_ip,
                self.context.mapdl_port,
            )

            try:
                from ansys.mapdl.mcp.helpers import create_pool

                create_pool(
                    ip=[self.context.mapdl_ip],
                    port=[self.context.mapdl_port],
                    start_instance=False,
                    cleanup_on_exit=False,
                    loglevel="INFO",
                )

            except Exception:  # pragma: no cover - best-effort startup only
                logger.exception(
                    "Initial connection to MAPDL failed at %s:%s",
                    self.context.mapdl_ip,
                    self.context.mapdl_port,
                )
        else:
            logger.info("MCP Server initialized. Use connect_to_mapdl to establish a connection.")


    def product_cleanup(self):
        if self.context.pool is not None:
            try:
                logger.info("Exiting MAPDL pool...")
                self.context.pool.exit()
                logger.info("MAPDL pool exit complete")
            except Exception as e:
                logger.error(f"Error during MAPDL pool exit: {e}")
        self.context.instance_nicknames.clear()

    


# Pass lifespan to server
mcp = PyMAPDLMCP("PyMAPDL MCP Server")
mcp.mcp_state = mcp_state


def add_tool(func):
    """Wrap functions to register them as MCP tools.

    It does return the original function unchanged.
    """
    mcp.tool(func)

    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapped


def _validate_port(port: int) -> int:
    if port < 1 or port > 65535:
        raise argparse.ArgumentTypeError("Port must be in range 1-65535")
    return port


def main(argv: list[str] | None = None) -> None:
    """Entry point for the MCP server.

    Parameters
    ----------
    argv : list[str] | None
        Optional list of arguments for testing. Defaults to `sys.argv[1:]`.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="ansys.mapdl.mcp")
    parser.add_argument(
        "--transport",
        dest="transport_type",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type. Allowed: stdio, http",
    )
    parser.add_argument("--ip", dest="mapdl_ip", default="127.0.0.1", help="MAPDL IP or hostname")
    parser.add_argument(
        "--port",
        dest="mapdl_port",
        type=lambda v: _validate_port(int(v)),
        default=50052,
        help="MAPDL gRPC port (1-65535)",
    )
    parser.add_argument(
        "--connect-on-startup",
        dest="connect_on_startup",
        action="store_true",
        help="Attempt to connect to MAPDL during MCP startup",
    )

    args = parser.parse_args(argv)

    # If unsupported transport chosen, provide clear message and exit
    if args.transport_type != "stdio":
        print(
            f"Transport '{args.transport_type}' is not implemented yet. Only 'stdio' is supported.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Attach CLI config to server so lifespan can read it
    setattr(
        mcp,
        "_cli_config",
        {
            "transport_type": args.transport_type,
            "mapdl_ip": args.mapdl_ip,
            "mapdl_port": args.mapdl_port,
            "connect_on_startup": bool(args.connect_on_startup),
        },
    )

    # Run server using stdio transport
    import asyncio

    asyncio.run(mcp.run_stdio_async())
