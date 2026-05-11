Best practices
==============

Session management
------------------

**Reuse MAPDL instances**
    Keep the same MAPDL instance open for multiple operations to improve performance.
    Only restart when necessary (for example, to clear the database).

**Clean shutdown**
    Always disconnect properly from MAPDL instances to free resources.

**Error handling**
    Check tool results for errors and handle them gracefully in your workflow.

Command execution
-----------------

**Batch commands**
    Use ``run_multiple_commands`` instead of individual commands for better performance.

**Verify state**
    Use ``check_mapdl_status`` periodically to verify the session state.

**Use Comments**
    Add comments in the MAPDL session to document your workflow for clarity.

Data handling
-------------

**Extract efficiently**
    Extract only the data you need rather than loading entire result sets.

**Cache results**
    Store extracted data in Python variables to avoid repeated extraction.

**Validate data**
    Check that extracted data makes physical sense (for example, positive stresses, reasonable displacements).

Visualization
-------------

**Screenshots after key steps**
    Take screenshots after geometry definition, meshing, and solving to verify progress.

**Custom plots for analysis**
    Use custom ``matplotlib`` plots for detailed analysis beyond MAPDL's built-in capabilities.

**Export for documentation**
    Save high-quality plots for reports and documentation.

Workflow design
---------------

**Modular workflows**
    Break complex analyses into smaller, independent steps.

**Error recovery**
    Design workflows that can recover from errors without complete restart.

**Progress feedback**
    Include status updates and progress indicators in long-running workflows.

**Parameter validation**
    Validate all input parameters before sending to MAPDL.

Performance
-----------

**Minimize restarts**
    Avoid restarting MAPDL unless absolutely necessary.

**Efficient meshing**
    Use adaptive meshing and mesh refinement selectively.

**Result processing**
    Process results in Python rather than repeatedly querying MAPDL.

**Parallel operations**
    Consider launching multiple MAPDL instances for independent analyses.

Common patterns
---------------

**Parameter sweep**
    1. Define parameter ranges
    2. Clear results between runs
    3. Update parameters
    4. Run analysis
    5. Extract results
    6. Aggregate results across runs

**Convergence study**
    1. Run analysis with coarse mesh
    2. Refine mesh selectively
    3. Re-run analysis
    4. Compare results
    5. Repeat until converged

**Sensitivity analysis**
    1. Identify key parameters
    2. Vary parameters one at a time
    3. Record output for each variation
    4. Analyze parameter importance
    5. Focus detailed studies on important parameters
