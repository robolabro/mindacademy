// Count valid operations for 60 with the new logic

// Copy of the UPDATED isAllowedOperation function
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
        // Special case: Starting from 0
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

        return true;
    }

    // For multi-digit numbers, check each digit independently
    if (currentValue > 9 || operand > 9) {
        const currentUnitsDigit = currentValue % 10;
        const operandUnitsDigit = operand % 10;

        if (operation === '+') {
            if (currentUnitsDigit + operandUnitsDigit >= 10) {
                return false;
            }
        } else {
            if (currentUnitsDigit < operandUnitsDigit) {
                return false;
            }
        }

        if (!isSingleDigitAllowed(currentUnitsDigit, operandUnitsDigit, operation, complexity)) {
            return false;
        }

        if (currentValue >= 10 && operand >= 10) {
            const currentTensDigit = Math.floor(currentValue / 10) % 10;
            const operandTensDigit = Math.floor(operand / 10) % 10;

            if (!isSingleDigitAllowed(currentTensDigit, operandTensDigit, operation, complexity)) {
                return false;
            }
        }

        return true;
    }

    return isSingleDigitAllowed(currentValue, operand, operation, complexity);
}

function countValidOps(currentResult, complexity) {
    const validOps = [];
    const maxLimit = 99; // For 2-digit

    // Try single-digit terms (1-9)
    for (let term = 1; term <= 9; term++) {
        const addResult = currentResult + term;
        if (addResult >= 1 && addResult <= maxLimit &&
            isAllowedOperation(currentResult, '+', term, complexity)) {
            validOps.push({ op: '+', term: term });
        }

        const subResult = currentResult - term;
        if (subResult >= 0 && subResult <= maxLimit &&
            isAllowedOperation(currentResult, '-', term, complexity)) {
            validOps.push({ op: '-', term: term });
        }
    }

    // Try two-digit terms (11-99, skip those ending with 0)
    for (let term = 11; term <= 99; term++) {
        if (term % 10 === 0) continue;

        const addResult = currentResult + term;
        if (addResult >= 1 && addResult <= maxLimit &&
            isAllowedOperation(currentResult, '+', term, complexity)) {
            validOps.push({ op: '+', term: term });
        }

        const subResult = currentResult - term;
        if (subResult >= 0 && subResult <= maxLimit &&
            isAllowedOperation(currentResult, '-', term, complexity)) {
            validOps.push({ op: '-', term: term });
        }
    }

    return validOps;
}

console.log("Counting valid operations for currentResult=60:\n");
const validOps = countValidOps(60, 'direct-counting');

console.log(`Found ${validOps.length} valid operations`);
if (validOps.length > 0) {
    console.log("\nFirst 20 operations:");
    validOps.slice(0, 20).forEach(op => {
        const result = op.op === '+' ? 60 + op.term : 60 - op.term;
        console.log(`  ${op.op}${op.term} = ${result}`);
    });
    if (validOps.length > 20) {
        console.log(`  ... and ${validOps.length - 20} more`);
    }
}
