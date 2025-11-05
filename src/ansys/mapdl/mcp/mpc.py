"""Example showing lifespan support for startup/shutdown with strong typing."""

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional

from ansys.mapdl.core import Mapdl
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

logging.basicConfig(level=logging.INFO)
logging.info("Loading modules...")


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    mapdl: Optional[Any]  # Using Any to avoid type issues with MAPDL variants


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    mapdl = None
    try:
        # Connect to existing MAPDL instance running in Docker
        print("Connecting to MAPDL instance on port 50052...", file=sys.stderr)

        # Connect to existing MAPDL instance
        mapdl = Mapdl(
            start_instance=False,
            ip="localhost",
            port=50052,
            cleanup_on_exit=False,  # Don't clean up since we didn't launch it
            loglevel="DEBUG",
            log_apdl="/Users/german.ayuso/Other_projects/pymapdl-mcp/mapdl.log",
        )

        print("Connected to MAPDL successfully!", file=sys.stderr)
        print(f"MAPDL version: {mapdl.version}", file=sys.stderr)

        yield AppContext(mapdl=mapdl)

    except Exception as e:
        print(f"Error during MAPDL initialization: {e}", file=sys.stderr)
        print(f"Exception type: {type(e).__name__}", file=sys.stderr)

        # Create a dummy context if MAPDL fails to launch
        print("Creating fallback context without MAPDL", file=sys.stderr)
        raise e
        yield AppContext(mapdl=None)

    finally:
        # Cleanup on shutdown
        if mapdl is not None:
            try:
                print("Disconnecting from MAPDL...", file=sys.stderr)
                # Don't call exit() since MAPDL is running in Docker
                # Just disconnect the client
                print("MAPDL disconnect complete", file=sys.stderr)
            except Exception as e:
                print(f"Error during MAPDL disconnect: {e}", file=sys.stderr)


# Pass lifespan to server
mcp = FastMCP("PyMAPDL", lifespan=app_lifespan)


# Access type-safe lifespan context in tools
@mcp.tool()
def check_mapdl_status(ctx: Context[ServerSession, AppContext]) -> str:
    """Check the status of MAPDL initialization."""
    mapdl = ctx.request_context.lifespan_context.mapdl

    return f"MAPDL is available. Version: {mapdl.version}"  # type: ignore[union-attr]


@mcp.tool()
def write_comment(ctx: Context[ServerSession, AppContext], comment: str) -> str:
    """Tool that writes a comment in MAPDL."""
    mapdl = ctx.request_context.lifespan_context.mapdl

    print(f"Writing comment: {comment}", file=sys.stderr)
    result = mapdl.com(f"{comment}", mute=True)  # type: ignore[union-attr]
    return f"Comment written successfully: {result}"


@mcp.tool()
def run_mapdl_command(ctx: Context[ServerSession, AppContext], cmd: str) -> str:
    """Execute a MAPDL command and return the result."""
    mapdl = ctx.request_context.lifespan_context.mapdl

    result = mapdl.run(cmd)  # type: ignore[union-attr]
    return f"MAPDL command executed successfully: {result}"


def main():
    """Start the MCP server and run it via stdio."""
    import asyncio

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
