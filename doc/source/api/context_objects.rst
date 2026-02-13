Context Objects
================

This document describes the internal context objects used by PyMAPDL-MCP.

Application Context
-------------------

The Application Context maintains the state of the PyMAPDL-MCP server.

**Key Attributes**:

- ``mapdl``: The current PyMAPDL instance (if connected)
- ``config``: Configuration settings
- ``logger``: Logger instance

**Responsibilities**:

- Managing the MAPDL connection lifecycle
- Storing session state
- Providing access to PyMAPDL functionality

Tool Context
------------

Each tool receives a Context object that provides:

- Access to the application context
- Request/response handling
- Logging capabilities

**Usage in Tools**:

.. code-block:: python

    def my_tool(ctx: Context, parameter: str) -> str:
        # Access the MAPDL instance
        mapdl = ctx.application_context.mapdl

        # Perform operations
        result = mapdl.prep7()

        return f"Result: {result}"

Connection Management
---------------------

Connection State
~~~~~~~~~~~~~~~~

The server maintains connection state through the Application Context:

- **Connected**: MAPDL instance is active and responding
- **Disconnected**: No active connection
- **Error**: Last connection attempt failed

Connection Lifecycle
~~~~~~~~~~~~~~~~~~~~

1. **Initialize**: Server starts with no connection
2. **Connect**: ``launch_mapdl`` or ``connect_to_mapdl`` creates connection
3. **Active**: Commands execute in the connected session
4. **Disconnect**: ``disconnect_from_mapdl`` closes connection
5. **Reset**: Context cleared for new connection

Error Handling in Contexts
--------------------------

Errors during context operations:

- Are caught and logged
- Return error information to the client
- Do not crash the server
- Allow for graceful recovery

Session Isolation
-----------------

Each client connection:

- Has its own session context
- Cannot interfere with other client sessions
- Gets independent access to MAPDL
- Maintains separate state

Implementation Details
----------------------

See the source code for detailed implementation:

- ``ansys.mapdl.mcp.contexts``: Context definitions
- ``ansys.mapdl.mcp.server``: Server and context management
- ``ansys.mapdl.mcp.helpers``: Context helper functions

API Compatibility
-----------------

The context API is internal to PyMAPDL-MCP and may change without notice.
Application code should use only the documented tool interfaces.
