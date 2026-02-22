/**
 * Test script to verify the distribution of large subtractions (6-9 minus 6-9)
 * in direct-to-9 exercises with 3, 4, and 5 terms
 */

// Allowed operations for direct-to-9 (cumulative)
const directTo4 = {
    '+': [[1,1],[1,2],[1,3],[2,1],[2,2],[3,1]],
    '-': [[1,1],[2,1],[2,2],[3,1],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4]]
};

const directTo5New = {
    '+': [[1,5],[2,5],[3,5],[4,5],[5,1],[5,2],[5,3],[5,4]],
    '-': [[5,5],[6,1],[6,5],[7,1],[7,2],[7,5],[8,1],[8,2],[8,3],[8,5],[9,1],[9,2],[9,3],[9,4],[9,5]]
};

const directTo9New = {
    '+': [[1,6],[1,7],[1,8],[2,6],[2,7],[3,6],[6,1],[6,2],[6,3],[7,1],[7,2],[8,1]],
    '-': [[6,6],[7,6],[7,7],[8,6],[8,7],[8,8],[9,6],[9,7],[9,8],[9,9]]
};

function isAllowedOperation(currentValue, operation, operand) {
    const ops4 = directTo4[operation] || [];
    const ops5 = directTo5New[operation] || [];
    const ops9 = directTo9New[operation] || [];

    const inDirect4 = ops4.some(([v, o]) => v === currentValue && o === operand);
    const inDirect5 = ops5.some(([v, o]) => v === currentValue && o === operand);
    const inDirect9 = ops9.some(([v, o]) => v === currentValue && o === operand);

    return inDirect4 || inDirect5 || inDirect9;
}

function generateExercise(numTerms) {
    const maxAttempts = numTerms === 3 ? 50 : numTerms === 4 ? 75 : 200;
    let attempt = 0;

    while (attempt < maxAttempts) {
        attempt++;

        // Generate first term: 60% large (6-9), 40% small (1-5)
        let firstTerm;
        if (Math.random() < 0.6) {
            firstTerm = Math.floor(Math.random() * 4) + 6; // 6-9
        } else {
            firstTerm = Math.floor(Math.random() * 5) + 1; // 1-5
        }

        let terms = [firstTerm];
        let operations = [];
        let valid = true;

        // Generate remaining terms
        for (let i = 1; i < numTerms; i++) {
            const currentResult = terms.reduce((acc, term, idx) => {
                if (idx === 0) return term;
                return operations[idx - 1] === '+' ? acc + term : acc - term;
            }, 0);

            // Random operation
            const op = Math.random() > 0.5 ? '+' : '-';
            operations.push(op);

            // Try to find a valid term
            let termFound = false;
            let termAttempts = 0;

            while (!termFound && termAttempts < 20) {
                termAttempts++;

                // Generate random term with weighted distribution for subtractions in direct-to-9
                let term;
                if (op === '-' && currentResult >= 6 && currentResult <= 9) {
                    // For subtractions from 6-9: 70% large (6-9), 30% small (1-5)
                    if (Math.random() < 0.7) {
                        term = Math.floor(Math.random() * 4) + 6; // 6-9
                    } else {
                        term = Math.floor(Math.random() * 5) + 1; // 1-5
                    }
                } else {
                    // Uniform distribution for other cases
                    term = Math.floor(Math.random() * 9) + 1;
                }

                const testResult = op === '+' ? currentResult + term : currentResult - term;

                // Check if valid
                if (testResult >= 0 && testResult <= 9 &&
                    isAllowedOperation(currentResult, op, term)) {
                    terms.push(term);
                    termFound = true;
                }
            }

            if (!termFound) {
                valid = false;
                break;
            }
        }

        if (!valid) continue;

        // Calculate final result
        const result = terms.reduce((acc, term, idx) => {
            if (idx === 0) return term;
            return operations[idx - 1] === '+' ? acc + term : acc - term;
        }, 0);

        // Check if result is valid (1-9)
        if (result >= 1 && result <= 9) {
            return { terms, operations, result };
        }
    }

    return null;
}

function analyzeSubtractionDistribution(numExercises, numTerms) {
    let totalSubtractions = 0;
    let largeSubtractions = 0; // Both operands 6-9
    let mediumSubtractions = 0; // Current 6-9, operand 1-5
    let smallSubtractions = 0; // Current 1-5

    let exercisesWithLargeSubtraction = 0;

    for (let i = 0; i < numExercises; i++) {
        const exercise = generateExercise(numTerms);
        if (!exercise) {
            console.log(`Failed to generate exercise ${i + 1}`);
            continue;
        }

        const { terms, operations } = exercise;
        let hasLargeSubtraction = false;

        // Analyze each operation
        for (let j = 0; j < operations.length; j++) {
            if (operations[j] === '-') {
                totalSubtractions++;

                // Calculate current value before this operation
                const currentValue = terms.slice(0, j + 1).reduce((acc, term, idx) => {
                    if (idx === 0) return term;
                    return operations[idx - 1] === '+' ? acc + term : acc - term;
                }, 0);

                const operand = terms[j + 1];

                if (currentValue >= 6 && currentValue <= 9 && operand >= 6 && operand <= 9) {
                    largeSubtractions++;
                    hasLargeSubtraction = true;
                } else if (currentValue >= 6 && currentValue <= 9 && operand >= 1 && operand <= 5) {
                    mediumSubtractions++;
                } else {
                    smallSubtractions++;
                }
            }
        }

        if (hasLargeSubtraction) {
            exercisesWithLargeSubtraction++;
        }
    }

    return {
        totalSubtractions,
        largeSubtractions,
        mediumSubtractions,
        smallSubtractions,
        exercisesWithLargeSubtraction,
        totalExercises: numExercises
    };
}

// Run analysis
console.log('=== ANALYZING SUBTRACTION DISTRIBUTION IN DIRECT-TO-9 EXERCISES ===\n');

for (const numTerms of [3, 4, 5]) {
    console.log(`--- ${numTerms} TERMS ---`);
    const stats = analyzeSubtractionDistribution(100, numTerms);

    console.log(`Total exercises: ${stats.totalExercises}`);
    console.log(`Total subtractions: ${stats.totalSubtractions}`);
    console.log(`Large subtractions (6-9 minus 6-9): ${stats.largeSubtractions} (${(stats.largeSubtractions / stats.totalSubtractions * 100).toFixed(1)}%)`);
    console.log(`Medium subtractions (6-9 minus 1-5): ${stats.mediumSubtractions} (${(stats.mediumSubtractions / stats.totalSubtractions * 100).toFixed(1)}%)`);
    console.log(`Small subtractions (1-5 minus X): ${stats.smallSubtractions} (${(stats.smallSubtractions / stats.totalSubtractions * 100).toFixed(1)}%)`);
    console.log(`Exercises with at least 1 large subtraction: ${stats.exercisesWithLargeSubtraction} (${(stats.exercisesWithLargeSubtraction / stats.totalExercises * 100).toFixed(1)}%)`);
    console.log('');
}

console.log('\n=== EXPECTED: ===');
console.log('For optimal learning, we should see:');
console.log('- At least 30-40% of subtractions should be large (6-9 minus 6-9)');
console.log('- At least 50% of exercises should contain at least 1 large subtraction');
