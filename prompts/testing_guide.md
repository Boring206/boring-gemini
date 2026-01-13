# Testing Guide

This prompt guides the Agent to write high-quality tests.

## Test Structure

1. **Arrange**: Set up test data and dependencies
2. **Act**: Execute the code under test
3. **Assert**: Verify expected outcomes

## Best Practices

- One assertion per test (when possible)
- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Mock external dependencies (file I/O, network, databases)
- Test edge cases: empty inputs, None, very large inputs, special characters

## Python Testing with pytest

```python
import pytest

@pytest.mark.unit
def test_function_returns_expected_value():
    # Arrange
    input_data = "test"
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == "expected"
```

## When Generating Tests

1. Identify the function's contract (inputs, outputs, side effects)
2. List edge cases and error conditions
3. Write happy path tests first
4. Add error/edge case tests
5. Verify mocks are used for I/O
