Tools reference
================

This document provides complete reference documentation for all PyMAPDL-MCP tools.

Tool availability
-----------------

PyMAPDL-MCP dynamically enables and disables tools based on the MAPDL connection state.
Tools tagged with ``requires_mapdl`` are hidden at startup and only become visible once
MAPDL is connected via ``connect_to_mapdl`` or ``launch_mapdl_session``. They are hidden
again when ``disconnect_from_mapdl`` is called.

See :doc:`../user_guide/tools_and_capabilities` for the full breakdown.

Instance management tools
--------------------------

``launch_mapdl_session``
~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: launch a new MAPDL instance

**Parameters**:

- ``exec_file`` (str, optional): Path to MAPDL executable. If None, PyMAPDL auto-detects.
- ``port`` (int, optional): gRPC port for MAPDL. If None, uses default.
- ``run_location`` (str, optional): Directory where MAPDL runs. If None, uses temporary directory.
- ``nproc`` (int, optional): Number of processors to use. Default is None (MAPDL decides).
- ``additional_switches`` (str, optional): Additional command-line switches for MAPDL.

**Returns**: launch status message with MAPDL version and connection information

**Example**:

.. code-block:: python

    result = launch_mapdl_session(
        exec_file=None,
        nproc=4,
        additional_switches="-check"
    )

``connect_to_mapdl``
~~~~~~~~~~~~~~~~~~~~

**Description**: connect to an existing running MAPDL instance

**Parameters**:

- ``ip`` (str, optional): IP address where MAPDL is running. Default: "localhost"
- ``port`` (int, optional): gRPC port where MAPDL is listening. Default: 50052

**Returns**: connection status message with MAPDL version information

**Example**:

.. code-block:: python

    result = connect_to_mapdl(ip="localhost", port=50052)

``list_mapdl_instances``
~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: list all MAPDL instances running on the local machine

**Returns**: formatted table with instance information (name, status, port, IP, PID, directory)

**Example**:

.. code-block:: python

    instances = list_mapdl_instances()

``check_mapdl_status``
~~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL.

**Description**: get comprehensive MAPDL status information

**Returns**: a JSON string containing:

- connection info (version, port, IP, directory, ``is_alive``)
- information (title, jobname, routine, units, etc.)
- geometry statistics
- post-processing data
- mesh statistics

**Example**:

.. code-block:: python

    status = check_mapdl_status()

``disconnect_from_mapdl``
~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL. It is also turned off when
   ``--connect-on-startup`` is used.

**Description**: disconnect from the currently connected MAPDL instance

**Returns**: disconnection status message

**Example**:

.. code-block:: python

    result = disconnect_from_mapdl()

``check_mapdl_installed``
~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: check if MAPDL is installed on the system

**Returns**: status message indicating installation status

**Example**:

.. code-block:: python

    status = check_mapdl_installed()

Command execution tools
-----------------------

``run_mapdl_command``
~~~~~~~~~~~~~~~~~~~~~


.. note::
   This tool is only available when connected to MAPDL.

**Description**: execute a single MAPDL command

**Parameters**:

- ``cmd`` (str): The MAPDL command to execute

**Returns**: command execution result

**Example**:

.. code-block:: python

    result = run_mapdl_command("FINISH")

``run_multiple_commands``
~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   This tool is only available when connected to MAPDL and is turned off on AALI environments.

**Description**: execute multiple MAPDL commands efficiently using batch mode

**Parameters**:

- ``commands`` (list[str]): List of MAPDL commands to execute

**Returns**: execution result with summary of commands executed

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

**Description**: execute arbitrary Python code in the persistent session

**Parameters**:

- ``code`` (str): Python code to execute
- ``timeout`` (int, optional): Maximum execution time in seconds. Default: 60

**Returns**: execution result or error message

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

**Description**: capture a screenshot of the MAPDL graphics window

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

**Description**: create a custom ``matplotlib`` or ``pyvista`` visualization

**Parameters**:

- ``plot_code`` (str): Python code to create the plot
- ``plot_type`` (str, optional): ``matplotlib`` or ``pyvista``. Default: ``matplotlib``
- ``timeout`` (int, optional): Maximum execution time in seconds. Default: 60

**Returns**: list containing:

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

**Description**: get general MAPDL simulation workflow guidelines

**Returns**: overview of the general simulation process

``get_guidelines_for_general_rules``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: get general rules and best practices for MAPDL workflows

**Returns**: general guidelines for high-quality simulations

``get_guidelines_for``
~~~~~~~~~~~~~~~~~~~~~~

**Description**: get MAPDL simulation guidelines for a specific topic using the unified tool ``get_guidelines_for(content)``.

**Parameters**:

- ``content`` (str): One of the following values: ``"workflow"``, ``"geometry"``, ``"elements"``, ``"materials"``, ``"mesh"``, ``"boundary_conditions"``, ``"solution"``, ``"postprocessing"``, ``"general"``.

**Returns**: guideline text for the requested topic.

**Example**::

    result = get_guidelines_for(content="mesh")

This unified tool replaces the previous per-topic guideline tools (for example, ``get_guidelines_for_preprocessing_mesh``) to reduce the number of registered tools and simplify client usage.

``get_guidelines_for_solution_phase``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: get guidelines for the solution phase

**Returns**: guidelines for configuring and running the solution

``get_guidelines_for_postprocessing_phase``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: get guidelines for postprocessing results

**Returns**: guidelines for extracting and visualizing results

Tool return values
------------------

Most tools return structured information:

**Success**: text describing the result or status

**Error**: detailed error message including:

- Error type
- Description of what went wrong
- Suggested corrective action

**Data**: structured data (JSON, arrays, etc.) depending on the tool

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

- :doc:`../user_guide/tools_and_capabilities` for conceptual overview
- :doc:`../examples/index` for practical usage examples
- :doc:`../user_guide/best_practices` for usage recommendations
