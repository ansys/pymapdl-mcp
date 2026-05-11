Tools and capabilities
======================

Tool availability
-----------------

PyMAPDL-MCP dynamically enables and disables tools based on whether an MAPDL instance is
connected. This keeps the AI assistant's context small when MAPDL is not in use.

**Before connecting to MAPDL**, only the following tools are available:

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

**After connecting to MAPDL** (via ``connect_to_mapdl`` or ``launch_mapdl_session``), all tools
become available. When ``disconnect_from_mapdl`` is called, the MAPDL-specific tools are hidden
again.

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
     - Create custom ``matplotlib`` or ``pyvista`` plots

.. note::
   When ``--connect-on-startup`` is used, MAPDL is already connected at startup so all tools
   are immediately available (except ``connect_to_mapdl``, ``launch_mapdl_session``, and
   ``disconnect_from_mapdl``, which are locked in that mode).

Using the tools
---------------

Running MAPDL commands
~~~~~~~~~~~~~~~~~~~~~~

Use ``run_mapdl_command`` for single commands:

   *"Run VPLOT on the MAPDL instance"*

For multiple commands, use ``run_multiple_commands``, which uses MAPDL's ``input_strings``
method for batch execution. This is significantly faster than running commands one by one:

   *"Run these commands: /PREP7, ET,1,SOLID185, MP,EX,1,200E9"*

Custom Python code execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``run_python_code`` to execute arbitrary Python and PyMAPDL code in a persistent session:

   *"Execute this Python code: displacements = mapdl.get_array('NODE', item1='U', it1num='Y'); print(f'Max displacement: {displacements.max()}')"*

This is useful for:

- Custom data processing and analysis
- Advanced PyVista visualizations
- NumPy/Pandas data manipulation
- Complex computations not available through direct MAPDL commands

Creating custom plots
~~~~~~~~~~~~~~~~~~~~~

Use ``custom_plot`` to create ``matplotlib`` or ``pyvista`` plots that are not available in MAPDL's
native plotting:

   *"Create a ``matplotlib`` plot showing nodal displacements vs node number"*

.. important::
   ``custom_plot`` is for plots that MAPDL cannot produce natively. For standard MAPDL plots
   (``APLOT``, ``LPLOT``, ``KPLOT``, ``PLNSOL``, etc.), use the MAPDL commands together with
   the ``screenshot`` tool.

Capturing plots
~~~~~~~~~~~~~~~

After running a MAPDL plot command, use the ``screenshot`` tool to capture the graphics window:

   *"Show a plot of the geometry"*

   *"Capture the current MAPDL plot"*

It returns the image directly so the AI assistant can display it inline. Works with all MAPDL
native plot commands, including:

- Geometry: ``APLOT``, ``LPLOT``, ``KPLOT``, ``VPLOT``
- Mesh: ``EPLOT``, ``NPLOT``
- Post-processing: ``PLNSOL``, ``PLESOL``, ``PLDISP``
- **Export results**: Export data for external visualization

Python code execution
~~~~~~~~~~~~~~~~~~~~~

- **Run Python code**: Execute arbitrary Python code in the persistent session *(requires MAPDL connection)*
- **Integrate with data analysis**: Use NumPy, Pandas, and other Python libraries

Workflow examples
-----------------

Linear static analysis
~~~~~~~~~~~~~~~~~~~~~~

1. Launch MAPDL instance
2. Define geometry (blocks, cylinders, etc.)
3. Define materials and element types
4. Mesh the geometry
5. Apply boundary conditions and loads
6. Run solution
7. Extract and visualize results

Parametric study
~~~~~~~~~~~~~~~~

1. Set up base MAPDL model
2. Define parameter ranges
3. For each parameter combination:
   - Update parameters
   - Run analysis
   - Extract results
4. Analyze and plot parameter sensitivity

Result post-processing
~~~~~~~~~~~~~~~~~~~~~~

1. Run or load MAPDL analysis
2. Extract result data
3. Create custom visualizations
4. Generate analysis reports

Feature reference
-----------------

See :doc:`../api/tools` for complete documentation of all available tools including parameters and return values.

Best practices
--------------

See :doc:`best_practices` for recommendations on using PyMAPDL-MCP effectively.
