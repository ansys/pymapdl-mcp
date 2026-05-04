Tools Reference
================

This document provides complete reference documentation for all PyMAPDL-MCP tools.

Tool Availability
-----------------

PyMAPDL-MCP dynamically enables and disables tools based on the MAPDL connection state.
Tools tagged with ``requires_mapdl`` are hidden at startup and only become visible once
MAPDL is connected via ``connect_to_mapdl`` or ``launch_mapdl_session``. They are hidden
again when ``disconnect_from_mapdl`` is called.

See :doc:`../user_guide/tools_and_capabilities` for the full breakdown.

Instance Management Tools
--------------------------

launch_mapdl_session
~~~~~~~~~~~~~~~~~~~~

**Description**: Launch a new MAPDL instance

**Parameters**:

- ``exec_file`` (str, optional): Path to MAPDL executable. If None, PyMAPDL will auto-detect.
- ``port`` (int, optional): gRPC port for MAPDL. If None, uses default.
- ``run_location`` (str, optional): Directory where MAPDL will run. If None, uses temporary directory.
- ``nproc`` (int, optional): Number of processors to use. Default is None (MAPDL decides).
- ``additional_switches`` (str, optional): Additional command-line switches for MAPDL.

**Returns**: Launch status message with MAPDL version and connection information

**Example**:

.. code-block:: python

    result = launch_mapdl_session(
        exec_file=None,
        nproc=4,
        additional_switches="-check"
    )

connect_to_mapdl
~~~~~~~~~~~~~~~~

**Description**: Connect to an existing running MAPDL instance

**Parameters**:

- ``ip`` (str, optional): IP address where MAPDL is running. Default: "localhost"
- ``port`` (int, optional): gRPC port where MAPDL is listening. Default: 50052

**Returns**: Connection status message with MAPDL version information

**Example**:

.. code-block:: python

    result = connect_to_mapdl(ip="localhost", port=50052)

list_mapdl_instances
~~~~~~~~~~~~~~~~~~~~

**Description**: List all MAPDL instances running on the local machine

**Returns**: Formatted table with instance information (name, status, port, IP, PID, directory)

**Example**:

.. code-block:: python

    instances = list_mapdl_instances()

check_mapdl_status
~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL.

**Description**: Get comprehensive MAPDL status information

**Returns**: JSON string containing:

- connection info (version, port, IP, directory, is_alive)
- information (title, jobname, routine, units, etc.)
- geometry statistics
- post-processing data
- mesh statistics

**Example**:

.. code-block:: python

    status = check_mapdl_status()

disconnect_from_mapdl
~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL. It is also disabled when
   ``--connect-on-startup`` is used.

**Description**: Disconnect from the currently connected MAPDL instance

**Returns**: Disconnection status message

**Example**:

.. code-block:: python

    result = disconnect_from_mapdl()

check_mapdl_installed
~~~~~~~~~~~~~~~~~~~~~

**Description**: Check if MAPDL is installed on the system

**Returns**: Status message indicating installation status

**Example**:

.. code-block:: python

    status = check_mapdl_installed()

Command Execution Tools
-----------------------

run_mapdl_command
~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL.

**Description**: Execute a single MAPDL command

**Parameters**:

- ``cmd`` (str): The MAPDL command to execute

**Returns**: Command execution result

**Example**:

.. code-block:: python

    result = run_mapdl_command("FINISH")

run_multiple_commands
~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL and is disabled on AALI environments.

**Description**: Execute multiple MAPDL commands efficiently using batch mode

**Parameters**:

- ``commands`` (list[str]): List of MAPDL commands to execute

**Returns**: Execution result with summary of commands executed

**Example**:

.. code-block:: python

    result = run_multiple_commands([
        "FINISH",
        "/PREP7",
        "ET,1,SOLID185"
    ])

Python Code Execution Tools
----------------------------

run_python_code
~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL.

**Description**: Execute arbitrary Python code in the persistent session

**Parameters**:

- ``code`` (str): Python code to execute
- ``timeout`` (int, optional): Maximum execution time in seconds. Default: 60

**Returns**: Execution result or error message

**Example**:

.. code-block:: python

    code = '''
    displacements = mapdl.get_array("NODE", item1="U", it1num="Y")
    print(f"Max displacement: {displacements.max()}")
    '''
    result = run_python_code(code)

Visualization Tools
-------------------

screenshot
~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL and is disabled on AALI environments.

**Description**: Capture a screenshot of the MAPDL graphics window

**Returns**: List containing:

- TextContent with screenshot file path
- ImageContent with base64-encoded image data

**Example**:

.. code-block:: python

    result = screenshot()

custom_plot
~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL and is disabled on AALI environments.

**Description**: Create a custom matplotlib or PyVista visualization

**Parameters**:

- ``plot_code`` (str): Python code to create the plot
- ``plot_type`` (str, optional): "matplotlib" or "pyvista". Default: "matplotlib"
- ``timeout`` (int, optional): Maximum execution time in seconds. Default: 60

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

Guidelines and Documentation Tools
----------------------------------

get_guidelines_for_workflow_overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get general MAPDL simulation workflow guidelines

**Returns**: Overview of the general simulation process

get_guidelines_for_general_rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get general rules and best practices for MAPDL workflows

**Returns**: General guidelines for high-quality simulations

get_guidelines_for_preprocessing_*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get guidelines for specific preprocessing phases

Available topics:

- ``get_guidelines_for_preprocessing_geometry``: Geometry and meshing
- ``get_guidelines_for_preprocessing_elements``: Element type selection
- ``get_guidelines_for_preprocessing_materials``: Material properties
- ``get_guidelines_for_preprocessing_mesh``: Mesh generation
- ``get_guidelines_for_preprocessing_boundary_conditions``: Boundary conditions and loads

**Returns**: Specific guidelines for the requested phase

get_guidelines_for_solution_phase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get guidelines for the solution phase

**Returns**: Guidelines for configuring and running the solution

get_guidelines_for_postprocessing_phase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Get guidelines for postprocessing results

**Returns**: Guidelines for extracting and visualizing results

Tool Return Values
------------------

Most tools return structured information:

**Success**: Text describing the result or status

**Error**: Detailed error message including:

- Error type
- Description of what went wrong
- Suggested corrective action

**Data**: Structured data (JSON, arrays, etc.) depending on the tool

Error Handling
--------------

Always check tool results for errors:

.. code-block:: python

    result = run_mapdl_command("INVALID_COMMAND")
    # Check if result contains error information
    if "error" in result.lower():
        print("Command failed:", result)
    else:
        print("Command succeeded:", result)

See Also
--------

- :doc:`../user_guide/tools_and_capabilities` for conceptual overview
- :doc:`../examples/index` for practical usage examples
- :doc:`../user_guide/best_practices` for usage recommendations
