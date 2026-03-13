// Test script for Small Friends +1 formula generation
// This tests the updated logic that allows both 4+1 and 1+4

// Copy relevant functions from anzan_simulator.html for testing

function requiresSmallFriendsFormula(currentValue, operation, operand) {
    const currentLastDigit = currentValue % 10;
    const operandLastDigit = operand % 10;
    const result = operation === '+' ? currentLastDigit + operandLastDigit : currentLastDigit - operandLastDigit;

    if (operation === '+') {
        if (currentLastDigit >= 1 && currentLastDigit <= 4 && operandLastDigit >= 1 && operandLastDigit <= 4 && result >= 5 && result <= 9) {
            return true;
        }
    } else if (operation === '-') {
        if (currentLastDigit === 5 && operandLastDigit >= 1 && operandLastDigit <= 4) {
            return true;
        }
        if (currentLastDigit >= 6 && currentLastDigit <= 9 && result >= 1 && result <= 4) {
            const lowerBeadsUsed = currentLastDigit - 5;
            if (operandLastDigit === 5) {
                return false;
            }
            return operandLastDigit >= 1 && operandLastDigit <= 4 && operandLastDigit > lowerBeadsUsed;
        }
    }

    return false;
}

function isAllowedOperation(currentValue, operation, operand, complexity) {
    const directTo4 = {
        '+': [[1,1],[1,2],[1,3],[2,1],[2,2],[3,1]],
        '-': [[1,1],[2,1],[2,2],[3,1],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4]]
    };
    const directTo5New = {
        '+': [[1,5],[2,5],[3,5],[4,5],[5,1],[5,2],[5,3],[5,4]],
        '-': [[5,5],[6,1],[6,5],[7,1],[7,2],[7,5],[8,1],[8,2],[8,3],[8,5],[9,1],[9,2],[9,3],[9,4],[9,5]]
    };
    const directTo9New = {
        '+': [
            [1,6],[1,7],[1,8],
            [2,6],[2,7],
            [3,6],
            [6,1],[6,2],[6,3],
            [7,1],[7,2],
            [8,1]
        ],
        '-': [
            [6,1],[6,5],[6,6],
            [7,1],[7,2],[7,5],[7,6],[7,7],
            [8,1],[8,2],[8,3],[8,5],[8,6],[8,7],[8,8],
            [9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9]
        ]
    };

    // UPDATED: Allow both commutative forms
    const smallPlus1 = {
        '+': [[4,1],[1,4]]  // Both 4+1 and 1+4
    };

    function isSingleDigitAllowed(currentDigit, operandDigit, operation, complexity) {
        if (currentDigit === 0 && operation === '+') {
            if (complexity === 'direct-to-4') {
                return operandDigit >= 1 && operandDigit <= 4;
            }
            if (complexity === 'direct-to-5') {
                return operandDigit >= 1 && operandDigit <= 5;
            }
            if (complexity === 'direct-to-9' || complexity === 'direct-counting') {
                return operandDigit >= 1 && operandDigit <= 9;
            }
        }
        if (currentDigit === 0 && operation === '-') {
            return false;
        }

        const ops4 = directTo4[operation] || [];
        const inDirect4 = ops4.some(([v, o]) => v === currentDigit && o === operandDigit);

        if (complexity === 'direct-to-4') {
            return inDirect4;
        }

        const ops5 = directTo5New[operation] || [];
        const inDirect5 = ops5.some(([v, o]) => v === currentDigit && o === operandDigit);

        if (complexity === 'direct-to-5') {
            return inDirect4 || inDirect5;
        }

        if (complexity === 'direct-to-9' || complexity === 'direct-counting') {
            const ops9 = directTo9New[operation] || [];
            const inDirect9 = ops9.some(([v, o]) => v === currentDigit && o === operandDigit);
            return inDirect4 || inDirect5 || inDirect9;
        }

        if (complexity.startsWith('small-')) {
            const ops9 = directTo9New[operation] || [];
            const inDirect9 = ops9.some(([v, o]) => v === currentDigit && o === operandDigit);
            if (inDirect9 || inDirect4 || inDirect5) {
                return true;
            }

            if (complexity === 'small-plus-1') {
                const ops = smallPlus1[operation] || [];
                return ops.some(([v, o]) => v === currentDigit && o === operandDigit);
            }
        }

        return false;
    }

    const currentDigit = currentValue % 10;
    const operandDigit = operand % 10;
    return isSingleDigitAllowed(currentDigit, operandDigit, operation, complexity);
}

console.log('=== Testing Small Friends +1 Formula Generation ===\n');

