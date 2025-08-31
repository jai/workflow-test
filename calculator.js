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

    pow(base, exponent) {
        // Handle edge case: 0^0 returns 1 as per mathematical convention
        if (base === 0 && exponent === 0) {
            const result = 1;
            this.history.push(`${base} ^ ${exponent} = ${result}`);
            return result;
        }
        
        const result = Math.pow(base, exponent);
        this.history.push(`${base} ^ ${exponent} = ${result}`);
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