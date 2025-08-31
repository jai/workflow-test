// Test file for Calculator class
const Calculator = require('./calculator');

describe('Calculator', () => {
    let calc;

    beforeEach(() => {
        calc = new Calculator();
    });

    describe('add', () => {
        test('should add two positive numbers', () => {
            expect(calc.add(5, 3)).toBe(8);
        });

        test('should add negative numbers', () => {
            expect(calc.add(-5, -3)).toBe(-8);
        });

        test('should record operation in history', () => {
            calc.add(5, 3);
            expect(calc.getHistory()).toContain('5 + 3 = 8');
        });
    });

    describe('divide', () => {
        test('should divide two numbers', () => {
            expect(calc.divide(10, 2)).toBe(5);
        });

        test('should handle division by zero', () => {
            expect(calc.divide(10, 0)).toBe(Infinity);
        });

        test('should record operation in history', () => {
            calc.divide(10, 2);
            expect(calc.getHistory()).toContain('10 / 2 = 5');
        });
    });

    describe('modulo', () => {
        test('should return remainder of division', () => {
            expect(calc.modulo(10, 3)).toBe(1);
            expect(calc.modulo(7, 2)).toBe(1);
            expect(calc.modulo(8, 4)).toBe(0);
        });

        test('should handle negative dividend', () => {
            expect(calc.modulo(-10, 3)).toBe(-1);
        });

        test('should handle negative divisor', () => {
            expect(calc.modulo(10, -3)).toBe(1);
        });

        test('should handle both negative numbers', () => {
            expect(calc.modulo(-10, -3)).toBe(-1);
        });

        test('should throw error for division by zero', () => {
            expect(() => calc.modulo(10, 0)).toThrow('Division by zero: divisor cannot be zero');
        });

        test('should record operation in history', () => {
            calc.modulo(10, 3);
            expect(calc.getHistory()).toContain('10 % 3 = 1');
        });
    });

    describe('mod (alias)', () => {
        test('should work as an alias for modulo', () => {
            expect(calc.mod(10, 3)).toBe(1);
            expect(calc.mod(7, 2)).toBe(1);
        });

        test('should throw error for division by zero', () => {
            expect(() => calc.mod(10, 0)).toThrow('Division by zero: divisor cannot be zero');
        });

        test('should record operation in history using modulo format', () => {
            calc.mod(7, 2);
            expect(calc.getHistory()).toContain('7 % 2 = 1');
        });
    });

    describe('multiply', () => {
        test('should multiply two numbers', () => {
            expect(calc.multiply(4, 7)).toBe(28);
        });

        test('should not record in history', () => {
            calc.multiply(4, 7);
            expect(calc.getHistory()).toHaveLength(0);
        });
    });

    describe('history management', () => {
        test('should maintain history of operations', () => {
            calc.add(5, 3);
            calc.divide(10, 2);
            calc.modulo(10, 3);
            calc.mod(7, 2);
            
            const history = calc.getHistory();
            expect(history).toHaveLength(4);
            expect(history[0]).toBe('5 + 3 = 8');
            expect(history[1]).toBe('10 / 2 = 5');
            expect(history[2]).toBe('10 % 3 = 1');
            expect(history[3]).toBe('7 % 2 = 1');
        });

        test('should clear history', () => {
            calc.add(5, 3);
            calc.modulo(10, 3);
            expect(calc.getHistory()).toHaveLength(2);
            
            calc.clearHistory();
            expect(calc.getHistory()).toHaveLength(0);
        });
    });
});