// Test 1: Verify both 4+1 and 1+4 are now allowed
console.log('Test 1: Verify both 4+1 and 1+4 are allowed for small-plus-1');
const test1_4plus1 = isAllowedOperation(4, '+', 1, 'small-plus-1');
const test1_1plus4 = isAllowedOperation(1, '+', 4, 'small-plus-1');
console.log(`  4+1 is allowed: ${test1_4plus1} ${test1_4plus1 ? '✓' : '✗'}`);
console.log(`  1+4 is allowed: ${test1_1plus4} ${test1_1plus4 ? '✓' : '✗'}`);
console.log(`  ${test1_4plus1 && test1_1plus4 ? '✓ PASS' : '✗ FAIL'}\n`);

// Test 2: Verify formula detection
console.log('Test 2: Verify formula requirement detection');
const test2_4plus1_requires = requiresSmallFriendsFormula(4, '+', 1);
const test2_1plus4_requires = requiresSmallFriendsFormula(1, '+', 4);
console.log(`  4+1 requires formula: ${test2_4plus1_requires} ${test2_4plus1_requires ? '✓' : '✗'}`);
console.log(`  1+4 requires formula: ${test2_1plus4_requires} ${test2_1plus4_requires ? '✓' : '✗'}`);
console.log(`  ${test2_4plus1_requires && test2_1plus4_requires ? '✓ PASS' : '✗ FAIL'}\n`);

// Test 3: Verify direct operations are still allowed
console.log('Test 3: Verify direct operations are still allowed');
const test3_1plus1 = isAllowedOperation(1, '+', 1, 'small-plus-1');
const test3_5plus1 = isAllowedOperation(5, '+', 1, 'small-plus-1');
const test3_6plus1 = isAllowedOperation(6, '+', 1, 'small-plus-1');
console.log(`  1+1 is allowed: ${test3_1plus1} ${test3_1plus1 ? '✓' : '✗'}`);
console.log(`  5+1 is allowed: ${test3_5plus1} ${test3_5plus1 ? '✓' : '✗'}`);
console.log(`  6+1 is allowed: ${test3_6plus1} ${test3_6plus1 ? '✓' : '✗'}`);
console.log(`  ${test3_1plus1 && test3_5plus1 && test3_6plus1 ? '✓ PASS' : '✗ FAIL'}\n`);

// Test 4: Generate sample exercise paths
console.log('Test 4: Sample exercise generation paths');
console.log('  Example exercise: 4 + 1 - 1 + 1 + 1');
let current = 4;
console.log(`  Start: ${current}`);
console.log(`  ${current} + 1 = 5 (uses formula 4+1) ${requiresSmallFriendsFormula(current, '+', 1) ? '✓ formula' : '✗ direct'}`);
current = 5;
console.log(`  ${current} - 1 = 4 (uses formula 5-1) ${requiresSmallFriendsFormula(current, '-', 1) ? '✓ formula' : 'direct'}`);
current = 4;
console.log(`  ${current} + 1 = 5 (uses formula 4+1) ${requiresSmallFriendsFormula(current, '+', 1) ? '✓ formula' : '✗ direct'}`);
current = 5;
console.log(`  ${current} + 1 = 6 (direct) ${requiresSmallFriendsFormula(current, '+', 1) ? 'formula' : '✓ direct'}`);
console.log('');

console.log('  Example exercise: 1 + 4 + 1 - 1 + 1');
current = 1;
console.log(`  Start: ${current}`);
console.log(`  ${current} + 4 = 5 (uses formula 1+4) ${requiresSmallFriendsFormula(current, '+', 4) ? '✓ formula' : '✗ direct'}`);
current = 5;
console.log(`  ${current} + 1 = 6 (direct) ${requiresSmallFriendsFormula(current, '+', 1) ? 'formula' : '✓ direct'}`);
current = 6;
console.log(`  ${current} - 1 = 5 (direct) ${requiresSmallFriendsFormula(current, '-', 1) ? 'formula' : '✓ direct'}`);
current = 5;
console.log(`  ${current} + 1 = 6 (direct) ${requiresSmallFriendsFormula(current, '+', 1) ? 'formula' : '✓ direct'}`);
console.log('');

// Summary
console.log('=== Summary ===');
const allPassed = test1_4plus1 && test1_1plus4 && test2_4plus1_requires && test2_1plus4_requires &&
                  test3_1plus1 && test3_5plus1 && test3_6plus1;
console.log(allPassed ? '✓ All tests passed!' : '✗ Some tests failed');
console.log('');
console.log('With the updated logic, both 4+1 and 1+4 are now allowed,');
console.log('making it much easier to generate valid exercises for small-plus-1.');
