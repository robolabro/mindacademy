/**
 * Test to verify that direct-to-9 exercises include large negative numbers (-6, -7, -8, -9)
 *
 * This script extracts the exercise generation logic and tests it
 */

// Extract the core logic from anzan_simulator.html
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

        // Generate first term (always positive)
        termsArray.push(generateNumber(settings, true));

        // Generate remaining terms
        for (let i = 1; i < terms; i++) {
            let op;

            // Normal operation selection
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

                let termsToTry = [];

                // For direct-to-9/direct-counting subtractions from 6-9: favor large numbers
                if (op === '-' && complexity === 'direct-to-9' &&
                    currentResult >= 6 && currentResult <= 9) {
                    // Weighted selection: 70% large numbers (6-9), 30% small (1-5)
                    if (Math.random() < 0.7) {
                        // Try large numbers first (descending)
                        for (let t = Math.min(termLimit, 9); t >= 6; t--) termsToTry.push(t);
                        // Then small numbers
                        for (let t = 5; t >= 1; t--) termsToTry.push(t);
                    } else {
                        // Try small numbers first
                        for (let t = 1; t <= 5; t++) termsToTry.push(t);
                        // Then large numbers (descending)
                        for (let t = Math.min(termLimit, 9); t >= 6; t--) termsToTry.push(t);
                    }
                } else {
                    // For all other cases: uniform distribution
                    for (let t = 1; t <= termLimit; t++) {
                        termsToTry.push(t);
                    }
                    // Shuffle for randomness
                    for (let j = termsToTry.length - 1; j > 0; j--) {
                        const k = Math.floor(Math.random() * (j + 1));
                        [termsToTry[j], termsToTry[k]] = [termsToTry[k], termsToTry[j]];
                    }
                }

                // Try each term in the list
                for (const t of termsToTry) {
                    const testResult = op === '+' ? currentResult + t : currentResult - t;

                    // Check if this term creates a valid operation
                    if (testResult >= 1 && testResult <= maxLimit &&
                        isAllowedOperation(currentResult, op, t, complexity) &&
                        !shouldAvoidTermRepetition(termsArray, t, terms) &&
                        !isSmallFriendsCombination(currentResult, op, t) &&
                        !isBigFriendsCombination(currentResult, op, t)) {
                        term = t;
                        validTermFound = true;
                        break;
                    }

                    termAttempts++;
                    if (termAttempts >= 20) break;
                }

                // If no valid term found with current operation, try switching operation
                if (!validTermFound) {
                    const altOp = op === '+' ? '-' : '+';

                    // Try all terms with the alternative operation
                    for (let t = 1; t <= termLimit; t++) {
                        const testResult = altOp === '+' ? currentResult + t : currentResult - t;

                        if (testResult >= 1 && testResult <= maxLimit &&
                            isAllowedOperation(currentResult, altOp, t, complexity) &&
                            !shouldAvoidTermRepetition(termsArray, t, terms) &&
                            !isSmallFriendsCombination(currentResult, altOp, t) &&
                            !isBigFriendsCombination(currentResult, altOp, t)) {
                            term = t;
                            op = altOp;
                            operations[operations.length - 1] = altOp;
                            validTermFound = true;
                            break;
                        }

                        termAttempts++;
                        if (termAttempts >= 40) break;
                    }
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
console.log('Testing direct-to-9 exercise generation for large negative numbers (-6, -7, -8, -9)');
console.log('='.repeat(80));

const settings = {
    digits: 1,
    terms: 3,
    operation: 'mixed',
    complexity: 'direct-to-9'
};

const operationCounts = {
    '+1': 0, '+2': 0, '+3': 0, '+4': 0, '+5': 0, '+6': 0, '+7': 0, '+8': 0, '+9': 0,
    '-1': 0, '-2': 0, '-3': 0, '-4': 0, '-5': 0, '-6': 0, '-7': 0, '-8': 0, '-9': 0
};

const numTests = 5000;

console.log(`\nGenerating ${numTests} exercises with settings:`, settings);
console.log('');

for (let i = 0; i < numTests; i++) {
    const exercise = generateExerciseTerms(settings);

    // Count each operation
    for (let j = 0; j < exercise.operations.length; j++) {
        const op = exercise.operations[j];
        const term = exercise.termsArray[j + 1];
        const key = op + term;
        operationCounts[key]++;
    }
}

// Display results
console.log('Operation distribution across ' + numTests + ' exercises (each with ' + (settings.terms - 1) + ' operations):');
console.log('-'.repeat(80));

console.log('\nADDITIONS:');
const additions = ['+1', '+2', '+3', '+4', '+5', '+6', '+7', '+8', '+9'];
for (const op of additions) {
    const count = operationCounts[op];
    const percentage = ((count / (numTests * (settings.terms - 1))) * 100).toFixed(1);
    const bar = '█'.repeat(Math.floor(count / 20));
    console.log(`  ${op.padEnd(4)} : ${count.toString().padStart(4)} (${percentage.padStart(5)}%)  ${bar}`);
}

console.log('\nSUBTRACTIONS:');
const subtractions = ['-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9'];
for (const op of subtractions) {
    const count = operationCounts[op];
    const percentage = ((count / (numTests * (settings.terms - 1))) * 100).toFixed(1);
    const bar = '█'.repeat(Math.floor(count / 20));
    console.log(`  ${op.padEnd(4)} : ${count.toString().padStart(4)} (${percentage.padStart(5)}%)  ${bar}`);
}

// Check for missing large negative numbers
console.log('\n' + '='.repeat(80));
const largeNegatives = ['-6', '-7', '-8', '-9'];
const missingLargeNegatives = largeNegatives.filter(op => operationCounts[op] === 0);

if (missingLargeNegatives.length > 0) {
    console.log('⚠️  PROBLEM FOUND: The following large negative numbers are MISSING:');
    console.log('   ', missingLargeNegatives.join(', '));
} else {
    const totalLargeNegatives = largeNegatives.reduce((sum, op) => sum + operationCounts[op], 0);
    const percentage = ((totalLargeNegatives / (numTests * (settings.terms - 1))) * 100).toFixed(1);
    console.log('✓ All large negative numbers (-6, -7, -8, -9) are present');
    console.log(`  Total large negatives: ${totalLargeNegatives} (${percentage}% of all operations)`);
}
console.log('='.repeat(80));
