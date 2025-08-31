const Calculator = require('./calculator');

console.log('Running tests for Calculator multiply function...\n');

const calc = new Calculator();
const tests = [
  { a: 5, b: 3, expected: 15, description: 'positive numbers' },
  { a: -4, b: 2, expected: -8, description: 'negative and positive' },
  { a: 0, b: 100, expected: 0, description: 'zero multiplication' },
  { a: 2.5, b: 4, expected: 10, description: 'decimal multiplication' },
  { a: -3, b: -3, expected: 9, description: 'two negative numbers' }
];

let allPassed = true;

tests.forEach((test, index) => {
  const result = calc.multiply(test.a, test.b);
  const passed = result === test.expected;
  
  if (passed) {
    console.log(`✓ Test ${index + 1} passed: multiply(${test.a}, ${test.b}) = ${result} (${test.description})`);
  } else {
    console.log(`✗ Test ${index + 1} failed: multiply(${test.a}, ${test.b}) returned ${result}, expected ${test.expected} (${test.description})`);
    allPassed = false;
  }
});

// Verify multiply doesn't save to history (as per requirements)
const historyBefore = calc.getHistory().length;
calc.multiply(10, 5);
const historyAfter = calc.getHistory().length;
const historyCheckPassed = historyBefore === historyAfter;

if (historyCheckPassed) {
  console.log('✓ History check passed: multiply function does not save to history');
} else {
  console.log('✗ History check failed: multiply function should not save to history');
  allPassed = false;
}

console.log('\n' + (allPassed ? 'All tests passed! ✅' : 'Some tests failed. ❌'));
process.exit(allPassed ? 0 : 1);