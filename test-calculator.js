const Calculator = require('./calculator');

console.log('Running tests for Calculator pow function...\n');

const calc = new Calculator();
let allPassed = true;

// Test cases for pow function
const powTests = [
  { base: 2, exp: 3, expected: 8, description: 'Basic power: 2^3' },
  { base: 5, exp: 2, expected: 25, description: 'Basic power: 5^2' },
  { base: 10, exp: 0, expected: 1, description: 'Any number to power 0' },
  { base: 0, exp: 5, expected: 0, description: 'Zero to any positive power' },
  { base: 0, exp: 0, expected: 1, description: 'Edge case: 0^0 (mathematical convention)' },
  { base: -2, exp: 3, expected: -8, description: 'Negative base with odd exponent' },
  { base: -2, exp: 4, expected: 16, description: 'Negative base with even exponent' },
  { base: 2, exp: -2, expected: 0.25, description: 'Negative exponent' },
  { base: 1, exp: 100, expected: 1, description: 'One to any power' },
  { base: 2.5, exp: 2, expected: 6.25, description: 'Decimal base' },
];

console.log('Testing pow function:');
console.log('====================');
powTests.forEach((test, index) => {
  const result = calc.pow(test.base, test.exp);
  const passed = result === test.expected;
  
  if (passed) {
    console.log(`✓ Test ${index + 1} passed: ${test.description} = ${result}`);
  } else {
    console.log(`✗ Test ${index + 1} failed: ${test.description}`);
    console.log(`  Expected: ${test.expected}, Got: ${result}`);
    allPassed = false;
  }
});

// Test history tracking
console.log('\nTesting history tracking:');
console.log('========================');
calc.clearHistory();
calc.pow(3, 2);
calc.pow(0, 0);
const history = calc.getHistory();

if (history.length === 2) {
  console.log('✓ History tracking works correctly');
  console.log('  History:', history);
} else {
  console.log('✗ History tracking failed');
  console.log('  Expected 2 entries, got:', history.length);
  allPassed = false;
}

// Test with other calculator functions to ensure integration
console.log('\nTesting integration with other functions:');
console.log('=========================================');
calc.clearHistory();
calc.add(5, 3);
calc.pow(2, 4);
calc.multiply(3, 4);
calc.divide(20, 4);

const fullHistory = calc.getHistory();
// Should have 3 entries (add, pow, divide) - multiply doesn't save to history
if (fullHistory.length === 3 && fullHistory[1].includes('^')) {
  console.log('✓ Integration with other calculator functions works');
  console.log('  Full history:', fullHistory);
} else {
  console.log('✗ Integration test failed');
  allPassed = false;
}

console.log('\n' + (allPassed ? 'All tests passed! ✅' : 'Some tests failed. ❌'));
process.exit(allPassed ? 0 : 1);