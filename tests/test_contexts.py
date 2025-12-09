"""Tests for MCP context tools (formerly resources)."""

import pytest


@pytest.mark.asyncio
async def test_context_tools_registered():
    """Test that all context tools are registered with the MCP server."""
    from ansys.mapdl.mcp.server import app

    # Get list of registered tools
    tool_list = await app.get_tools()

    # Expected tool names
    expected_tools = [
        "get_context_for_workflow_overview",
        "get_context_for_preprocessing_geometry",
        "get_context_for_preprocessing_elements",
        "get_context_for_preprocessing_materials",
        "get_context_for_preprocessing_mesh",
        "get_context_for_preprocessing_boundary_conditions",
        "get_context_for_solution_phase",
        "get_context_for_postprocessing_phase",
        "get_context_for_general_rules",
    ]

    # Check each expected tool is registered
    tool_names = [t.name for t in tool_list.values()]
    for expected_name in expected_tools:
        assert expected_name in tool_names, f"Tool {expected_name} not found"


def test_workflow_overview_content():
    """Test that workflow overview tool returns expected content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_workflow_overview()

    # Check for key sections in the overview
    assert "MAPDL Simulation Workflow Overview" in content
    assert "Preprocessing" in content
    assert "Solution" in content
    assert "Postprocessing" in content
    assert "General Rules" in content


def test_preprocessing_geometry_content():
    """Test preprocessing geometry tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_preprocessing_geometry()

    assert "Geometry Guidelines" in content
    assert "2D vs 3D" in content
    assert "finite elements" in content


def test_preprocessing_elements_content():
    """Test preprocessing elements tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_preprocessing_elements()

    assert "Element Type Selection" in content
    assert "SOLID186" in content
    assert "SHELL181" in content
    assert "BEAM189" in content


def test_preprocessing_materials_content():
    """Test preprocessing materials tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_preprocessing_materials()

    assert "Material Property Definition" in content
    assert "Steel" in content or "steel" in content
    assert "Aluminum" in content or "aluminum" in content


def test_preprocessing_mesh_content():
    """Test preprocessing mesh tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_preprocessing_mesh()

    assert "Mesh Generation Guidelines" in content
    assert "mesh quality" in content.lower()
    assert "vmesh" in content or "VMESH" in content


def test_preprocessing_boundary_conditions_content():
    """Test preprocessing boundary conditions tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_preprocessing_boundary_conditions()

    assert "Boundary Conditions and Loads" in content
    assert "Fixed Supports" in content or "fixed supports" in content
    assert "beam elements" in content.lower()


def test_solution_phase_content():
    """Test solution phase tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_solution_phase()

    assert "Solution" in content
    assert "STATIC" in content
    assert "MODAL" in content
    assert "TRANSIENT" in content
    assert "mapdl.solution()" in content


def test_postprocessing_phase_content():
    """Test postprocessing phase tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_postprocessing_phase()

    assert "Postprocessing" in content
    assert "post1" in content
    assert "post26" in content
    assert "plot_nodal_solution" in content


def test_general_rules_content():
    """Test general rules tool content."""
    from ansys.mapdl.mcp import contexts

    content = contexts.get_context_for_general_rules()

    assert "General Rules" in content
    assert "Accuracy" in content or "accuracy" in content
    assert "convergence" in content.lower()
    assert "verification" in content.lower()


def test_all_context_tools_return_strings():
    """Test that all context tool functions return strings."""
    from ansys.mapdl.mcp import contexts

    context_tool_functions = [
        contexts.get_context_for_workflow_overview,
        contexts.get_context_for_preprocessing_geometry,
        contexts.get_context_for_preprocessing_elements,
        contexts.get_context_for_preprocessing_materials,
        contexts.get_context_for_preprocessing_mesh,
        contexts.get_context_for_preprocessing_boundary_conditions,
        contexts.get_context_for_solution_phase,
        contexts.get_context_for_postprocessing_phase,
        contexts.get_context_for_general_rules,
    ]

    for func in context_tool_functions:
        result = func()
        assert isinstance(result, str), f"{func.__name__} should return a string"
        assert len(result) > 0, f"{func.__name__} should return non-empty string"
