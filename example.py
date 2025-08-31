# Example Python code for testing code review

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = sum(numbers)
    count = len(numbers)
    # Potential issue: division by zero if list is empty
    return total / count

def process_data(data):
    """Process data without validation."""
    result = []
    for item in data:
        # No type checking or error handling
        processed = item * 2
        result.append(processed)
    return result

# Test the functions
numbers = [1, 2, 3, 4, 5]
print(f"Average: {calculate_average(numbers)}")

data = [10, 20, 30]
print(f"Processed: {process_data(data)}")