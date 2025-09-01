const Calculator = require('./calculator');

console.log('Running tests for Calculator module...\n');

const calc = new Calculator();
let allPassed = true;
let testCount = 0;

// Helper function to run a test
function runTest(description, testFunc) {
    testCount++;
    try {
        const result = testFunc();
        if (result) {
            console.log(`✓ Test ${testCount}: ${description}`);
        } else {
            console.log(`✗ Test ${testCount}: ${description} - Failed`);
            allPassed = false;
        }
    } catch (error) {
        console.log(`✗ Test ${testCount}: ${description} - Error: ${error.message}`);
        allPassed = false;
    }
}

// Test factorial function
console.log('Testing factorial function:');

runTest('factorial(0) should return 1', () => {
    return calc.factorial(0) === 1;
});

runTest('factorial(1) should return 1', () => {
    return calc.factorial(1) === 1;
});

runTest('factorial(5) should return 120', () => {
    return calc.factorial(5) === 120;
});

runTest('factorial(10) should return 3628800', () => {
    return calc.factorial(10) === 3628800;
});

runTest('factorial(-1) should return NaN', () => {
    return isNaN(calc.factorial(-1));
});

runTest('factorial(-10) should return NaN', () => {
    return isNaN(calc.factorial(-10));
});

// Test that factorial adds to history
runTest('factorial should add to history', () => {
    calc.clearHistory();
    calc.factorial(4);
    const history = calc.getHistory();
    return history.length === 1 && history[0] === '4! = 24';
});

// Test existing functions
console.log('\nTesting existing calculator functions:');

runTest('add(5, 3) should return 8', () => {
    return calc.add(5, 3) === 8;
});

runTest('divide(10, 2) should return 5', () => {
    return calc.divide(10, 2) === 5;
});

runTest('multiply(4, 7) should return 28', () => {
    return calc.multiply(4, 7) === 28;
});

// Test edge cases for factorial
console.log('\nTesting factorial edge cases:');

runTest('factorial(0) edge case check', () => {
    const result = calc.factorial(0);
    return result === 1;
});

runTest('factorial with large number (15)', () => {
    const result = calc.factorial(15);
    return result === 1307674368000;
});

// Summary
console.log('\n' + (allPassed ? `All ${testCount} tests passed! ✅` : `Some tests failed. ❌`));
process.exit(allPassed ? 0 : 1);