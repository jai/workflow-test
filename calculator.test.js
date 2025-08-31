// Test file for Calculator class
const Calculator = require('./calculator');

// Test subtract function
function testSubtract() {
    const calc = new Calculator();
    
    // Test basic subtraction
    console.log('Testing subtract(10, 3):', calc.subtract(10, 3) === 7 ? 'PASS' : 'FAIL');
    console.log('Testing subtract(5, 5):', calc.subtract(5, 5) === 0 ? 'PASS' : 'FAIL');
    console.log('Testing subtract(0, 5):', calc.subtract(0, 5) === -5 ? 'PASS' : 'FAIL');
    console.log('Testing subtract(-3, -2):', calc.subtract(-3, -2) === -1 ? 'PASS' : 'FAIL');
    
    // Test history functionality
    calc.clearHistory();
    calc.subtract(100, 25);
    const history = calc.getHistory();
    console.log('Testing history after subtract:', history.includes('100 - 25 = 75') ? 'PASS' : 'FAIL');
    
    console.log('\nAll subtract tests completed!');
}

// Run tests
console.log('Running Calculator Tests\n');
testSubtract();