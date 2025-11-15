# Tests Directory

This directory contains organized test files for the OpenCode project.

## Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests for component interactions
- `system/` - End-to-end system tests

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/system/
```

## Test Organization

- Unit tests should focus on individual functions/classes
- Integration tests should test component interactions
- System tests should test end-to-end functionality

## Adding New Tests

When adding new tests:

1. Place in the appropriate subdirectory
2. Follow naming convention: `test_*.py`
3. Include docstrings and comments
4. Ensure tests are isolated and repeatable
