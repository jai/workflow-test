// Test file for Calculator class
const Calculator = require('./calculator');

// Test helper function
function runTest(testName, testFunction) {
    try {
        testFunction();
        console.log(`✅ ${testName} passed`);
    } catch (error) {
        console.error(`❌ ${testName} failed: ${error.message}`);
    }
}

// Assert helper function
function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

console.log('Running Calculator sqrt() tests...\n');

const calc = new Calculator();

// Test 1: Square root of a positive number
runTest('sqrt of positive number (9)', () => {
    const result = calc.sqrt(9);
    assert(result === 3, `Expected 3, got ${result}`);
});

// Test 2: Square root of zero
runTest('sqrt of zero', () => {
    const result = calc.sqrt(0);
    assert(result === 0, `Expected 0, got ${result}`);
});

// Test 3: Square root of a negative number (should return NaN)
runTest('sqrt of negative number (-4)', () => {
    const result = calc.sqrt(-4);
    assert(isNaN(result), `Expected NaN for negative input, got ${result}`);
});

// Test 4: Square root of a decimal number
runTest('sqrt of decimal (2.25)', () => {
    const result = calc.sqrt(2.25);
    assert(result === 1.5, `Expected 1.5, got ${result}`);
});

// Test 5: Square root of 1
runTest('sqrt of 1', () => {
    const result = calc.sqrt(1);
    assert(result === 1, `Expected 1, got ${result}`);
});

// Test 6: Square root of a large number
runTest('sqrt of large number (10000)', () => {
    const result = calc.sqrt(10000);
    assert(result === 100, `Expected 100, got ${result}`);
});

// Test 7: Verify history tracking
runTest('history tracking for sqrt', () => {
    calc.clearHistory();
    calc.sqrt(16);
    calc.sqrt(-9);
    const history = calc.getHistory();
    assert(history.length === 2, `Expected 2 history entries, got ${history.length}`);
    assert(history[0] === 'sqrt(16) = 4', `Unexpected history entry: ${history[0]}`);
    assert(history[1] === 'sqrt(-9) = NaN (negative input)', `Unexpected history entry: ${history[1]}`);
});

console.log('\nAll tests completed!');