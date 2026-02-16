Implementing a Custom Tool
==========================

This guide walks through implementing a custom MCP tool for PyMAPDL-MCP.

What is a Tool?
---------------

A tool is a function that:

1. Takes structured input parameters
2. Performs some operation (usually involving MAPDL)
3. Returns structured output

Tools are discovered by MCP clients and can be called with appropriate parameters.

Anatomy of a Tool
-----------------

Here's a minimal tool structure:

.. code-block:: python

    from ansys.mapdl.mcp.contexts import Context

    def my_analysis_tool(ctx: Context, model_name: str, load_magnitude: float) -> str:
        """
        Run a simple FEA analysis.

        Parameters
        ----------
        ctx : Context
            The tool context with access to MAPDL instance
        model_name : str
            Name/description of the model
        load_magnitude : float
            Load magnitude in Newtons

        Returns
        -------
        str
            Analysis result summary
        """
        # Get the MAPDL instance from context
        mapdl = ctx.application_context.mapdl

        if mapdl is None:
            return "Error: No MAPDL instance connected"

        try:
            # Perform the analysis
            mapdl.prep7()
            mapdl.et(1, 'SOLID185')
            # ... more MAPDL commands ...
            mapdl.run()

            # Extract results
            result = mapdl.post_processing.stress()

            return f"Analysis '{model_name}' completed. Max stress: {result:.2f} MPa"

        except Exception as e:
            return f"Error during analysis: {str(e)}"

Key Components
~~~~~~~~~~~~~~

**Documentation String**: Describe what the tool does

**Context Parameter**: Access to MAPDL and application state

**Input Parameters**: Specific parameters for this tool

**Error Handling**: Graceful handling of errors

**Return Value**: Status message or results

Tool Registration
-----------------

Tools are registered in the MCP server's tool registry. The registration includes:

1. **Function**: The Python function to call
2. **Name**: Human-readable name
3. **Description**: What the tool does
4. **Input Schema**: Parameter definitions and types

Best Practices
--------------

**1. Clear Documentation**
    Write comprehensive docstrings explaining parameters and return values.

**2. Type Hints**
    Use Python type hints for all parameters and return values.

**3. Error Handling**
    Handle errors gracefully and return informative error messages.

**4. Input Validation**
    Validate input parameters before using them.

**5. Status Feedback**
    Provide feedback on progress for long-running operations.

**6. Context Management**
    Always check if MAPDL is connected before using it.

**7. Documentation**
    Document parameters, return values, and exceptions.

Example: Complete Analysis Tool
--------------------------------

Here's a more complete example of a tool:

.. code-block:: python

    from ansys.mapdl.mcp.contexts import Context
    from typing import Optional

    def cantilever_beam_analysis(
        ctx: Context,
        length: float,
        width: float,
        height: float,
        material_e: float = 2.1e11,
        material_nu: float = 0.3,
        tip_load: float = 1000.0,
    ) -> str:
        """
        Analyze a cantilever beam under point load.

        Parameters
        ----------
        ctx : Context
            Tool execution context
        length : float
            Beam length in meters
        width : float
            Beam width in meters
        height : float
            Beam height in meters
        material_e : float, optional
            Young's modulus in Pa. Default: 2.1e11 (steel)
        material_nu : float, optional
            Poisson's ratio. Default: 0.3
        tip_load : float, optional
            Tip load in Newtons. Default: 1000.0

        Returns
        -------
        str
            Analysis results including max deflection and stress
        """
        mapdl = ctx.application_context.mapdl

        if mapdl is None:
            return "Error: MAPDL not connected"

        # Validate inputs
        if length <= 0 or width <= 0 or height <= 0:
            return "Error: Dimensions must be positive"

        if material_e <= 0 or material_nu < 0 or material_nu > 0.5:
            return "Error: Invalid material properties"

        try:
            # Clear previous model
            mapdl.clear()
            mapdl.prep7()

            # Define material
            mapdl.mp('ex', 1, material_e)
            mapdl.mp('nuxy', 1, material_nu)

            # Define element type
            mapdl.et(1, 'SOLID185')

            # Create beam geometry
            mapdl.block(0, length, 0, width, 0, height)

            # Mesh
            mapdl.esize(length / 10)
            mapdl.vmesh('ALL')

            # Boundary conditions
            mapdl.nsel('s', 'loc', 'x', 0)
            mapdl.d('all', 'all', 0)

            # Apply load
            mapdl.nsel('s', 'loc', 'x', length)
            mapdl.nsel('a', 'loc', 'y', width / 2)
            mapdl.nsel('a', 'loc', 'z', height / 2)
            mapdl.f('all', 'fz', -tip_load)

            # Solve
            mapdl.run()
            mapdl.finish()

            # Extract results
            mapdl.post1()
            max_deflection = mapdl.post_processing.get_max_deflection()
            max_stress = mapdl.post_processing.get_max_stress()

            return (
                f"Cantilever analysis complete:\\n"
                f"  Beam: {length}m × {width}m × {height}m\\n"
                f"  Load: {tip_load}N\\n"
                f"  Max deflection: {max_deflection:.4e} m\\n"
                f"  Max stress: {max_stress:.2e} Pa"
            )

        except Exception as e:
            return f"Analysis failed: {str(e)}"

Testing Your Tool
-----------------

When developing a tool, test it:

1. **Unit Testing**: Test with mock contexts
2. **Integration Testing**: Test with actual MAPDL
3. **Error Cases**: Test error conditions and invalid inputs
4. **Performance**: Verify execution time is acceptable

Debugging Tools
---------------

Use these techniques to debug your tools:

1. **Logging**: Use ``ctx`` logger to log debug information
2. **Status Messages**: Return detailed status messages
3. **Comments**: Add MAPDL comments to track execution
4. **Screenshots**: Take screenshots at key points

Advanced Topics
---------------

**Async Tools**: For long-running operations, consider async implementations

**Streaming Results**: For tools producing large outputs, stream results

**Caching**: Cache expensive computations when appropriate

**Tool Composition**: Combine multiple tools into workflows

See Also
--------

- Source code in ``src/ansys/mapdl/mcp/tools.py``
- Context documentation in :doc:`../api/context_objects`
- :doc:`../user_guide/best_practices` for general recommendations
