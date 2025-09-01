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

    modulo(dividend, divisor) {
        // Handle edge case: division by zero
        if (divisor === 0) {
            throw new Error('Division by zero: divisor cannot be zero');
        }
        const result = dividend % divisor;
        this.history.push(`${dividend} % ${divisor} = ${result}`);
        return result;
    }

    // Alias for modulo function
    mod(dividend, divisor) {
        return this.modulo(dividend, divisor);
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
}

// Example usage
const calc = new Calculator();
console.log(calc.add(5, 3));
console.log(calc.divide(10, 2));
console.log(calc.multiply(4, 7));
console.log(calc.modulo(10, 3));
console.log(calc.mod(7, 2));  // Using alias
console.log('History:', calc.getHistory());

module.exports = Calculator;