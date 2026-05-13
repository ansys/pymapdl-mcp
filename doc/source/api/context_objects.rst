Context objects
================

This page describes the internal context objects used by PyMAPDL-MCP.

App context
-----------

The app context maintains the state of the PyMAPDL-MCP server.

**Key attributes**:

- ``mapdl``: Current PyMAPDL instance (if connected).
- ``config``: Configuration settings.
- ``logger``: Logger instance.

**Responsibilities**:

- Manages the MAPDL connection lifecycle.
- Stores session state.
- Provides access to PyMAPDL features.

Tool context
------------

Each tool receives a context object that provides:

- Access to the app context
- Request/response handling
- Logging capabilities

**Usage in tools**:

.. code-block:: python

    def my_tool(ctx: Context, parameter: str) -> str:
        # Access the MAPDL instance
        mapdl = ctx.application_context.mapdl

        # Perform operations
        result = mapdl.prep7()

        return f"Result: {result}"

Connection management
---------------------

Connection state
~~~~~~~~~~~~~~~~

The server maintains connection state through the app context:

- **Connected**: MAPDL instance is active and responding.
- **Disconnected**: No active MAPDL connection.
- **Error**: Last connection attempt failed.

Connection lifecycle
~~~~~~~~~~~~~~~~~~~~

1. **Initialize**: Server starts with no connection.
2. **Connect**: ``launch_mapdl_session`` or ``connect_to_mapdl`` tool creates connection.
3. **Active**: Commands execute in the connected session.
4. **Disconnect**: ``disconnect_from_mapdl`` tool closes connection.
5. **Reset**: Context cleared for new connection.

Error handling in contexts
--------------------------

Errors during context operations follow this pattern:

- They are caught and logged.
- They return error information to the client.
- They do not crash the server.
- They allow for graceful recovery.

Session isolation
-----------------

Each client connection maintains these characteristics:

- It has its own session context.
- It cannot interfere with other client sessions.
- It gets independent access to MAPDL.
- It maintains separate state.

Implementation details
----------------------

See the source code for detailed implementation:

- ``ansys.mapdl.mcp.contexts``: Defines context objects.
- ``ansys.mapdl.mcp.server``: Manages server and context.
- ``ansys.mapdl.mcp.helpers``: Provides context helper functions.

API compatibility
-----------------

The context API is internal to PyMAPDL-MCP and may change without notice.
Use only the documented tool interfaces in your app code.
