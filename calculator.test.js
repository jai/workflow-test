const Calculator = require('./calculator');

console.log('Running tests for Calculator.abs() function...\n');

const calc = new Calculator();
let allPassed = true;
let testNumber = 0;

// Test cases for abs function
const absTests = [
  // Basic positive and negative numbers
  { input: 5, expected: 5, description: 'positive number' },
  { input: -5, expected: 5, description: 'negative number' },
  { input: 0, expected: 0, description: 'zero' },
  
  // Edge cases
  { input: null, expected: 0, description: 'null value' },
  { input: undefined, expected: 0, description: 'undefined value' },
  { input: NaN, expected: 0, description: 'NaN value' },
  
  // String numbers
  { input: '10', expected: 10, description: 'positive string number' },
  { input: '-10', expected: 10, description: 'negative string number' },
  
  // Decimal numbers
  { input: 3.14, expected: 3.14, description: 'positive decimal' },
  { input: -3.14, expected: 3.14, description: 'negative decimal' },
  
  // Special values
  { input: Infinity, expected: Infinity, description: 'Infinity' },
  { input: -Infinity, expected: Infinity, description: 'negative Infinity' },
  
  // Invalid string
  { input: 'abc', expected: 0, description: 'non-numeric string' }
];

console.log('Testing abs() function:');
console.log('----------------------');

absTests.forEach((test) => {
  testNumber++;
  const result = calc.abs(test.input);
  const passed = result === test.expected;
  
  if (passed) {
    console.log(`✓ Test ${testNumber} passed: abs(${test.input}) = ${result} (${test.description})`);
  } else {
    console.log(`✗ Test ${testNumber} failed: abs(${test.input}) returned ${result}, expected ${test.expected} (${test.description})`);
    allPassed = false;
  }
});

// Test that history is being recorded
console.log('\n' + 'Testing history recording:');
console.log('-------------------------');
// Create a fresh calculator instance for history testing
const calcForHistory = new Calculator();
calcForHistory.abs(5);
calcForHistory.abs(-10);
calcForHistory.abs(null);

const history = calcForHistory.getHistory();
const expectedHistory = ['abs(5) = 5', 'abs(-10) = 10', 'abs(null) = 0'];
let historyPassed = true;

if (history.length === expectedHistory.length) {
  for (let i = 0; i < history.length; i++) {
    if (history[i] !== expectedHistory[i]) {
      console.log(`✗ History mismatch at index ${i}: got "${history[i]}", expected "${expectedHistory[i]}"`);
      historyPassed = false;
      allPassed = false;
    }
  }
  if (historyPassed) {
    console.log('✓ History recording works correctly');
  }
} else {
  console.log(`✗ History length mismatch: got ${history.length}, expected ${expectedHistory.length}`);
  allPassed = false;
}

console.log('\n' + (allPassed ? 'All tests passed! ✅' : 'Some tests failed. ❌'));
process.exit(allPassed ? 0 : 1);