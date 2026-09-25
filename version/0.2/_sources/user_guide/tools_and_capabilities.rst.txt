Tools and capabilities
======================

Tool availability
-----------------

PyMAPDL-MCP dynamically enables and disables tools based on whether an MAPDL instance is
connected. This keeps the AI assistant's context small when MAPDL is not in use.

**Before connecting to MAPDL**, you can access these tools:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Tool
     - Description
   * - ``check_mapdl_installed``
     - Check if MAPDL is installed on the system
   * - ``list_mapdl_instances``
     - Discover running MAPDL instances
   * - ``connect_to_mapdl``
     - Connect to an existing MAPDL instance
   * - ``launch_mapdl_session``
     - Launch and connect to a new MAPDL instance
   * - ``get_guidelines_for``
     - Workflow guidance and best-practice context tool

**After connecting to MAPDL**, you gain access to the full set of tools. When you call the
``disconnect_from_mapdl`` tool, the MAPDL-specific tools become unavailable.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Tool
     - Description
   * - ``check_mapdl_status``
     - Get comprehensive MAPDL status
   * - ``run_mapdl_command``
     - Execute a single MAPDL command
   * - ``run_multiple_commands``
     - Execute multiple MAPDL commands in batch
   * - ``disconnect_from_mapdl``
     - Disconnect from the MAPDL instance
   * - ``screenshot``
     - Capture the MAPDL graphics window
   * - ``run_python_code``
     - Execute Python/PyMAPDL code in a persistent session
   * - ``custom_plot``
     - Create custom matplotlib or PyVista plots

.. note::
   When you use ``--connect-on-startup``, MAPDL connects at startup and all tools are immediately
   available (except ``connect_to_mapdl``, ``launch_mapdl_session``, and ``disconnect_from_mapdl``,
   which are locked).

Using the tools
---------------

Running MAPDL commands
~~~~~~~~~~~~~~~~~~~~~~

Use ``run_mapdl_command`` for single commands:

*"Run VPLOT on the MAPDL instance."*

For multiple commands, use ``run_multiple_commands``, which uses MAPDL's ``input_strings``
method for batch execution. This is significantly faster than running commands one by one:

*"Run these commands: /PREP7, ET,1,SOLID185, MP,EX,1,200E9."*

Custom Python code execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``run_python_code`` to execute arbitrary Python and PyMAPDL code in a persistent session:

*"Execute this Python code: displacements = mapdl.get_array('NODE', item1='U', it1num='Y'); print(f'Max displacement: {displacements.max()}')."*

This is useful for:

- Custom data processing and analysis
- Advanced PyVista visualizations
- NumPy/Pandas data manipulation
- Complex computations not available through direct MAPDL commands

Creating custom plots
~~~~~~~~~~~~~~~~~~~~~

Use ``custom_plot`` to create Matplotlib or PyVista plots that are not available in MAPDL's
native plotting:

*"Create a Matplotlib plot showing nodal displacements versus node number."*

.. important::
   ``custom_plot`` is for plots that MAPDL cannot produce natively. For standard MAPDL plots
   (``APLOT``, ``LPLOT``, ``KPLOT``, ``PLNSOL``, etc.), use the MAPDL commands together with
   the ``screenshot`` tool.

Capturing plots
~~~~~~~~~~~~~~~

After running a MAPDL plot command, use the ``screenshot`` tool to capture the graphics window:

*"Show a plot of the geometry."*

*"Capture the current MAPDL plot."*

It returns the image directly so the AI assistant can display it inline. Works with all MAPDL
native plot commands, including:

- Geometry: ``APLOT``, ``LPLOT``, ``KPLOT``, ``VPLOT``
- Mesh: ``EPLOT``, ``NPLOT``
- Post-processing: ``PLNSOL``, ``PLESOL``, ``PLDISP``

Python code execution
~~~~~~~~~~~~~~~~~~~~~

- Run Python code: Execute arbitrary Python code in the persistent session *(requires MAPDL connection)*.
- Integrate with data analysis: Use NumPy, Pandas, and other Python libraries.


Workflow examples
-----------------

Linear static analysis
~~~~~~~~~~~~~~~~~~~~~~

#. Launch MAPDL instance.
#. Define geometry (blocks, cylinders, and so on).
#. Define materials and element types.
#. Mesh the geometry.
#. Apply boundary conditions and loads.
#. Run solution.
#. Extract and visualize results.

Parametric study
~~~~~~~~~~~~~~~~

#. Set up the base MAPDL model.
#. Define parameter ranges.
#. Update parameters, run analysis, and extract results for each parameter combination.
#. Analyze and plot parameter sensitivity.

Result postprocessing
~~~~~~~~~~~~~~~~~~~~~

#. Run or load MAPDL analysis.
#. Extract result data.
#. Create custom visualizations.
#. Generate analysis reports.

Feature reference
-----------------

For the documentation of all available tools, including parameters and return values, see :doc:`../api/tools`.

Best practices
--------------

For recommendations on using PyMAPDL-MCP effectively, see :doc:`best_practices`.
