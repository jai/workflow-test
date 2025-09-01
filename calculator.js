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

    /**
     * Calculate the percentage of a value
     * @param {number} value - The base value
     * @param {number} percent - The percentage to calculate
     * @returns {number} The percentage of the value
     * @example percentage(200, 10) returns 20
     */
    percentage(value, percent) {
        // Handle edge cases
        if (typeof value !== 'number' || typeof percent !== 'number') {
            throw new TypeError('Both arguments must be numbers');
        }
        if (!isFinite(value) || !isFinite(percent)) {
            throw new Error('Arguments must be finite numbers');
        }
        
        const result = (value * percent) / 100;
        this.history.push(`${percent}% of ${value} = ${result}`);
        return result;
    }

    /**
     * Calculate what percent one value is of another
     * @param {number} part - The part value
     * @param {number} whole - The whole value
     * @returns {number} The percentage that part is of whole
     * @example percentOf(20, 200) returns 10
     */
    percentOf(part, whole) {
        // Handle edge cases
        if (typeof part !== 'number' || typeof whole !== 'number') {
            throw new TypeError('Both arguments must be numbers');
        }
        if (!isFinite(part) || !isFinite(whole)) {
            throw new Error('Arguments must be finite numbers');
        }
        if (whole === 0) {
            throw new Error('Cannot calculate percentage of zero');
        }
        
        const result = (part / whole) * 100;
        this.history.push(`${part} is ${result}% of ${whole}`);
        return result;
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
console.log(calc.percentage(200, 10));  // 20
console.log(calc.percentOf(20, 200));   // 10
console.log('History:', calc.getHistory());

module.exports = Calculator;