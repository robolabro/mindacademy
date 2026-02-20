// Script pentru simularea exercițiilor de Calcul Direct

// Tabele de operații permise pentru fiecare nivel
const directTo4 = {
    '+': [[1,1],[1,2],[1,3],[2,1],[2,2],[3,1]],
    '-': [[1,1],[2,1],[2,2],[3,1],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4]]
};

const directTo5New = {
    '+': [[1,5],[2,5],[3,5],[4,5]],
    '-': [[6,1],[6,5],[7,1],[7,2],[7,5],[8,1],[8,2],[8,3],[8,5],[9,1],[9,2],[9,3],[9,4],[9,5]]
};

const directTo9New = {
    '+': [[1,6],[1,7],[1,8],[2,6],[2,7],[3,6]],
    '-': [[6,6],[7,6],[7,7],[8,6],[8,7],[8,8],[9,6],[9,7],[9,8],[9,9]]
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

    if (complexity === 'direct-to-9') {
        const ops9 = directTo9New[operation] || [];
        const inDirect9 = ops9.some(([v, o]) => v === currentValue && o === operand);
        return inDirect4 || inDirect5 || inDirect9;
    }

    return false;
}

function getComplexityLimit(complexity) {
    if (complexity === 'direct-to-4') return 4;
    if (complexity === 'direct-to-5') return 9;
    if (complexity === 'direct-to-9') return 9;
    return 9;
}

function generateExercise(numTerms, complexity) {
    const maxLimit = getComplexityLimit(complexity);
    const maxAttempts = 500;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        let terms = [];
        let ops = [];
        let currentValue;

        // Primul termen
        if (complexity === 'direct-to-4') {
            currentValue = Math.floor(Math.random() * 4) + 1;
        } else if (complexity === 'direct-to-5') {
            currentValue = Math.floor(Math.random() * 5) + 1;
        } else {
            currentValue = Math.floor(Math.random() * 9) + 1;
        }

        terms.push(currentValue);
        let valid = true;
        let hasFive = currentValue === 5;
        let largeCount = (currentValue >= 6 && currentValue <= 9) ? 1 : 0;

        // Generează restul termenilor
        for (let i = 1; i < numTerms; i++) {
            let foundValid = false;

            for (let termAttempt = 0; termAttempt < 100; termAttempt++) {
                const operation = Math.random() < 0.5 ? '+' : '-';
                let operand;

                if (complexity === 'direct-to-4') {
                    operand = Math.floor(Math.random() * 4) + 1;
                } else if (complexity === 'direct-to-5') {
                    operand = Math.floor(Math.random() * 9) + 1;
                } else {
                    operand = Math.floor(Math.random() * 9) + 1;
                }

                const newValue = operation === '+' ? currentValue + operand : currentValue - operand;

                // Verifică dacă operația este permisă
                if (newValue >= 1 && newValue <= maxLimit &&
                    isAllowedOperation(currentValue, operation, operand, complexity)) {

                    // Pentru direct-to-9, verifică proporția de numere mari
                    if (complexity === 'direct-to-9' && i > 0) {
                        if (operand >= 6 && operand <= 9) {
                            largeCount++;
                        }
                    }

                    if (operand === 5) hasFive = true;

                    terms.push(operand);
                    ops.push(operation);
                    currentValue = newValue;
                    foundValid = true;
                    break;
                }
            }

            if (!foundValid) {
                valid = false;
                break;
            }
        }

        // Validări finale
        if (valid && currentValue >= 1) {
            // Pentru direct-to-5, trebuie să existe cel puțin un 5
            if (complexity === 'direct-to-5' && !hasFive) {
                continue;
            }

            // Pentru direct-to-9, verifică proporția de numere mari
            if (complexity === 'direct-to-9' && numTerms >= 3) {
                const requiredPercentage = numTerms === 3 ? 0.7 :
                                          numTerms === 4 ? 0.6 :
                                          numTerms === 5 ? 0.5 : 0.4;
                const nonFirstTerms = numTerms - 1;
                const requiredCount = Math.ceil(nonFirstTerms * requiredPercentage);

                if (largeCount < requiredCount) {
                    continue;
                }
            }

            return { terms, ops, result: currentValue, complexity };
        }
    }

    return null;
}

function formatExercise(ex) {
    if (!ex) return "Eroare la generare";

    let str = ex.terms[0].toString();
    for (let i = 0; i < ex.ops.length; i++) {
        str += ` ${ex.ops[i]} ${ex.terms[i + 1]}`;
    }
    return `${str} = ${ex.result}`;
}

// Generează 50 de exerciții doar pentru Calcul Direct cu 9
console.log("Generare 50 exerciții de Calcul Direct cu 9 (3, 4, 5 termeni)\n");
console.log("=" .repeat(80));

const exercises = [];

// Doar Direct to 9 cu 3, 4, 5 termeni (50 exerciții)
const configs = [];

// Distribuție echilibrată: ~17 cu 3 termeni, ~17 cu 4 termeni, ~16 cu 5 termeni
for (let i = 0; i < 17; i++) {
    configs.push({ terms: 3, complexity: 'direct-to-9' });
}
for (let i = 0; i < 17; i++) {
    configs.push({ terms: 4, complexity: 'direct-to-9' });
}
for (let i = 0; i < 16; i++) {
    configs.push({ terms: 5, complexity: 'direct-to-9' });
}

for (let i = 0; i < configs.length; i++) {
    const config = configs[i];
    const ex = generateExercise(config.terms, config.complexity);

    if (ex) {
        exercises.push({
            nr: i + 1,
            termeni: config.terms,
            complexitate: config.complexity,
            exercitiu: formatExercise(ex),
            rezultat: ex.result
        });
    }
}

// Afișează tabelul
console.log("\n| Nr | Termeni | Complexitate | Exercițiu | Rezultat |");
console.log("|----|---------|--------------|-----------|----------|");

exercises.forEach(ex => {
    const termsStr = ex.termeni.toString().padEnd(7);
    const complexStr = ex.complexitate.padEnd(12);
    const exerciseStr = ex.exercitiu.padEnd(30);
    console.log(`| ${String(ex.nr).padStart(2)} | ${termsStr} | ${complexStr} | ${exerciseStr} | ${ex.rezultat} |`);
});

console.log("\n" + "=".repeat(80));
console.log(`\nTotal exerciții generate: ${exercises.length}`);
