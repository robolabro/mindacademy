// Test for requiresSmallFriendsFormula fix
// This tests that the function correctly identifies which operations require Small Friends formulas

function requiresSmallFriendsFormula(currentValue, operation, operand) {
    // For multi-digit numbers, work with last digits only
    const currentLastDigit = currentValue % 10;
    const operandLastDigit = operand % 10;
    const result = operation === '+' ? currentLastDigit + operandLastDigit : currentLastDigit - operandLastDigit;

    if (operation === '+') {
        // Adding from 1-4 to get 5-9 requires Small Friends formula
        // Formula is needed when transitioning from lower beads (1-4) to heaven bead region (5-9)
        // Example: 4+1=5 requires +1 = +5-4 (move heaven up, remove all 4 lower beads)
        // CRITICAL: Must check that OPERAND is also 1-4, not just the current value
        // Otherwise operations like 1+5=6, 1+6=7 are incorrectly considered as requiring formula
        if (currentLastDigit >= 1 && currentLastDigit <= 4 && operandLastDigit >= 1 && operandLastDigit <= 4 && result >= 5 && result <= 9) {
            return true;
        }
    } else if (operation === '-') {
        // Subtracting from 5 to get 1-4 requires Small Friends
        if (currentLastDigit === 5 && operandLastDigit >= 1 && operandLastDigit <= 4) {
            return true;
        }
        // Subtracting from 6-9 where we need to remove the heaven bead
        if (currentLastDigit >= 6 && currentLastDigit <= 9 && result >= 1 && result <= 4) {
            const lowerBeadsUsed = currentLastDigit - 5;
            // CRITICAL: Subtracting 5 from 6-9 is DIRECT (just remove heaven bead)
            // Only operations subtracting 1-4 where we need more than available lower beads require formula
            // Example: 6-2=4 requires formula (6=5+1, can't subtract 2 from 1 lower bead)
            // Example: 6-5=1 is DIRECT (just remove heaven bead, 1 lower bead remains)
            if (operandLastDigit === 5) {
                return false; // Subtracting 5 is always direct
            }
            // If we need to subtract more than the lower beads we have (and operand is 1-4)
            return operandLastDigit >= 1 && operandLastDigit <= 4 && operandLastDigit > lowerBeadsUsed;
        }
    }

    return false;
}

console.log('=== Testing requiresSmallFriendsFormula Fix ===\n');

// Test cases for Addition
console.log('ADDITION Tests:');
console.log('Operations that SHOULD require Small Friends formula:');
const shouldRequireFormula = [
    [4, '+', 1, 5],  // +1 formula: 4+1=5
    [3, '+', 2, 5],  // +2 formula: 3+2=5
    [4, '+', 2, 6],  // +2 formula: 4+2=6
    [2, '+', 3, 5],  // +3 formula: 2+3=5
    [3, '+', 3, 6],  // +3 formula: 3+3=6
    [4, '+', 3, 7],  // +3 formula: 4+3=7
    [1, '+', 4, 5],  // +4 formula: 1+4=5
    [2, '+', 4, 6],  // +4 formula: 2+4=6
    [3, '+', 4, 7],  // +4 formula: 3+4=7
    [4, '+', 4, 8],  // +4 formula: 4+4=8
];

let passed = 0;
let failed = 0;

