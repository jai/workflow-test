// Test file for Calculator class
const Calculator = require('./calculator');

// Test suite for Calculator
function runTests() {
    const calc = new Calculator();
    let testsPassed = 0;
    let totalTests = 0;

    console.log('Running Calculator Tests...\n');

    // Test 1: Normal division
    totalTests++;
    const result1 = calc.divide(10, 2);
    if (result1 === 5) {
        console.log('✓ Test 1 passed: divide(10, 2) = 5');
        testsPassed++;
    } else {
        console.log(`✗ Test 1 failed: divide(10, 2) expected 5, got ${result1}`);
    }

    // Test 2: Division by zero
    totalTests++;
    const result2 = calc.divide(10, 0);
    if (result2 === 'Error: Division by zero') {
        console.log('✓ Test 2 passed: divide(10, 0) returns error message');
        testsPassed++;
    } else {
        console.log(`✗ Test 2 failed: divide(10, 0) expected error message, got ${result2}`);
    }

    // Test 3: Division with negative numbers
    totalTests++;
    const result3 = calc.divide(-15, 3);
    if (result3 === -5) {
        console.log('✓ Test 3 passed: divide(-15, 3) = -5');
        testsPassed++;
    } else {
        console.log(`✗ Test 3 failed: divide(-15, 3) expected -5, got ${result3}`);
    }

    // Test 4: Division with decimal result
    totalTests++;
    const result4 = calc.divide(7, 2);
    if (result4 === 3.5) {
        console.log('✓ Test 4 passed: divide(7, 2) = 3.5');
        testsPassed++;
    } else {
        console.log(`✗ Test 4 failed: divide(7, 2) expected 3.5, got ${result4}`);
    }

    // Test 5: Division with both negative numbers
    totalTests++;
    const result5 = calc.divide(-20, -4);
    if (result5 === 5) {
        console.log('✓ Test 5 passed: divide(-20, -4) = 5');
        testsPassed++;
    } else {
        console.log(`✗ Test 5 failed: divide(-20, -4) expected 5, got ${result5}`);
    }

    // Summary
    console.log(`\n========================================`);
    console.log(`Test Results: ${testsPassed}/${totalTests} tests passed`);
    if (testsPassed === totalTests) {
        console.log('All tests passed! ✓');
    } else {
        console.log(`${totalTests - testsPassed} test(s) failed.`);
        process.exit(1);
    }
}

// Run the tests
runTests();