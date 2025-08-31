const { sayHello } = require('./hello');

console.log('Running tests for sayHello function...\n');

const tests = [
  { input: 'World', expected: 'Hello, World!' },
  { input: 'Claude', expected: 'Hello, Claude!' },
  { input: 'GitHub', expected: 'Hello, GitHub!' },
  { input: '', expected: 'Hello, !' }
];

let allPassed = true;

tests.forEach((test, index) => {
  const result = sayHello(test.input);
  const passed = result === test.expected;
  
  if (passed) {
    console.log(`✓ Test ${index + 1} passed: sayHello("${test.input}") = "${result}"`);
  } else {
    console.log(`✗ Test ${index + 1} failed: sayHello("${test.input}") returned "${result}", expected "${test.expected}"`);
    allPassed = false;
  }
});

console.log('\n' + (allPassed ? 'All tests passed! ✅' : 'Some tests failed. ❌'));
process.exit(allPassed ? 0 : 1);