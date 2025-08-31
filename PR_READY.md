# Pull Request Ready for Creation

## Branch Information
- **Branch Name**: `claude/issue-20-add-a-square-root-function-to-calculator`
- **Base Branch**: `master`
- **Issue**: #20

## PR Title
feat: add square root function to Calculator class

## PR Description
Fixes #20

## Summary
This PR adds a square root function to the Calculator class as requested in issue #20.

### Changes Made:
- ✅ Added `sqrt()` method to the Calculator class
- ✅ Takes one parameter (num) and returns the square root
- ✅ Handles negative numbers appropriately by returning NaN
- ✅ Tracks operations in history with special message for negative inputs
- ✅ Created comprehensive test suite with 7 test cases

### Test Coverage:
The test suite (`test-calculator.js`) includes:
1. Square root of positive number (9 → 3)
2. Square root of zero (0 → 0)
3. Square root of negative number (-4 → NaN)
4. Square root of decimal (2.25 → 1.5)
5. Square root of 1 (1 → 1)
6. Square root of large number (10000 → 100)
7. History tracking verification

All tests are passing ✅

### Example Usage:
```javascript
const calc = new Calculator();
console.log(calc.sqrt(16));  // Output: 4
console.log(calc.sqrt(-4));  // Output: NaN
```

### Files Changed:
- `calculator.js` - Added sqrt() method
- `test-calculator.js` - Created comprehensive test suite

## How to Create the PR
Run the following command to create the pull request:
```bash
gh pr create \
  --title "feat: add square root function to Calculator class" \
  --body "Fixes #20" \
  --base master \
  --head claude/issue-20-add-a-square-root-function-to-calculator
```