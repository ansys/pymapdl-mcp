Tools and capabilities
======================

Available Tools
---------------

PyMAPDL-MCP exposes the following categories of tools:

MAPDL Instance Management
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Launch MAPDL**: Start a new MAPDL instance with custom settings
- **Connect to MAPDL**: Connect to an existing running MAPDL instance
- **List Instances**: Discover MAPDL instances running on the system
- **Check Status**: Get detailed information about MAPDL status
- **Disconnect**: Cleanly close the MAPDL connection

Command Execution
~~~~~~~~~~~~~~~~~~

- **Run MAPDL Command**: Execute individual MAPDL commands
- **Run Multiple Commands**: Execute sequences of commands efficiently
- **Write Comments**: Add comments to the MAPDL session

Data Extraction
~~~~~~~~~~~~~~~

- **Get Status**: Extract comprehensive status information
- **Get Arrays**: Extract numerical data from MAPDL results
- **Get Mesh Information**: Query mesh statistics and properties
- **Get Geometry**: Extract geometry information

Visualization
~~~~~~~~~~~~~~

- **Take Screenshots**: Capture MAPDL graphics window
- **Create Custom Plots**: Generate matplotlib or PyVista visualizations
- **Export Results**: Export data for external visualization

Python Code Execution
~~~~~~~~~~~~~~~~~~~~~~

- **Run Python Code**: Execute arbitrary Python code in the persistent session
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
