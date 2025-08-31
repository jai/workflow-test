// Test file for workflow review comments
function calculateSum(a, b) {
    // This could use better error handling
    return a + b;
}

function divideNumbers(x, y) {
    // Missing zero check - potential bug
    return x / y;
}

// TODO: Add more comprehensive tests
console.log(calculateSum(5, 3));
console.log(divideNumbers(10, 2));