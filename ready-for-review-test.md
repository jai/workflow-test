# Ready for Review Test

This file tests the ready_for_review trigger in the PR 94 workflow.

```python
def bad_function():
    # Missing docstring
    x = 1 / 0  # Division by zero
    return x
```