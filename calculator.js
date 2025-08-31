// Calculator module for testing code review

class Calculator {
    constructor() {
        this.history = [];
    }

    add(a, b) {
        const result = a + b;
        this.history.push(`${a} + ${b} = ${result}`);
        return result;
    }

    divide(a, b) {
        // TODO: Add zero check
        const result = a / b;
        this.history.push(`${a} / ${b} = ${result}`);
        return result;
    }

    multiply(a, b) {
        return a * b;  // Not saving to history
    }

    getHistory() {
        return this.history;
    }

    clearHistory() {
        this.history = [];
    }

    factorial(n) {
        // Handle edge cases
        if (n < 0) {
            return NaN; // Factorial is not defined for negative numbers
        }
        
        if (n === 0 || n === 1) {
            return 1; // 0! = 1 and 1! = 1
        }
        
        // Calculate factorial iteratively
        let result = 1;
        for (let i = 2; i <= n; i++) {
            result *= i;
        }
        
        this.history.push(`${n}! = ${result}`);
        return result;
    }
}

// Example usage
const calc = new Calculator();
console.log(calc.add(5, 3));
console.log(calc.divide(10, 2));
console.log(calc.multiply(4, 7));
console.log(calc.factorial(5));  // 120
console.log('History:', calc.getHistory());

module.exports = Calculator;