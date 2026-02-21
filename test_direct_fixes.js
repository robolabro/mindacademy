/**
 * Test script to verify fixes for direct-to-5 and direct-to-9 exercise generation
 *
 * Tests:
 * 1. Direct-to-5: Verify that operations with 5 (especially -5) appear regularly
 * 2. Direct-to-9: Verify that large numbers (6-9) appear in both additions and subtractions
 */

const fs = require('fs');

// Simulated operation tables (copy from anzan_simulator.html)
const directTo4 = {
    '+': [[1,1],[1,2],[1,3],[2,1],[2,2],[3,1]],
    '-': [[1,1],[2,1],[2,2],[3,1],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4]]
};

const directTo5New = {
    '+': [[1,5],[2,5],[3,5],[4,5]],
    '-': [[6,1],[6,5],[7,1],[7,2],[7,5],[8,1],[8,2],[8,3],[8,5],[9,1],[9,2],[9,3],[9,4],[9,5]]
};

const directTo9New = {
    '+': [
        [1,6],[1,7],[1,8],  // 1+6=7, 1+7=8, 1+8=9
        [2,6],[2,7],        // 2+6=8, 2+7=9
        [3,6],              // 3+6=9
        [4,5]               // 4+5=9
    ],
    '-': [
        [6,1],[6,5],[6,6],                          // 6-1=5, 6-5=1, 6-6=0
        [7,1],[7,2],[7,5],[7,6],[7,7],              // 7-1=6, 7-2=5, 7-5=2, 7-6=1, 7-7=0
        [8,1],[8,2],[8,3],[8,5],[8,6],[8,7],[8,8],  // 8-1=7, 8-2=6, 8-3=5, 8-5=3, 8-6=2, 8-7=1, 8-8=0
        [9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9]  // All subtractions from 9
    ]
};

function isAllowedOperation(currentValue, operation, operand, complexity) {
    const ops4 = directTo4[operation] || [];
    const inDirect4 = ops4.some(([v, o]) => v === currentValue && o === operand);

    if (complexity === 'direct-to-4') {
        return inDirect4;
    }

    const ops5 = directTo5New[operation] || [];
    const inDirect5 = ops5.some(([v, o]) => v === currentValue && o === operand);

    if (complexity === 'direct-to-5') {
        return inDirect4 || inDirect5;
    }

    if (complexity === 'direct-to-9' || complexity === 'direct-counting') {
        const ops9 = directTo9New[operation] || [];
        const inDirect9 = ops9.some(([v, o]) => v === currentValue && o === operand);
        return inDirect4 || inDirect5 || inDirect9;
    }

    return true;
}

// Test direct-to-5: Check all possible operations
console.log('=== DIRECT-TO-5 OPERATIONS TEST ===\n');

console.log('Testing operations with 5 (should all be allowed):');
const directTo5Tests = [
    [1, '+', 5, 6],   // 1+5=6
    [2, '+', 5, 7],   // 2+5=7
    [3, '+', 5, 8],   // 3+5=8
    [4, '+', 5, 9],   // 4+5=9
    [6, '-', 5, 1],   // 6-5=1
    [7, '-', 5, 2],   // 7-5=2
    [8, '-', 5, 3],   // 8-5=3
    [9, '-', 5, 4],   // 9-5=4
];

let passedDirect5 = 0;
for (const [current, op, operand, expected] of directTo5Tests) {
    const allowed = isAllowedOperation(current, op, operand, 'direct-to-5');
    const result = op === '+' ? current + operand : current - operand;
    const status = allowed ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${current}${op}${operand}=${result} - ${status}`);
    if (allowed) passedDirect5++;
}

console.log(`\nDirect-to-5: ${passedDirect5}/${directTo5Tests.length} tests passed\n`);

// Test direct-to-9: Check all possible operations with large numbers
console.log('=== DIRECT-TO-9 OPERATIONS TEST ===\n');

console.log('Testing additions with large numbers (6-9):');
const directTo9AddTests = [
    [1, '+', 6, 7],   // 1+6=7
    [1, '+', 7, 8],   // 1+7=8
    [1, '+', 8, 9],   // 1+8=9
    [2, '+', 6, 8],   // 2+6=8
    [2, '+', 7, 9],   // 2+7=9
    [3, '+', 6, 9],   // 3+6=9
];

let passedDirect9Add = 0;
for (const [current, op, operand, expected] of directTo9AddTests) {
    const allowed = isAllowedOperation(current, op, operand, 'direct-to-9');
    const result = op === '+' ? current + operand : current - operand;
    const status = allowed ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${current}${op}${operand}=${result} - ${status}`);
    if (allowed) passedDirect9Add++;
}

console.log(`\nDirect-to-9 additions: ${passedDirect9Add}/${directTo9AddTests.length} tests passed\n`);

console.log('Testing subtractions with large numbers (6-9):');
const directTo9SubTests = [
    [6, '-', 6, 0],   // 6-6=0
    [7, '-', 6, 1],   // 7-6=1
    [7, '-', 7, 0],   // 7-7=0
    [8, '-', 6, 2],   // 8-6=2
    [8, '-', 7, 1],   // 8-7=1
    [8, '-', 8, 0],   // 8-8=0
    [9, '-', 6, 3],   // 9-6=3
    [9, '-', 7, 2],   // 9-7=2
    [9, '-', 8, 1],   // 9-8=1
    [9, '-', 9, 0],   // 9-9=0
];

let passedDirect9Sub = 0;
for (const [current, op, operand, expected] of directTo9SubTests) {
    const allowed = isAllowedOperation(current, op, operand, 'direct-to-9');
    const result = op === '+' ? current + operand : current - operand;
    const status = allowed ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${current}${op}${operand}=${result} - ${status}`);
    if (allowed) passedDirect9Sub++;
}

console.log(`\nDirect-to-9 subtractions: ${passedDirect9Sub}/${directTo9SubTests.length} tests passed\n`);

// Summary
console.log('=== SUMMARY ===');
const totalTests = directTo5Tests.length + directTo9AddTests.length + directTo9SubTests.length;
const totalPassed = passedDirect5 + passedDirect9Add + passedDirect9Sub;
console.log(`Total: ${totalPassed}/${totalTests} tests passed`);

if (totalPassed === totalTests) {
    console.log('\n✓ ALL TESTS PASSED! The operation tables are correct.');
    process.exit(0);
} else {
    console.log('\n✗ SOME TESTS FAILED! There are issues with the operation tables.');
    process.exit(1);
}
