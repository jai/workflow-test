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

    abs(num) {
        // Handle edge cases for null and undefined
        if (num === null || num === undefined) {
            this.history.push(`abs(${num}) = 0`);
            return 0;
        }
        
        // Convert to number if it's not already
        const value = Number(num);
        
        // Check if conversion resulted in NaN
        if (isNaN(value)) {
            this.history.push(`abs(${num}) = 0`);
            return 0;
        }
        
        // Return absolute value
        const result = Math.abs(value);
        this.history.push(`abs(${num}) = ${result}`);
        return result;
    }
}

// Example usage
const calc = new Calculator();
console.log(calc.add(5, 3));
console.log(calc.divide(10, 2));
console.log(calc.multiply(4, 7));
console.log('History:', calc.getHistory());

module.exports = Calculator;