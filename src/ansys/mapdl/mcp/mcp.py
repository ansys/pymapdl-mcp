"""Lifespan and CLI entry for the MCP server with startup options."""

import argparse
import ipaddress
import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with typed dependencies and CLI options.

    Attributes
    ----------
    mapdl : Optional[Any]
        MAPDL instance connection.
    transport_type : str
        Transport type used for the MCP server (e.g. 'stdio').
    mapdl_ip : str
        IP/hostname of MAPDL instance.
    mapdl_port : int
        gRPC port where MAPDL is listening.
    connect_on_startup : bool
        Whether to attempt connecting to MAPDL during startup.
    """

    mapdl: Optional[Any] = None
    transport_type: str = "stdio"
    mapdl_ip: str = "127.0.0.1"
    mapdl_port: int = 50052
    connect_on_startup: bool = False


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with typed context and startup connect.

    The server object may carry parsed CLI options in `server._cli_config`.
    If `connect_on_startup` is True and `transport_type` is `stdio`, an
    initial attempt to connect to MAPDL will be performed. Failures are
    logged but do not stop the server.
    """
    context = AppContext()

    # Populate context from CLI config on server if available
    cli_cfg = getattr(server, "_cli_config", None)
    if cli_cfg is not None:
        context.transport_type = cli_cfg.get("transport_type", context.transport_type)
        context.mapdl_ip = cli_cfg.get("mapdl_ip", context.mapdl_ip)
        context.mapdl_port = cli_cfg.get("mapdl_port", context.mapdl_port)
        context.connect_on_startup = cli_cfg.get("connect_on_startup", context.connect_on_startup)

    try:
        logger.info("MCP Server initialized. Use connect_to_mapdl to establish a connection.")

        # Attempt an initial connection if requested and using stdio transport
        if context.connect_on_startup and context.transport_type == "stdio":
            try:
                from ansys.mapdl.core import Mapdl  # type: ignore

                logger.info(
                    "Attempting initial MAPDL connection to %s:%s",
                    context.mapdl_ip,
                    context.mapdl_port,
                )

                mapdl = Mapdl(
                    start_instance=False,
                    ip=context.mapdl_ip,
                    port=context.mapdl_port,
                    cleanup_on_exit=False,
                    loglevel="INFO",
                )

                context.mapdl = mapdl
                logger.info("Connected to MAPDL at %s:%s", context.mapdl_ip, context.mapdl_port)

            except Exception as e:  # pragma: no cover - best-effort startup only
                logger.error(
                    "Initial connection to MAPDL failed at %s:%s - %s",
                    context.mapdl_ip,
                    context.mapdl_port,
                    str(e),
                )

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


# Pass lifespan to server
mcp = FastMCP("PyMAPDL", lifespan=app_lifespan)


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
    parser.add_argument("--type", dest="transport_type", choices=["stdio", "http"], default="stdio", help="Transport type. Allowed: stdio, http")
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

    # Basic IP validation - allow hostnames but try ipaddress for numeric IPs
    try:
        ipaddress.ip_address(args.mapdl_ip)
    except Exception:
        # If this is not a pure IP address, assume hostname; no further validation
        pass

    # If unsupported transport chosen, provide clear message and exit
    if args.transport_type != "stdio":
        print(
            f"Transport '{args.transport_type}' is not implemented yet. Only 'stdio' is supported.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Attach CLI config to server so lifespan can read it
    setattr(mcp, "_cli_config", {
        "transport_type": args.transport_type,
        "mapdl_ip": args.mapdl_ip,
        "mapdl_port": args.mapdl_port,
        "connect_on_startup": bool(args.connect_on_startup),
    })

    # Run server using stdio transport
    import asyncio

    asyncio.run(mcp.run_stdio_async())
