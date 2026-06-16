Tools reference
================

This page provides reference documentation for all PyMAPDL-MCP tools.

Tool availability
-----------------

PyMAPDL-MCP dynamically enables and disables tools based on the MAPDL connection state.
Tools tagged with ``requires_mapdl`` are hidden at startup and only become visible once
MAPDL is connected with the ``connect_to_mapdl`` or ``launch_mapdl_session`` tool. MAPDL
tools are hidden again when ``disconnect_from_mapdl`` is called.

For more information, see :doc:`../user_guide/tools_and_capabilities`.

Tool sets
---------

Tools are organized into logical tool sets for better organization and accessibility. The
available tool sets are exposed through the ``toolsets://definition`` resource, which provides
metadata about each set including its name, description, and the tools it contains.

**Available tool sets**:

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Tool set
     - Purpose
     - Tools included

   * - ``session_management``
     - Manage MAPDL connections and discover instances
     - ``check_mapdl_installed``, ``check_mapdl_status``, ``launch_mapdl_session``,
       ``connect_to_mapdl``, ``disconnect_from_mapdl``, ``list_mapdl_instances``

   * - ``command_execution``
     - Execute MAPDL commands and scripts
     - ``run_mapdl_command``, ``run_multiple_commands``, ``run_python_code``

   * - ``visualization``
     - Visualization and post-processing of results
     - ``screenshot``, ``custom_plot``

   * - ``python_execution``
     - Execute arbitrary Python and PyMAPDL code
     - ``run_python_code``

The ``list_tool_sets()`` resource function returns the complete tool set definitions,
allowing client applications to discover and organize available capabilities.

Instance management tools
-------------------------

``launch_mapdl_session``
~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Launch a new MAPDL instance. This tool starts a new MAPDL process and
automatically establishes a connection to it for immediate use.

**Parameters**:

- ``exec_file`` (str, default: None): Path to the MAPDL executable. If ``None``, PyMAPDL auto-detects.
- ``port`` (int, default: None): gRPC port for MAPDL. If ``None``, the default port is used.
- ``run_location`` (str, default: None): Directory where MAPDL runs. If ``None``, the temporary
  directory is used.
- ``nproc`` (int, default: None): Number of processors to use. If ``None``, MAPDL decides.
- ``additional_switches`` (str, optional): Additional command-line switches for MAPDL.

**Returns**: Launch status message with MAPDL version and connection information.

**Example**:

.. code-block:: python

    result = launch_mapdl_session(
        exec_file=None,
        nproc=4,
        additional_switches="-check"
    )

``connect_to_mapdl``
~~~~~~~~~~~~~~~~~~~~

**Description**: Connect to an existing running MAPDL instance.

**Parameters**:

- ``ip`` (str, default: "localhost"): IP address where MAPDL is running.
- ``port`` (int, default: 50052): gRPC port where MAPDL is listening.

**Returns**: Connection status message with MAPDL version information.

**Example**:

.. code-block:: python

    result = connect_to_mapdl(ip="localhost", port=50052)

``list_mapdl_instances``
~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: List all MAPDL instances running on the local machine.

**Returns**: Formatted table with instance information (name, status, port, IP, PID, and directory).

**Example**:

.. code-block:: python

    instances = list_mapdl_instances()

``check_mapdl_status``
~~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL.

**Description**: Get comprehensive MAPDL status information.

**Returns**: JSON string containing:

- Connection information (version, port, IP, directory, ``is_alive``)
- Session information (title, jobname, routine, units, and more)
- Geometry statistics
- Postprocessing data
- Mesh statistics

**Example**:

.. code-block:: python

    status = check_mapdl_status()

``disconnect_from_mapdl``
~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL. It is also turned off when
   ``--connect-on-startup`` is used.

**Description**: Disconnect from the currently connected MAPDL instance.

**Returns**: Disconnection status message.

**Example**:

.. code-block:: python

    result = disconnect_from_mapdl()

``check_mapdl_installed``
~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Check if MAPDL is installed on the system.

**Returns**: Status message indicating installation status.

**Example**:

.. code-block:: python

    status = check_mapdl_installed()

Command execution tools
-----------------------

``run_mapdl_command``
~~~~~~~~~~~~~~~~~~~~~


.. note::
   This tool is only available when connected to MAPDL.

**Description**: Execute a single MAPDL command.

**Parameters**:

- ``cmd`` (str): MAPDL command to execute.

**Returns**: Command execution result.

**Example**:

