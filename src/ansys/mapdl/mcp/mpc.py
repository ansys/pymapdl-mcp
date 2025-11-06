"""Example showing lifespan support for startup/shutdown with strong typing."""

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logging.info("Loading modules...")


@dataclass
class AppContext:
    """Application context with typed dependencies.

    Attributes
    ----------
    mapdl : Optional[Any]
        MAPDL instance connection. Using Any to avoid type issues with MAPDL variants.
    """

    mapdl: Optional[Any] = None  # Using Any to avoid type issues with MAPDL variants


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
        Application context for storing MAPDL connections.
    """
    context = AppContext()
    try:
        print(
            "MCP Server initialized. Use connect_to_mapdl to establish a connection.",
            file=sys.stderr,
        )
        yield context

    finally:
        # Cleanup on shutdown
        if context.mapdl is not None:
            try:
                print("Disconnecting from MAPDL...", file=sys.stderr)
                context.mapdl.exit()
                print("MAPDL disconnect complete", file=sys.stderr)
            except Exception as e:
                print(f"Error during MAPDL disconnect: {e}", file=sys.stderr)


# Pass lifespan to server
mcp = FastMCP("PyMAPDL", lifespan=app_lifespan)


def main():
    """Entry point for the MCP server.

    This function initializes and runs the FastMCP server using stdio
    for communication with MCP clients.
    """
    import asyncio

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
