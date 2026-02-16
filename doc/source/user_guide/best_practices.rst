Best Practices
==============

Session Management
------------------

**Reuse MAPDL Instances**
    Keep the same MAPDL instance open for multiple operations to improve performance.
    Only restart when necessary (e.g., to clear the database).

**Clean Shutdown**
    Always disconnect properly from MAPDL instances to free resources.

**Error Handling**
    Check tool results for errors and handle them gracefully in your workflow.

Command Execution
-----------------

**Batch Commands**
    Use ``run_multiple_commands`` instead of individual commands for better performance.

**Verify State**
    Use ``check_mapdl_status`` periodically to verify the session state.

**Use Comments**
    Add comments in the MAPDL session to document your workflow for clarity.

Data Handling
-------------

**Extract Efficiently**
    Extract only the data you need rather than loading entire result sets.

**Cache Results**
    Store extracted data in Python variables to avoid repeated extraction.

**Validate Data**
    Check that extracted data makes physical sense (e.g., positive stresses, reasonable displacements).

Visualization
-------------

**Screenshots After Key Steps**
    Take screenshots after geometry definition, meshing, and solving to verify progress.

**Custom Plots for Analysis**
    Use custom matplotlib plots for detailed analysis beyond MAPDL's built-in capabilities.

**Export for Documentation**
    Save high-quality plots for reports and documentation.

Workflow Design
---------------

**Modular Workflows**
    Break complex analyses into smaller, independent steps.

**Error Recovery**
    Design workflows that can recover from errors without complete restart.

**Progress Feedback**
    Include status updates and progress indicators in long-running workflows.

**Parameter Validation**
    Validate all input parameters before sending to MAPDL.

Performance
-----------

**Minimize Restarts**
    Avoid restarting MAPDL unless absolutely necessary.

**Efficient Meshing**
    Use adaptive meshing and mesh refinement selectively.

**Result Processing**
    Process results in Python rather than repeatedly querying MAPDL.

**Parallel Operations**
    Consider launching multiple MAPDL instances for independent analyses.

Common Patterns
---------------

**Parameter Sweep**
    1. Define parameter ranges
    2. Clear results between runs
    3. Update parameters
    4. Run analysis
    5. Extract results
    6. Aggregate results across runs

**Convergence Study**
    1. Run analysis with coarse mesh
    2. Refine mesh selectively
    3. Re-run analysis
    4. Compare results
    5. Repeat until converged

**Sensitivity Analysis**
    1. Identify key parameters
    2. Vary parameters one at a time
    3. Record output for each variation
    4. Analyze parameter importance
    5. Focus detailed studies on important parameters