.. code-block:: python

    result = run_mapdl_command("FINISH")

``run_multiple_commands``
~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL and is turned off on AALI environments.

**Description**: Execute multiple MAPDL commands efficiently using batch mode.

**Parameters**:

- ``commands`` (list[str]): List of MAPDL commands to execute.

**Returns**: Execution result with summary of commands executed.

**Example**:

.. code-block:: python

    result = run_multiple_commands([
        "FINISH",
        "/PREP7",
        "ET,1,SOLID185"
    ])

Python code execution tools
----------------------------

``run_python_code``
~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL.

**Description**: Execute arbitrary Python code in the persistent session.

**Parameters**:

- ``code`` (str): Python code to execute.
- ``timeout`` (int, default: 60): Maximum execution time in seconds.

**Returns**: Execution result or error message.

**Example**:

.. code-block:: python

    code = '''
    displacements = mapdl.get_array("NODE", item1="U", it1num="Y")
    print(f"Max displacement: {displacements.max()}")
    '''
    result = run_python_code(code)

Visualization tools
-------------------

``screenshot``
~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL and is turned off on AALI environments.

**Description**: Capture a screenshot of the MAPDL graphics window.

**Returns**: list containing:

- TextContent with screenshot path
- ImageContent with base64-encoded image data

**Example**:

.. code-block:: python

    result = screenshot()

``custom_plot``
~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL and is turned off on AALI environments.

**Description**: Create a custom Matplotlib or PyVista visualization.

**Parameters**:

- ``plot_code`` (str): Python code to create the plot.
- ``plot_type`` (str, default: "matplotlib"): Type of plot to create. Options are ``"matplotlib"`` and ``"pyvista"``.
- ``timeout`` (int, default: 60): Maximum execution time in seconds.

**Returns**: List containing:

- TextContent with status message
- ImageContent with base64-encoded image data

**Example**:

.. code-block:: python

    plot_code = '''
    import matplotlib.pyplot as plt
    import numpy as np

    displacements = mapdl.get_array("NODE", item1="U", it1num="Y")

    plt.figure(figsize=(10, 6))
    plt.plot(displacements)
    plt.xlabel("Node Number")
    plt.ylabel("Displacement (m)")
    plt.title("Custom Displacement Plot")
    plt.grid(True)

    result = save_matplotlib_plot(dpi=150)
    print(result)
    '''
    result = custom_plot(plot_code, plot_type="matplotlib")

Guidelines and documentation tools
----------------------------------

``get_guidelines_for_workflow_overview``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get general MAPDL simulation workflow guidelines.

**Returns**: Overview of the general simulation process.

``get_guidelines_for_general_rules``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get general rules and best practices for MAPDL workflows.

**Returns**: General guidelines for high-quality simulations.

``get_guidelines_for``
~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get MAPDL simulation guidelines for a specific topic using the unified tool ``get_guidelines_for(content)``.

**Parameters**:

- ``content`` (str): Type of topic. Options are ``"workflow"``, ``"geometry"``, ``"elements"``, ``"materials"``, ``"mesh"``, ``"boundary_conditions"``, ``"solution"``, ``"postprocessing"``, and ``"general"``.

**Returns**: Guideline text for the requested topic.

**Example**::

    result = get_guidelines_for(content="mesh")

This unified tool replaces the previous per-topic guideline tools (for example, ``get_guidelines_for_preprocessing_mesh``)
to reduce the number of registered tools and simplify client usage.

``get_guidelines_for_solution_phase``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get guidelines for the solution phase.

**Returns**: Guidelines for configuring and running the solution.

``get_guidelines_for_postprocessing_phase``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get guidelines for postprocessing results.

**Returns**: Guidelines for extracting and visualizing results.

Tool return values
------------------

Most tools return structured information:

**Success**: Text describing the result or status.

**Error**: Detailed error message including:

- Error type
- Description of what went wrong
- Suggested corrective action

**Data**: Structured data (such as JSON and arrays), depending on the tool.

Error handling
--------------

Always check tool results for errors:

.. code-block:: python

    result = run_mapdl_command("INVALID_COMMAND")
    # Check if result contains error information
    if "error" in result.lower():
        print("Command failed:", result)
    else:
        print("Command succeeded:", result)

See also
--------

- For a conceptual overview, see :doc:`../user_guide/tools_and_capabilities`.
- For practical usage examples, see :doc:`../examples/index`.
- For usage recommendations, see :doc:`../user_guide/best_practices`.
