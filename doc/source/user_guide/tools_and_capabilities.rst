Tools and capabilities
======================

Tool Availability
-----------------

PyMAPDL-MCP dynamically enables and disables tools based on whether an MAPDL instance is
connected. This keeps the AI assistant's context small when MAPDL is not in use.

**Before connecting to MAPDL**, only the following tools are available:

- ``check_mapdl_installed``
- ``list_mapdl_instances``
- ``connect_to_mapdl``
- ``launch_mapdl_session``
- All ``get_guidelines_for_*`` workflow guidance tools

**After connecting to MAPDL** (via ``connect_to_mapdl`` or ``launch_mapdl_session``), the full
set of tools becomes available. When ``disconnect_from_mapdl`` is called, the MAPDL-specific
tools are hidden again.

.. note::
   When ``--connect-on-startup`` is used, MAPDL is already connected at startup so all tools
   are immediately available (except ``connect_to_mapdl``, ``launch_mapdl_session``, and
   ``disconnect_from_mapdl``, which are locked in that mode).

Available Tools
---------------

PyMAPDL-MCP exposes the following categories of tools:

MAPDL Instance Management
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Launch MAPDL**: Start a new MAPDL instance with custom settings
- **Connect to MAPDL**: Connect to an existing running MAPDL instance
- **List Instances**: Discover MAPDL instances running on the system
- **Check Status**: Get detailed information about MAPDL status *(requires MAPDL connection)*
- **Disconnect**: Cleanly close the MAPDL connection *(requires MAPDL connection)*

Command Execution
~~~~~~~~~~~~~~~~~~

- **Run MAPDL Command**: Execute individual MAPDL commands *(requires MAPDL connection)*
- **Run Multiple Commands**: Execute sequences of commands efficiently *(requires MAPDL connection)*
- **Write Comments**: Add comments to the MAPDL session

Data Extraction
~~~~~~~~~~~~~~~

- **Get Status**: Extract comprehensive status information
- **Get Arrays**: Extract numerical data from MAPDL results
- **Get Mesh Information**: Query mesh statistics and properties
- **Get Geometry**: Extract geometry information

Visualization
~~~~~~~~~~~~~~

- **Take Screenshots**: Capture MAPDL graphics window *(requires MAPDL connection)*
- **Create Custom Plots**: Generate matplotlib or PyVista visualizations *(requires MAPDL connection)*
- **Export Results**: Export data for external visualization

Python Code Execution
~~~~~~~~~~~~~~~~~~~~~~

- **Run Python Code**: Execute arbitrary Python code in the persistent session *(requires MAPDL connection)*
- **Integrate with Data Analysis**: Use NumPy, Pandas, and other Python libraries

Workflow Examples
-----------------

Linear Static Analysis
~~~~~~~~~~~~~~~~~~~~~~

1. Launch MAPDL instance
2. Define geometry (blocks, cylinders, etc.)
3. Define materials and element types
4. Mesh the geometry
5. Apply boundary conditions and loads
6. Run solution
7. Extract and visualize results

Parametric Study
~~~~~~~~~~~~~~~~

1. Set up base MAPDL model
2. Define parameter ranges
3. For each parameter combination:
   - Update parameters
   - Run analysis
   - Extract results
4. Analyze and plot parameter sensitivity

Result Post-Processing
~~~~~~~~~~~~~~~~~~~~~~

1. Run or load MAPDL analysis
2. Extract result data
3. Create custom visualizations
4. Generate analysis reports

Feature Reference
-----------------

See :doc:`../api/tools` for complete documentation of all available tools including parameters and return values.

Best Practices
--------------

See :doc:`best_practices` for recommendations on using PyMAPDL-MCP effectively.
