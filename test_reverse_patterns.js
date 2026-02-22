/**
 * Test to verify that immediate reverse operations (+5-5, +6-6, etc.) are avoided
 */

// Copy all helper functions from test_direct9_negatives.js
function getComplexityLimit(complexity) {
    if (complexity === 'direct-to-9') return 9;
    return null;
}

function getTermLimit(complexity) {
    if (complexity === 'direct-to-9') return 9;
    return null;
}

function isDirectCalculationLevel(complexity) {
    return complexity === 'direct-to-9';
}

function generateNumber(settings, isFirstTerm = false) {
    const { digits, complexity } = settings;

    if (complexity === 'direct-to-9') {
        if (digits === 1) {
            const rand = Math.random();
            if (rand < 0.6) {
                return Math.floor(Math.random() * 4) + 6; // 6-9
            } else {
                return Math.floor(Math.random() * 5) + 1; // 1-5
            }
        }
    }
    return 1; // Fallback
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
            [4,5]
        ],
        '-': [
            [6,1],[6,5],[6,6],
            [7,1],[7,2],[7,5],[7,6],[7,7],
            [8,1],[8,2],[8,3],[8,5],[8,6],[8,7],[8,8],
            [9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9]
        ]
    };

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

function shouldAvoidTermRepetition(termsArray, candidateTerm) {
    if (termsArray.length === 0) return false;
    const MAX_CONSECUTIVE_REPETITIONS = 1;
    let consecutiveCount = 0;
    for (let i = termsArray.length - 1; i >= 0; i--) {
        if (Math.abs(termsArray[i]) === Math.abs(candidateTerm)) {
            consecutiveCount++;
        } else {
            break;
        }
    }
    return consecutiveCount >= MAX_CONSECUTIVE_REPETITIONS;
}

function isImmediateReverseOperation(operations, termsArray, currentOp, currentTerm) {
    if (operations.length === 0 || termsArray.length === 0) {
        return false;
    }

    const lastOp = operations[operations.length - 1];
    const lastTerm = termsArray[termsArray.length - 1];

    if ((lastOp === '+' && currentOp === '-' || lastOp === '-' && currentOp === '+') &&
        lastTerm === currentTerm) {
        return true;
    }

    return false;
}

function isSmallFriendsCombination(current, op, operand) {
    const currentLastDigit = current % 10;
    const operandLastDigit = operand % 10;

    if (op === '+') {
        return currentLastDigit >= 1 && currentLastDigit <= 4 &&
               operandLastDigit >= 1 && operandLastDigit <= 4 &&
               (currentLastDigit + operandLastDigit) >= 5 && (currentLastDigit + operandLastDigit) <= 9;
    } else if (op === '-') {
        return currentLastDigit === 5 && operandLastDigit >= 1 && operandLastDigit <= 4;
    }
    return false;
}

function isBigFriendsCombination(current, op, operand) {
    if (op === '+') {
        return (current % 10) + (operand % 10) >= 10;
    } else if (op === '-') {
        return (current % 10) < (operand % 10);
    }
    return false;
}

function calculateResult(termsArray, operationsArray) {
    let result = termsArray[0];
    for (let i = 0; i < operationsArray.length; i++) {
        if (operationsArray[i] === '+') {
            result += termsArray[i + 1];
        } else {
            result -= termsArray[i + 1];
        }
    }
    return result;
}

