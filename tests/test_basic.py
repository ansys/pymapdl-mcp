"""Basic tests for PyMAPDL MCP Server package."""

import pytest

import ansys.mapdl.mcp


@pytest.mark.unit
def test_version():
    """Test that version is defined and is a string."""
    assert hasattr(ansys.mapdl.mcp, "__version__")
    assert isinstance(ansys.mapdl.mcp.__version__, str)
    assert len(ansys.mapdl.mcp.__version__) > 0


@pytest.mark.unit
def test_package_imports():
    """Test that all expected functions and classes can be imported."""
    from ansys.mapdl.mcp import (
        AppContext,
        app_lifespan,
        check_mapdl_status,
        mcp,
        run_mapdl_command,
        write_comment,
    )

    assert AppContext is not None
    assert app_lifespan is not None
    assert check_mapdl_status is not None
    assert mcp is not None
    assert run_mapdl_command is not None
    assert write_comment is not None


@pytest.mark.unit
def test_all_exports():
    """Test that __all__ contains all expected exports."""
    from ansys.mapdl.mcp import __all__

    expected_exports = [
        "AppContext",
        "app_lifespan",
        "check_mapdl_installed",
        "check_mapdl_status",
        "connect_to_mapdl",
        "disconnect_from_mapdl",
        "launch_mapdl",
        "list_mapdl_instances",
        "mcp",
        "run_mapdl_command",
        "run_multiple_commands",
        "write_comment",
        "__version__",
    ]

    assert set(__all__) == set(expected_exports)


@pytest.mark.unit
def test_app_context_creation(app_context):
    """Test that AppContext can be created with MAPDL instance."""
    assert app_context.mapdl is not None
    assert hasattr(app_context.mapdl, "version")


@pytest.mark.unit
def test_app_context_no_mapdl(app_context_no_mapdl):
    """Test that AppContext can be created without MAPDL instance."""
    assert app_context_no_mapdl.mapdl is None
