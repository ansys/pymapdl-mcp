Quick start
===========

Launch PyMAPDL-MCP
------------------

This command is the simplest way to start the MCP server:

.. code-block:: bash

   ansys-mapdl-mcp

It launches the server and waits for connections from MCP clients.

Connect to your IDE or client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyMAPDL-MCP works with multiple MCP-compatible clients. For setup information, see :doc:`ide_configuration`.

- Claude Code (recommended for AI-assisted development)
- Visual Studio Code with Copilot (for Visual Studio Code users)
- Claude Desktop (macOS application)
- Other MCP-compatible clients

Transport options
-----------------

PyMAPDL-MCP supports two transport protocols.

STDIO transport (default)
~~~~~~~~~~~~~~~~~~~~~~~~~

STDIO transport is the default and recommended for local MCP client integration.
It communicates via standard input/output streams, so the MCP client manages the
server process automatically.

Start with STDIO explicitly:

.. code-block:: bash

   python -m ansys.mapdl.mcp --transport stdio

HTTP transport
~~~~~~~~~~~~~~

HTTP transport enables remote access over HTTP with Server-Sent Events (SSE), allowing
web-based clients and remote integrations.

.. note::
   With HTTP transport, you must start the MCP server separately **before** configuring
   your client. Unlike STDIO, the client does not auto-start the server.

Start the HTTP server:

.. code-block:: bash

   # Basic HTTP server (localhost:8080)
   python -m ansys.mapdl.mcp --transport http

   # Custom host and port
   python -m ansys.mapdl.mcp --transport http --http-host 0.0.0.0 --http-port 9000

   # With CORS origins for web clients
   python -m ansys.mapdl.mcp --transport http --cors-origins "http://localhost:3000,https://example.com"

Then configure your MCP client to connect to the HTTP URL, for example in
``.vscode/mcp.json``:

.. code-block:: json

   {
     "servers": {
       "pymapdl": {
         "type": "http",
         "url": "http://127.0.0.1:8080"
       }
     }
   }

.. warning::
   HTTP transport is not encrypted. Use only in trusted networks or behind a
   reverse proxy (for example, Nginx or HAProxy) that provides TLS/SSL.

Command-line reference
----------------------

Transport options
~~~~~~~~~~~~~~~~~

- ``--transport {stdio,http}``: Transport type. Default: ``stdio``

MAPDL connection options
~~~~~~~~~~~~~~~~~~~~~~~~

These options work with both STDIO and HTTP transports.

- ``--ip``: MAPDL IP address or hostname. Default: ``127.0.0.1``
- ``--port``: MAPDL gRPC port. Default: ``50052`` (range: 1-65535)
- ``--connect-on-startup``: Automatically connect to MAPDL when the server starts

.. code-block:: bash

   # Connect to MAPDL on startup
   python -m ansys.mapdl.mcp --connect-on-startup --ip 192.168.1.100 --port 50053

.. warning::
   When ``--connect-on-startup`` is used, the connection is locked. The
   ``launch_mapdl_session``, ``connect_to_mapdl``, and ``disconnect_from_mapdl``
   tools are turned off.

HTTP-specific options
~~~~~~~~~~~~~~~~~~~~~

- ``--http-host``: HTTP server host address. Default: ``127.0.0.1``
- ``--http-port``: HTTP server port. Default: ``8080`` (range: 1-65535)
- ``--cors-origins``: Comma-separated list of allowed CORS origins (optional)

Special environment options
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``--on-aali``: Specifies that the server is running on an AALI environment.
  This turns off tools that are not compatible with AALI.

Basic workflow
--------------

Starting a MAPDL instance
~~~~~~~~~~~~~~~~~~~~~~~~~

There are three ways to connect to MAPDL once the MCP server is running.

**Option 1: launch a new MAPDL instance (recommended)**

Ask your AI assistant to use the ``launch_mapdl_session`` tool:

   *"Launch a new MAPDL instance"*

   *"Launch MAPDL with 4 processors in /tmp/mapdl_work"*

This starts a new MAPDL process and connects to it automatically. It lets you
specify custom settings (number of processors, working directory, etc.) without
any manual setup.

**Option 2: connect to an existing instance**

Ask your AI assistant to use the ``connect_to_mapdl`` tool:

   *"Connect to MAPDL on localhost port 50052"*

   *"Connect to MAPDL on 192.168.1.100 port 50053"*

You can first ask it to run ``list_mapdl_instances`` to discover what is running.
This option is useful for connecting to different instances during a session or
when MAPDL is already running on a remote machine.

**Option 3: auto-connect on server startup**

Pass ``--connect-on-startup`` when starting the MCP server:

.. code-block:: bash

   python -m ansys.mapdl.mcp --connect-on-startup --ip 127.0.0.1 --port 50052

.. warning::
   When ``--connect-on-startup`` is used, the connection is locked. The
   ``launch_mapdl_session``, ``connect_to_mapdl``, and ``disconnect_from_mapdl``
   tools are turned off.

Running commands and extracting results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once MAPDL is connected, you can use MCP tools to:

1. Launch MAPDL instances.
2. Execute MAPDL commands through PyMAPDL.
3. Retrieve and analyze results.
4. Generate plots and screenshots.
5. Manage the MAPDL session lifecycle.


Example use cases
~~~~~~~~~~~~~~~~~

- Run parametric studies with AI guidance.
- Analyze FEA results automatically.
- Generate documentation from simulation results.
- Debug MAPDL scripts with AI assistance.

Next steps
----------

- For an overview of available tools, see :doc:`../user_guide/overview` 
- Check :doc:`../api/tools` for the complete API reference
- Browse :doc:`../examples/index` for practical examples
- See :doc:`../user_guide/docker` for containerized deployment
