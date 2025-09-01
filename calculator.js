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

    subtract(a, b) {
        const result = a - b;
        this.history.push(`${a} - ${b} = ${result}`);
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

    /**
     * Calculate the square of a number
     * @param {number} n - The number to square
     * @returns {number} The square of the number
     * @example square(5) returns 25
     */
    square(n) {
        // Handle edge cases
        if (typeof n !== 'number') {
            throw new TypeError('Argument must be a number');
        }
        if (!isFinite(n)) {
            throw new Error('Argument must be a finite number');
        }
        
        const result = n * n;
        this.history.push(`${n}² = ${result}`);
        return result;
    }

    /**
     * Calculate the nth root of a number
     * @param {number} value - The value to find the root of
     * @param {number} n - The degree of the root (default: 2 for square root)
     * @returns {number} The nth root of the value
     * @example root(27, 3) returns 3 (cube root of 27)
     * @example root(16) returns 4 (square root of 16)
     */
    root(value, n = 2) {
        // Handle edge cases
        if (typeof value !== 'number' || typeof n !== 'number') {
            throw new TypeError('Both arguments must be numbers');
        }
        if (!isFinite(value) || !isFinite(n)) {
            throw new Error('Arguments must be finite numbers');
        }
        if (n === 0) {
            throw new Error('Root degree cannot be zero');
        }
        if (value < 0 && n % 2 === 0) {
            throw new Error('Cannot calculate even root of negative number');
        }
        
        // Calculate nth root using Math.pow with fractional exponent
        // For negative values with odd n, handle sign separately
        let result;
        if (value < 0 && n % 2 !== 0) {
            result = -Math.pow(Math.abs(value), 1 / n);
        } else {
            result = Math.pow(value, 1 / n);
        }
        
        // Format history message based on root degree
        if (n === 2) {
            this.history.push(`√${value} = ${result}`);
        } else if (n === 3) {
            this.history.push(`∛${value} = ${result}`);
        } else {
            this.history.push(`${n}√${value} = ${result}`);
        }
        
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
console.log(calc.subtract(10, 4));
console.log(calc.divide(10, 2));
console.log(calc.multiply(4, 7));
console.log(calc.percentage(200, 10));  // 20
console.log(calc.percentOf(20, 200));   // 10
console.log(calc.square(5));            // 25
console.log(calc.root(16));             // 4 (square root)
console.log(calc.root(27, 3));          // 3 (cube root)
console.log('History:', calc.getHistory());

module.exports = Calculator;