function generateExerciseTerms(settings) {
    const { terms, operation, complexity } = settings;
    const maxLimit = getComplexityLimit(complexity);

    let maxAttempts = 150;
    let attempt = 0;
    let result;
    let termsArray = [];
    let operations = [];

    const startTime = Date.now();
    const maxGenerationTime = 15000;

    do {
        if (Date.now() - startTime > maxGenerationTime) {
            console.error('Generation timeout!');
            break;
        }
        termsArray = [];
        operations = [];

        termsArray.push(generateNumber(settings, true));

        for (let i = 1; i < terms; i++) {
            let op;

            if (operation === 'mixed') {
                op = Math.random() > 0.5 ? '+' : '-';
            } else {
                op = operation === 'addition' ? '+' : '-';
            }

            operations.push(op);

            let term;
            let validTermFound = false;
            let termAttempts = 0;

            if (isDirectCalculationLevel(complexity)) {
                const currentResult = calculateResult(termsArray, operations.slice(0, -1));
                const termLimit = getTermLimit(complexity);

                let possibleOperations = [];

                for (let t = 1; t <= termLimit; t++) {
                    possibleOperations.push({ op: '+', term: t });
                }

                for (let t = 1; t <= termLimit; t++) {
                    possibleOperations.push({ op: '-', term: t });
                }

                for (let j = possibleOperations.length - 1; j > 0; j--) {
                    const k = Math.floor(Math.random() * (j + 1));
                    [possibleOperations[j], possibleOperations[k]] = [possibleOperations[k], possibleOperations[j]];
                }

                for (const opConfig of possibleOperations) {
                    const testOp = opConfig.op;
                    const testTerm = opConfig.term;
                    const testResult = testOp === '+' ? currentResult + testTerm : currentResult - testTerm;

                    if (testResult >= 1 && testResult <= maxLimit &&
                        isAllowedOperation(currentResult, testOp, testTerm, complexity) &&
                        !shouldAvoidTermRepetition(termsArray, testTerm, terms) &&
                        !isSmallFriendsCombination(currentResult, testOp, testTerm) &&
                        !isBigFriendsCombination(currentResult, testOp, testTerm) &&
                        !isImmediateReverseOperation(operations, termsArray, testOp, testTerm)) {
                        term = testTerm;
                        op = testOp;
                        operations[operations.length - 1] = testOp;
                        validTermFound = true;
                        break;
                    }

                    termAttempts++;
                }
            }

            if (!validTermFound) {
                break;
            }

            termsArray.push(term);
        }

        result = calculateResult(termsArray, operations);
        attempt++;

    } while ((result <= 0 || result > maxLimit || termsArray.length < terms) && attempt < maxAttempts);

    return { termsArray, operations, result };
}

// Run the test
console.log('='.repeat(80));
console.log('Testing that immediate reverse operations (+5-5, +6-6, etc.) are avoided');
console.log('='.repeat(80));

const settings = {
    digits: 1,
    terms: 4, // Using 4 terms to have 3 operations (more chances to detect patterns)
    operation: 'mixed',
    complexity: 'direct-to-9'
};

const numTests = 10000;
let reversePatternCount = 0;
const reversePatterns = [];

console.log(`\nGenerating ${numTests} exercises with settings:`, settings);
console.log('Checking for immediate reverse operations (e.g., +5-5, +6-6, -7+7)...\n');

for (let i = 0; i < numTests; i++) {
    const exercise = generateExerciseTerms(settings);

    // Check for immediate reverse operations
    for (let j = 1; j < exercise.operations.length; j++) {
        const prevOp = exercise.operations[j - 1];
        const currOp = exercise.operations[j];
        const prevTerm = exercise.termsArray[j];
        const currTerm = exercise.termsArray[j + 1];

        // Check if current operation reverses the previous one
        if ((prevOp === '+' && currOp === '-' || prevOp === '-' && currOp === '+') &&
            prevTerm === currTerm) {
            reversePatternCount++;
            const pattern = `${prevOp}${prevTerm} ${currOp}${currTerm}`;
            reversePatterns.push({
                exercise: exercise.termsArray.map((t, idx) =>
                    idx === 0 ? t : exercise.operations[idx - 1] + t
                ).join(' '),
                pattern: pattern
            });
        }
    }
}

console.log('='.repeat(80));
if (reversePatternCount === 0) {
    console.log('✓ SUCCESS: No immediate reverse operations found!');
    console.log(`  All ${numTests} exercises avoid simple patterns like +5-5, +6-6, etc.`);
} else {
    console.log('⚠️  PROBLEM FOUND: Immediate reverse operations detected!');
    console.log(`  Found ${reversePatternCount} reverse patterns in ${numTests} exercises`);
    console.log('\n  First 10 examples:');
    reversePatterns.slice(0, 10).forEach(({ exercise, pattern }) => {
        console.log(`    ${exercise} (contains: ${pattern})`);
    });
}
console.log('='.repeat(80));
