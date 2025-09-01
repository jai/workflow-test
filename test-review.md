# Test File for Code Review

This is a test file to trigger the code review workflow.

## Test Code

```python
def calculate_sum(a, b):
    # This function has intentional issues for testing
    result = a + b
    print(result)  # Should return instead of print
    # Missing return statement
```

## Another Issue

```javascript
function getData() {
    fetch('/api/data')
        .then(response => response.json())
        // Missing error handling
}
```