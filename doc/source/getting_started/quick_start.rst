Quick start
===========

Launch PyMAPDL-MCP
------------------

This command is the simplest way to start the MCP server:

.. code-block:: bash

   ansys-mapdl-mcp

It launches the server and waits for connections from MCP clients.

Connect to your IDE or client
-----------------------------

PyMAPDL-MCP works with multiple MCP-compatible clients. For setup information, see :doc:`ide_configuration`.

- Claude Code (recommended for AI-assisted development)
- Visual Studio Code with Copilot (for Visual Studio Code users)
- Claude Desktop (macOS application)
- Other MCP-compatible clients

Follow the basic workflow
-------------------------

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


Consider example use cases
--------------------------

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
