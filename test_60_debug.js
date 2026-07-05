// Debug test for currentResult=60

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
        // Special case: Starting from 0
        if (currentDigit === 0 && operation === '+') {
            if (complexity === 'direct-to-4') {
                return operandDigit >= 1 && operandDigit <= 4;
            }
            if (complexity === 'direct-to-5') {
                return operandDigit >= 1 && operandDigit <= 5;
            }
            if (complexity === 'direct-to-9' || complexity === 'direct-counting') {
                console.log(`  [isSingleDigitAllowed] 0 + ${operandDigit} for ${complexity}: ${operandDigit >= 1 && operandDigit <= 9}`);
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
                console.log(`  [isAllowedOperation] Carry detected: ${currentUnitsDigit} + ${operandUnitsDigit} = ${currentUnitsDigit + operandUnitsDigit}`);
                return false;
            }
        } else {
            if (currentUnitsDigit < operandUnitsDigit) {
                console.log(`  [isAllowedOperation] Borrow detected: ${currentUnitsDigit} < ${operandUnitsDigit}`);
                return false;
            }
        }

        // Check units digit operation
        const unitsAllowed = isSingleDigitAllowed(currentUnitsDigit, operandUnitsDigit, operation, complexity);
        console.log(`  [isAllowedOperation] Units digit check: ${currentUnitsDigit} ${operation} ${operandUnitsDigit} = ${unitsAllowed}`);
        if (!unitsAllowed) {
            return false;
        }

        // Check tens digit operation (if both numbers have tens digits)
        if (currentValue >= 10 && operand >= 10) {
            const currentTensDigit = Math.floor(currentValue / 10) % 10;
            const operandTensDigit = Math.floor(operand / 10) % 10;

            const tensAllowed = isSingleDigitAllowed(currentTensDigit, operandTensDigit, operation, complexity);
            console.log(`  [isAllowedOperation] Tens digit check: ${currentTensDigit} ${operation} ${operandTensDigit} = ${tensAllowed}`);
            if (!tensAllowed) {
                return false;
            }
        } else {
            console.log(`  [isAllowedOperation] Skipping tens check (operand < 10)`);
        }

        return true;
    }

    // Single-digit case
    return isSingleDigitAllowed(currentValue, operand, operation, complexity);
}

// Test 60 + 1
console.log("Testing 60 + 1:");
const result1 = isAllowedOperation(60, '+', 1, 'direct-counting');
console.log(`Result: ${result1}\n`);

// Test 60 + 11
console.log("Testing 60 + 11:");
const result2 = isAllowedOperation(60, '+', 11, 'direct-counting');
console.log(`Result: ${result2}\n`);

// Test 60 + 22
console.log("Testing 60 + 22:");
const result3 = isAllowedOperation(60, '+', 22, 'direct-counting');
console.log(`Result: ${result3}\n`);
