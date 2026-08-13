// Test for multi-digit direct-to-9 allowed operations

// Copy of the updated isAllowedOperation function
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
            [6,1],[6,2],[6,3],[6,4],[6,5],[6,6],
            [7,1],[7,2],[7,3],[7,4],[7,5],[7,6],[7,7],
            [8,1],[8,2],[8,3],[8,4],[8,5],[8,6],[8,7],[8,8],
            [9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9]
        ]
    };

    function isSingleDigitAllowed(currentDigit, operandDigit, operation, complexity) {
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

        return true;
    }

    // For multi-digit numbers, check each digit independently
    if (currentValue > 9 || operand > 9) {
        const currentUnitsDigit = currentValue % 10;
        const operandUnitsDigit = operand % 10;

        if (operation === '+') {
            if (currentUnitsDigit + operandUnitsDigit >= 10) {
                return false; // Carry between digits
            }
        } else {
            if (currentUnitsDigit < operandUnitsDigit) {
                return false; // Borrow between digits
            }
        }

        // Check units digit operation
        if (!isSingleDigitAllowed(currentUnitsDigit, operandUnitsDigit, operation, complexity)) {
            return false;
        }

        // Check tens digit operation (if both numbers have tens digits)
        if (currentValue >= 10 && operand >= 10) {
            const currentTensDigit = Math.floor(currentValue / 10) % 10;
            const operandTensDigit = Math.floor(operand / 10) % 10;

            if (!isSingleDigitAllowed(currentTensDigit, operandTensDigit, operation, complexity)) {
                return false;
            }
        }

        return true;
    }

    // Single-digit case
    return isSingleDigitAllowed(currentValue, operand, operation, complexity);
}

// Test cases for multi-digit direct-counting
const testCases = [
    // Two-digit + two-digit that SHOULD work (each digit operation is valid for direct-to-9)
    { current: 66, op: '+', term: 11, expected: true, desc: "66 + 11 (6+1 valid, 6+1 valid)" },
    { current: 79, op: '-', term: 22, expected: true, desc: "79 - 22 (9-2 valid, 7-2 valid)" },
    { current: 79, op: '-', term: 11, expected: true, desc: "79 - 11 (9-1 valid, 7-1 valid)" },
    { current: 66, op: '+', term: 22, expected: true, desc: "66 + 22 (6+2 valid, 6+2 valid)" },
    { current: 77, op: '+', term: 11, expected: true, desc: "77 + 11 (7+1 valid, 7+1 valid)" },
    { current: 44, op: '+', term: 55, expected: true, desc: "44 + 55 (4+5 valid from direct-to-5, 4+5 valid)" },

    // Two-digit + one-digit (units only)
    { current: 44, op: '+', term: 5, expected: true, desc: "44 + 5 (4+5 valid from direct-to-5)" },
    { current: 66, op: '+', term: 3, expected: true, desc: "66 + 3 (6+3 valid from direct-to-9)" },
    { current: 79, op: '-', term: 5, expected: true, desc: "79 - 5 (9-5 valid)" },

    // Should fail: carry between digits
    { current: 45, op: '+', term: 26, expected: false, desc: "45 + 26 (5+6=11 causes carry)" },
    { current: 79, op: '+', term: 11, expected: false, desc: "79 + 11 (9+1=10 causes carry)" },

    // Should fail: borrow between digits
    { current: 41, op: '-', term: 22, expected: false, desc: "41 - 22 (1<2 causes borrow)" },

    // Should fail: invalid digit operation (requires Small Friends formula)
    { current: 44, op: '+', term: 22, expected: false, desc: "44 + 22 (4+2 requires Small Friends)" },
    { current: 44, op: '+', term: 21, expected: false, desc: "44 + 21 (4+1 requires Small Friends)" },
    { current: 44, op: '+', term: 32, expected: false, desc: "44 + 32 (4+2 requires Small Friends)" },
];

console.log("Testing multi-digit allowed operations for direct-counting:\n");

let passed = 0;
let failed = 0;

testCases.forEach(test => {
    const result = isAllowedOperation(test.current, test.op, test.term, 'direct-counting');
    const status = result === test.expected ? '✓ PASS' : '✗ FAIL';

    if (result === test.expected) {
        passed++;
    } else {
        failed++;
    }

    console.log(`${status}: ${test.desc}`);
    console.log(`  ${test.current} ${test.op} ${test.term} = ${test.current + (test.op === '+' ? test.term : -test.term)}`);
    console.log(`  Expected: ${test.expected}, Got: ${result}\n`);
});

console.log(`\nResults: ${passed} passed, ${failed} failed out of ${testCases.length} tests`);

// Now let's count how many valid operations exist for some problematic values
console.log("\n\n=== Counting valid operations for problematic values ===\n");

function countValidOps(currentResult, complexity) {
    const validOps = [];
    const maxLimit = complexity === 'direct-counting' ? 99 : 9; // For 2-digit

    // Try all possible terms from 1 to 9 (single digit terms)
    for (let term = 1; term <= 9; term++) {
        // Try addition
        const addResult = currentResult + term;
        if (addResult >= 1 && addResult <= maxLimit &&
            isAllowedOperation(currentResult, '+', term, complexity)) {
            validOps.push({ op: '+', term: term });
        }

        // Try subtraction
        const subResult = currentResult - term;
        if (subResult >= 0 && subResult <= maxLimit &&
            isAllowedOperation(currentResult, '-', term, complexity)) {
            validOps.push({ op: '-', term: term });
        }
    }

    // Also try two-digit terms (11-99)
    for (let term = 11; term <= 99; term++) {
        // Try addition
        const addResult = currentResult + term;
        if (addResult >= 1 && addResult <= maxLimit &&
            isAllowedOperation(currentResult, '+', term, complexity)) {
            validOps.push({ op: '+', term: term });
        }

        // Try subtraction
        const subResult = currentResult - term;
        if (subResult >= 0 && subResult <= maxLimit &&
            isAllowedOperation(currentResult, '-', term, complexity)) {
            validOps.push({ op: '-', term: term });
        }
    }

    return validOps;
}

const problematicValues = [44, 60, 68, 72, 79, 95, 22, 21];

problematicValues.forEach(value => {
    const validOps = countValidOps(value, 'direct-counting');
    console.log(`currentResult=${value}: Found ${validOps.length} valid operations`);
    if (validOps.length > 0) {
        const examples = validOps.slice(0, 5).map(o => `${o.op}${o.term}`).join(', ');
        console.log(`  Examples: ${examples}${validOps.length > 5 ? ', ...' : ''}`);
    }
    console.log();
});
