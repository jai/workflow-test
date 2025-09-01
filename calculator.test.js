// Test file for Calculator module
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

        test('should add mixed positive and negative', () => {
            expect(calc.add(5, -3)).toBe(2);
        });

        test('should save to history', () => {
            calc.add(5, 3);
            expect(calc.getHistory()).toContain('5 + 3 = 8');
        });
    });

    describe('subtract', () => {
        test('should subtract two positive numbers', () => {
            expect(calc.subtract(10, 4)).toBe(6);
        });

        test('should subtract negative numbers', () => {
            expect(calc.subtract(-5, -3)).toBe(-2);
        });

        test('should subtract mixed positive and negative', () => {
            expect(calc.subtract(5, -3)).toBe(8);
        });

        test('should handle when result is negative', () => {
            expect(calc.subtract(3, 5)).toBe(-2);
        });

        test('should save to history', () => {
            calc.subtract(10, 4);
            expect(calc.getHistory()).toContain('10 - 4 = 6');
        });
    });

    describe('divide', () => {
        test('should divide two numbers', () => {
            expect(calc.divide(10, 2)).toBe(5);
        });

        test('should handle division by negative', () => {
            expect(calc.divide(10, -2)).toBe(-5);
        });

        test('should return Infinity for division by zero', () => {
            expect(calc.divide(10, 0)).toBe(Infinity);
        });

        test('should save to history', () => {
            calc.divide(10, 2);
            expect(calc.getHistory()).toContain('10 / 2 = 5');
        });
    });

    describe('multiply', () => {
        test('should multiply two positive numbers', () => {
            expect(calc.multiply(4, 7)).toBe(28);
        });

        test('should multiply with zero', () => {
            expect(calc.multiply(5, 0)).toBe(0);
        });

        test('should multiply negative numbers', () => {
            expect(calc.multiply(-3, -4)).toBe(12);
        });

        test('should not save to history', () => {
            calc.multiply(4, 7);
            expect(calc.getHistory()).toHaveLength(0);
        });
    });

    describe('percentage', () => {
        test('should calculate percentage correctly', () => {
            expect(calc.percentage(200, 10)).toBe(20);
        });

        test('should handle 0% correctly', () => {
            expect(calc.percentage(100, 0)).toBe(0);
        });

        test('should handle 100% correctly', () => {
            expect(calc.percentage(50, 100)).toBe(50);
        });

        test('should handle percentages over 100%', () => {
            expect(calc.percentage(100, 150)).toBe(150);
        });

        test('should handle decimal percentages', () => {
            expect(calc.percentage(100, 12.5)).toBe(12.5);
        });

        test('should handle negative values', () => {
            expect(calc.percentage(-100, 10)).toBe(-10);
        });

        test('should handle negative percentages', () => {
            expect(calc.percentage(100, -10)).toBe(-10);
        });

        test('should throw TypeError for non-number arguments', () => {
            expect(() => calc.percentage('100', 10)).toThrow(TypeError);
            expect(() => calc.percentage(100, '10')).toThrow(TypeError);
            expect(() => calc.percentage(null, 10)).toThrow(TypeError);
            expect(() => calc.percentage(100, undefined)).toThrow(TypeError);
        });

        test('should throw Error for infinite values', () => {
            expect(() => calc.percentage(Infinity, 10)).toThrow('Arguments must be finite numbers');
            expect(() => calc.percentage(100, Infinity)).toThrow('Arguments must be finite numbers');
            expect(() => calc.percentage(NaN, 10)).toThrow('Arguments must be finite numbers');
        });

        test('should save to history', () => {
            calc.percentage(200, 10);
            expect(calc.getHistory()).toContain('10% of 200 = 20');
        });
    });

    describe('percentOf', () => {
        test('should calculate what percent one value is of another', () => {
            expect(calc.percentOf(20, 200)).toBe(10);
        });

        test('should handle when part equals whole', () => {
            expect(calc.percentOf(100, 100)).toBe(100);
        });

        test('should handle when part is zero', () => {
            expect(calc.percentOf(0, 100)).toBe(0);
        });

        test('should handle when part is greater than whole', () => {
            expect(calc.percentOf(150, 100)).toBe(150);
        });

        test('should handle decimal values', () => {
            expect(calc.percentOf(12.5, 100)).toBe(12.5);
        });

        test('should handle negative part', () => {
            expect(calc.percentOf(-20, 100)).toBe(-20);
        });

        test('should handle negative whole', () => {
            expect(calc.percentOf(20, -100)).toBe(-20);
        });

        test('should throw Error when whole is zero', () => {
            expect(() => calc.percentOf(20, 0)).toThrow('Cannot calculate percentage of zero');
        });

        test('should throw TypeError for non-number arguments', () => {
            expect(() => calc.percentOf('20', 200)).toThrow(TypeError);
            expect(() => calc.percentOf(20, '200')).toThrow(TypeError);
            expect(() => calc.percentOf(null, 200)).toThrow(TypeError);
            expect(() => calc.percentOf(20, undefined)).toThrow(TypeError);
        });

        test('should throw Error for infinite values', () => {
            expect(() => calc.percentOf(Infinity, 200)).toThrow('Arguments must be finite numbers');
            expect(() => calc.percentOf(20, Infinity)).toThrow('Arguments must be finite numbers');
            expect(() => calc.percentOf(NaN, 200)).toThrow('Arguments must be finite numbers');
        });

        test('should save to history', () => {
            calc.percentOf(20, 200);
            expect(calc.getHistory()).toContain('20 is 10% of 200');
        });
    });

    describe('square', () => {
        test('should calculate square of positive number', () => {
            expect(calc.square(5)).toBe(25);
        });

        test('should calculate square of zero', () => {
            expect(calc.square(0)).toBe(0);
        });

        test('should calculate square of negative number', () => {
            expect(calc.square(-3)).toBe(9);
        });

        test('should handle decimal numbers', () => {
            expect(calc.square(2.5)).toBe(6.25);
        });

        test('should handle very small numbers', () => {
            expect(calc.square(0.1)).toBeCloseTo(0.01);
        });

        test('should handle large numbers', () => {
            expect(calc.square(100)).toBe(10000);
        });

        test('should throw TypeError for non-number arguments', () => {
            expect(() => calc.square('5')).toThrow(TypeError);
            expect(() => calc.square(null)).toThrow(TypeError);
            expect(() => calc.square(undefined)).toThrow(TypeError);
            expect(() => calc.square({})).toThrow(TypeError);
            expect(() => calc.square([])).toThrow(TypeError);
        });

        test('should throw Error for infinite values', () => {
            expect(() => calc.square(Infinity)).toThrow('Argument must be a finite number');
            expect(() => calc.square(-Infinity)).toThrow('Argument must be a finite number');
            expect(() => calc.square(NaN)).toThrow('Argument must be a finite number');
        });

        test('should save to history with proper format', () => {
            calc.square(5);
            expect(calc.getHistory()).toContain('5² = 25');
        });

        test('should save negative number squares to history', () => {
            calc.square(-4);
            expect(calc.getHistory()).toContain('-4² = 16');
        });
    });

    describe('cube', () => {
        test('should calculate cube of positive number', () => {
            expect(calc.cube(3)).toBe(27);
        });

        test('should calculate cube of zero', () => {
            expect(calc.cube(0)).toBe(0);
        });

        test('should calculate cube of negative number', () => {
            expect(calc.cube(-2)).toBe(-8);
        });

        test('should handle decimal numbers', () => {
            expect(calc.cube(2.5)).toBe(15.625);
        });

        test('should handle very small numbers', () => {
            expect(calc.cube(0.1)).toBeCloseTo(0.001);
        });

        test('should handle large numbers', () => {
            expect(calc.cube(10)).toBe(1000);
        });

        test('should throw TypeError for non-number arguments', () => {
            expect(() => calc.cube('3')).toThrow(TypeError);
            expect(() => calc.cube(null)).toThrow(TypeError);
            expect(() => calc.cube(undefined)).toThrow(TypeError);
            expect(() => calc.cube({})).toThrow(TypeError);
            expect(() => calc.cube([])).toThrow(TypeError);
        });

        test('should throw Error for infinite values', () => {
            expect(() => calc.cube(Infinity)).toThrow('Argument must be a finite number');
            expect(() => calc.cube(-Infinity)).toThrow('Argument must be a finite number');
            expect(() => calc.cube(NaN)).toThrow('Argument must be a finite number');
        });

        test('should save to history with proper format', () => {
            calc.cube(3);
            expect(calc.getHistory()).toContain('3³ = 27');
        });

        test('should save negative number cubes to history', () => {
            calc.cube(-3);
            expect(calc.getHistory()).toContain('-3³ = -27');
        });
    });

    describe('history management', () => {
        test('should maintain history across multiple operations', () => {
            calc.add(5, 3);
            calc.subtract(10, 4);
            calc.divide(10, 2);
            calc.percentage(200, 10);
            calc.percentOf(20, 200);
            calc.square(5);
            calc.cube(3);
            
            const history = calc.getHistory();
            expect(history).toHaveLength(7);
            expect(history[0]).toBe('5 + 3 = 8');
            expect(history[1]).toBe('10 - 4 = 6');
            expect(history[2]).toBe('10 / 2 = 5');
            expect(history[3]).toBe('10% of 200 = 20');
            expect(history[4]).toBe('20 is 10% of 200');
            expect(history[5]).toBe('5² = 25');
            expect(history[6]).toBe('3³ = 27');
        });

        test('should clear history', () => {
            calc.add(5, 3);
            calc.percentage(100, 25);
            expect(calc.getHistory()).toHaveLength(2);
            
            calc.clearHistory();
            expect(calc.getHistory()).toHaveLength(0);
        });
    });
});