for (const [current, op, operand, expected] of shouldRequireFormula) {
    const requires = requiresSmallFriendsFormula(current, op, operand);
    const status = requires ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${current}${op}${operand}=${expected} - requires formula: ${requires} - ${status}`);
    if (requires) passed++; else failed++;
}

console.log('\nOperations that should NOT require Small Friends formula (direct calculations):');
const shouldNotRequireFormula = [
    [1, '+', 5, 6],  // Direct: 1+5=6
    [2, '+', 5, 7],  // Direct: 2+5=7
    [3, '+', 5, 8],  // Direct: 3+5=8
    [4, '+', 5, 9],  // Direct: 4+5=9
    [1, '+', 6, 7],  // Direct: 1+6=7
    [1, '+', 7, 8],  // Direct: 1+7=8
    [1, '+', 8, 9],  // Direct: 1+8=9
    [2, '+', 6, 8],  // Direct: 2+6=8
    [2, '+', 7, 9],  // Direct: 2+7=9
    [3, '+', 6, 9],  // Direct: 3+6=9
    [5, '+', 1, 6],  // Direct: 5+1=6
    [5, '+', 2, 7],  // Direct: 5+2=7
    [5, '+', 3, 8],  // Direct: 5+3=8
    [5, '+', 4, 9],  // Direct: 5+4=9
    [1, '+', 1, 2],  // Direct: 1+1=2
    [1, '+', 2, 3],  // Direct: 1+2=3
    [2, '+', 1, 3],  // Direct: 2+1=3
];

for (const [current, op, operand, expected] of shouldNotRequireFormula) {
    const requires = requiresSmallFriendsFormula(current, op, operand);
    const status = !requires ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${current}${op}${operand}=${expected} - requires formula: ${requires} - ${status}`);
    if (!requires) passed++; else failed++;
}

// Test cases for Subtraction
console.log('\n\nSUBTRACTION Tests:');
console.log('Operations that SHOULD require Small Friends formula:');
const shouldRequireSubFormula = [
    [5, '-', 1, 4],  // -1 formula: 5-1=4
    [5, '-', 2, 3],  // -2 formula: 5-2=3
    [6, '-', 2, 4],  // -2 formula: 6-2=4
    [5, '-', 3, 2],  // -3 formula: 5-3=2
    [6, '-', 3, 3],  // -3 formula: 6-3=3
    [7, '-', 3, 4],  // -3 formula: 7-3=4
    [5, '-', 4, 1],  // -4 formula: 5-4=1
    [6, '-', 4, 2],  // -4 formula: 6-4=2
    [7, '-', 4, 3],  // -4 formula: 7-4=3
    [8, '-', 4, 4],  // -4 formula: 8-4=4
];

for (const [current, op, operand, expected] of shouldRequireSubFormula) {
    const requires = requiresSmallFriendsFormula(current, op, operand);
    const status = requires ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${current}${op}${operand}=${expected} - requires formula: ${requires} - ${status}`);
    if (requires) passed++; else failed++;
}

console.log('\nOperations that should NOT require Small Friends formula (direct calculations):');
const shouldNotRequireSubFormula = [
    [6, '-', 1, 5],  // Direct: 6-1=5
    [7, '-', 1, 6],  // Direct: 7-1=6
    [8, '-', 1, 7],  // Direct: 8-1=7
    [9, '-', 1, 8],  // Direct: 9-1=8
    [6, '-', 5, 1],  // Direct: 6-5=1
    [7, '-', 5, 2],  // Direct: 7-5=2
    [8, '-', 5, 3],  // Direct: 8-5=3
    [9, '-', 5, 4],  // Direct: 9-5=4
    [7, '-', 2, 5],  // Direct: 7-2=5
    [8, '-', 2, 6],  // Direct: 8-2=6
    [9, '-', 2, 7],  // Direct: 9-2=7
    [8, '-', 3, 5],  // Direct: 8-3=5
    [9, '-', 3, 6],  // Direct: 9-3=6
    [9, '-', 4, 5],  // Direct: 9-4=5
    [2, '-', 1, 1],  // Direct: 2-1=1
    [3, '-', 1, 2],  // Direct: 3-1=2
    [4, '-', 1, 3],  // Direct: 4-1=3
];

for (const [current, op, operand, expected] of shouldNotRequireSubFormula) {
    const requires = requiresSmallFriendsFormula(current, op, operand);
    const status = !requires ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${current}${op}${operand}=${expected} - requires formula: ${requires} - ${status}`);
    if (!requires) passed++; else failed++;
}

console.log(`\n\n=== SUMMARY ===`);
console.log(`Total tests: ${passed + failed}`);
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log(`Success rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

if (failed === 0) {
    console.log('\n✓ All tests passed! The fix is working correctly.');
} else {
    console.log('\n✗ Some tests failed. Please review the fix.');
}
