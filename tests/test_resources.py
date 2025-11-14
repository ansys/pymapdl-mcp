"""Tests for MCP resources."""

import pytest


@pytest.mark.asyncio
async def test_resources_registered():
    """Test that all resources are registered with the MCP server."""
    from ansys.mapdl.mcp.mpc import mcp

    # Get list of registered resources
    resource_list = await mcp.list_resources()

    # Expected resource URIs
    expected_resources = [
        "mapdl://workflow/overview",
        "mapdl://workflow/preprocessing/geometry",
        "mapdl://workflow/preprocessing/elements",
        "mapdl://workflow/preprocessing/materials",
        "mapdl://workflow/preprocessing/mesh",
        "mapdl://workflow/preprocessing/boundary-conditions",
        "mapdl://workflow/solution",
        "mapdl://workflow/postprocessing",
        "mapdl://workflow/general-rules",
    ]

    # Check each expected resource is registered
    resource_uris = [str(r.uri) for r in resource_list]
    for expected_uri in expected_resources:
        assert expected_uri in resource_uris, f"Resource {expected_uri} not found"


@pytest.mark.asyncio
async def test_resources_readable_at_runtime():
    """Test that all registered resources can be read at runtime."""
    from ansys.mapdl.mcp.mpc import mcp

    # Get list of all registered resources
    resource_list = await mcp.list_resources()

    # Try to read each resource to ensure it's accessible at runtime
    for resource in resource_list:
        resource_uri = str(resource.uri)

        # Read the resource using the MCP server's read_resource method
        # This returns a list of ReadResourceContents objects
        content_list = await mcp.read_resource(resource_uri)

        # Verify we got content back
        assert content_list is not None, f"Resource {resource_uri} returned None"
        assert len(content_list) > 0, f"Resource {resource_uri} returned empty list"

        # Extract the actual text content from the first item
        content_item = content_list[0]
        assert hasattr(
            content_item, "content"
        ), f"Resource {resource_uri} content item missing 'content' attribute"

        content = content_item.content


@pytest.mark.asyncio
async def test_specific_resource_content_at_runtime():
    """Test that specific resources return expected content at runtime."""
    from ansys.mapdl.mcp.mpc import mcp

    # Test workflow overview
    overview_list = await mcp.read_resource("mapdl://workflow/overview")
    overview_content = overview_list[0].content
    assert "MAPDL Simulation Workflow Overview" in overview_content
    assert "Preprocessing" in overview_content
    assert "Solution" in overview_content
    assert "Postprocessing" in overview_content

    # Test preprocessing geometry
    geometry_list = await mcp.read_resource("mapdl://workflow/preprocessing/geometry")
    geometry_content = geometry_list[0].content
    assert "Geometry Guidelines" in geometry_content
    assert "2D vs 3D" in geometry_content

    # Test solution phase
    solution_list = await mcp.read_resource("mapdl://workflow/solution")
    solution_content = solution_list[0].content
    assert "Solution Phase" in solution_content
    assert "mapdl.solution()" in solution_content

    # Test postprocessing
    postproc_list = await mcp.read_resource("mapdl://workflow/postprocessing")
    postproc_content = postproc_list[0].content
    assert "Postprocessing Phase" in postproc_content
    assert "post1" in postproc_content or "post_processing" in postproc_content


def test_workflow_overview_content():
    """Test that workflow overview resource returns expected content."""
    from ansys.mapdl.mcp import resources

    content = resources.workflow_overview()

    # Check for key sections in the overview
    assert "MAPDL Simulation Workflow Overview" in content
    assert "Preprocessing" in content
    assert "Solution" in content
    assert "Postprocessing" in content
    assert "General Rules" in content


def test_preprocessing_geometry_content():
    """Test preprocessing geometry resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.preprocessing_geometry()

    assert "Geometry Guidelines" in content
    assert "2D vs 3D" in content
    assert "finite elements" in content


def test_preprocessing_elements_content():
    """Test preprocessing elements resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.preprocessing_elements()

    assert "Element Type Selection" in content
    assert "SOLID186" in content
    assert "SHELL181" in content
    assert "BEAM189" in content


def test_preprocessing_materials_content():
    """Test preprocessing materials resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.preprocessing_materials()

    assert "Material Property Definition" in content
    assert "Steel" in content or "steel" in content
    assert "Aluminum" in content or "aluminum" in content


def test_preprocessing_mesh_content():
    """Test preprocessing mesh resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.preprocessing_mesh()

    assert "Mesh Generation Guidelines" in content
    assert "mesh quality" in content.lower()
    assert "vmesh" in content or "VMESH" in content


def test_preprocessing_boundary_conditions_content():
    """Test preprocessing boundary conditions resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.preprocessing_boundary_conditions()

    assert "Boundary Conditions and Loads" in content
    assert "Fixed Supports" in content or "fixed supports" in content
    assert "beam elements" in content.lower()


def test_solution_phase_content():
    """Test solution phase resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.solution_phase()

    assert "Solution" in content
    assert "STATIC" in content
    assert "MODAL" in content
    assert "TRANSIENT" in content
    assert "mapdl.solution()" in content


def test_postprocessing_phase_content():
    """Test postprocessing phase resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.postprocessing_phase()

    assert "Postprocessing" in content
    assert "post1" in content
    assert "post26" in content
    assert "plot_nodal_solution" in content


def test_general_rules_content():
    """Test general rules resource content."""
    from ansys.mapdl.mcp import resources

    content = resources.general_rules()

    assert "General Rules" in content
    assert "Accuracy" in content or "accuracy" in content
    assert "convergence" in content.lower()
    assert "verification" in content.lower()


def test_all_resources_return_strings():
    """Test that all resource functions return strings."""
    from ansys.mapdl.mcp import resources

    resource_functions = [
        resources.workflow_overview,
        resources.preprocessing_geometry,
        resources.preprocessing_elements,
        resources.preprocessing_materials,
        resources.preprocessing_mesh,
        resources.preprocessing_boundary_conditions,
        resources.solution_phase,
        resources.postprocessing_phase,
        resources.general_rules,
    ]

    for func in resource_functions:
        result = func()
        assert isinstance(result, str), f"{func.__name__} should return a string"
        assert len(result) > 0, f"{func.__name__} should return non-empty string"
