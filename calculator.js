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

    sqrt(num) {
        // Handle negative numbers by returning NaN
        if (num < 0) {
            this.history.push(`sqrt(${num}) = NaN (negative input)`);
            return NaN;
        }
        
        const result = Math.sqrt(num);
        this.history.push(`sqrt(${num}) = ${result}`);
        return result;
    }
}

// Example usage
const calc = new Calculator();
console.log(calc.add(5, 3));
console.log(calc.divide(10, 2));
console.log(calc.multiply(4, 7));
console.log(calc.sqrt(16));
console.log(calc.sqrt(-4));
console.log('History:', calc.getHistory());

module.exports = Calculator;