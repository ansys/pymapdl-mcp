"""Example showing lifespan support for startup/shutdown with strong typing."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


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
            The default MAPDL instance from the pool, or None if no pool exists.
        """
        if self.pool is not None and len(self.pool) > 0:
            try:
                return self.pool[self.default_instance_index]
            except (IndexError, KeyError):
                return None
        return None


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
        logger.info(
            "MCP Server initialized. Use connect_to_mapdl or launch_mapdl to establish connections."
        )
        yield context

    finally:
        # Cleanup on shutdown - exit entire pool
        if context.pool is not None:
            try:
                logger.info("Exiting MAPDL pool...")
                context.pool.exit()
                logger.info("MAPDL pool exit complete")
            except Exception as e:
                logger.error(f"Error during MAPDL pool exit: {e}")
        context.instance_nicknames.clear()


# Pass lifespan to server
mcp = FastMCP("PyMAPDL", lifespan=app_lifespan)


def main():
    """Entry point for the MCP server.

    This function initializes and runs the FastMCP server using stdio
    for communication with MCP clients.
    """
    import asyncio

    asyncio.run(mcp.run_stdio_async())
