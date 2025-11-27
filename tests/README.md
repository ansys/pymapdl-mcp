# PyMAPDL MCP Tests

This directory contains the test suite for the PyMAPDL Model Context Protocol (MCP) server.

## Test Organization

### Unit Tests (No MAPDL Required)
These tests use mocks and don't require MAPDL to be installed:

- **`test_context.py`** - Tests for `PyMAPDLContext` dataclass
- **`test_server.py`** - Tests for `PyMAPDLMCPServer` initialization and lifecycle
- **`test_helpers.py`** - Tests for helper functions (connection checks, reconnection, replay)
- **`test_tools.py`** - Tests for MCP tool functions with mocked dependencies

### Integration Tests (Requires MAPDL)
These tests require an actual MAPDL installation:

- **`test_integration.py`** - End-to-end tests with real MAPDL instances

## Running Tests

### Run All Unit Tests (Fast)
```bash
pytest -m unit
```

### Run All Tests (Including Integration)
```bash
pytest
```

### Run Integration Tests Only
```bash
pytest -m integration
```

### Run with Coverage Report
```bash
pytest --cov=ansys.mapdl.mcp --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_context.py
pytest tests/test_tools.py -v
```

### Run Specific Test
```bash
pytest tests/test_tools.py::TestExecutePythonCodeTool::test_execute_success -v
```

## Test Markers

- `@pytest.mark.unit` - Unit tests that don't require MAPDL
- `@pytest.mark.integration` - Integration tests requiring MAPDL
- `@pytest.mark.slow` - Tests that take significant time to run

## Fixtures

The `conftest.py` file provides shared fixtures:

- **`mock_python_session`** - Mock PersistentPythonSession for unit tests
- **`mock_context`** - Mock PyMAPDLContext with session and history
- **`mock_mapdl`** - Mock MAPDL instance
- **`sample_command_history`** - Sample command list for testing
- **`mock_get_context`** - Mock dependency injection for tools

## Integration Test Setup

Integration tests are skipped by default unless:
1. MAPDL is installed and accessible
2. Environment variable `RUN_INTEGRATION_TESTS=1` is set

To run integration tests:
```bash
export RUN_INTEGRATION_TESTS=1  # Linux/Mac
set RUN_INTEGRATION_TESTS=1     # Windows CMD
$env:RUN_INTEGRATION_TESTS=1    # Windows PowerShell

pytest -m integration
```

## Test Coverage

Target coverage: **>85%**

Generate coverage report:
```bash
pytest --cov=ansys.mapdl.mcp --cov-report=term-missing --cov-report=html
```

View HTML report:
```bash
# Open htmlcov/index.html in browser
```

## Continuous Integration

In CI/CD pipelines:
- Run unit tests on every commit
- Run integration tests only when MAPDL is available
- Generate and publish coverage reports

Example CI configuration:
```yaml
# Unit tests (always run)
- name: Run Unit Tests
  run: pytest -m unit --cov --cov-report=xml

# Integration tests (conditional)
- name: Run Integration Tests
  if: env.MAPDL_AVAILABLE == 'true'
  run: pytest -m integration
```

## Writing New Tests

### Unit Test Example
```python
import pytest
from ansys.mapdl.mcp.your_module import your_function

@pytest.mark.unit
def test_your_function(mock_python_session):
    """Test description."""
    # Arrange
    mock_python_session.execute.return_value = {"success": True}
    
    # Act
    result = your_function()
    
    # Assert
    assert result is not None
```

### Integration Test Example
```python
import pytest

@pytest.mark.integration
def test_with_real_mapdl(real_mapdl):
    """Test description."""
    # Test with actual MAPDL instance
    real_mapdl.prep7()
    assert real_mapdl.is_alive
```

## Troubleshooting

### Import Errors
Ensure the package is installed in development mode:
```bash
pip install -e .
pip install -e ".[dev]"
```

### MAPDL Not Found
Ensure MAPDL is installed and PyMAPDL can find it:
```bash
pymapdl list
```

### Slow Tests
Skip slow tests:
```bash
pytest -m "not slow"
```

### Mock Issues
If mocks aren't working, check:
- Import paths in patches match actual module structure
- Mock is configured before the function is called
- `spec` parameter is used for strict mocking
