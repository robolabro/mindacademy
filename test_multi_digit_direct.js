/**
 * Test for multi-digit direct calculation
 * Each digit position should follow direct-to-9 rules independently
 */

// Mock generateDirectTo function for testing
function generateDirectTo(maxUnits, addends, formula) {
    const numbers = [];
    const operators = [];

    if (formula === 'addition') {
        let remaining = maxUnits;
        for (let i = 0; i < addends; i++) {
            if (i === addends - 1) {
                numbers.push(Math.max(1, Math.min(remaining, maxUnits)));
            } else {
                const minForRemaining = addends - i - 1;
                const maxAllowed = Math.max(1, remaining - minForRemaining);
                const num = Math.floor(Math.random() * maxAllowed) + 1;
                numbers.push(num);
                remaining -= num;
            }
            if (i > 0) operators.push('+');
        }
    } else if (formula === 'subtraction') {
        const firstNum = Math.floor(Math.random() * (maxUnits - addends + 1)) + addends;
        numbers.push(firstNum);
        let remaining = firstNum;
        for (let i = 1; i < addends; i++) {
            if (i === addends - 1) {
                const lastNum = Math.floor(Math.random() * remaining) + 1;
                numbers.push(lastNum);
            } else {
                const minForRemaining = addends - i;
                const maxAllowed = Math.max(1, remaining - minForRemaining);
                const num = Math.floor(Math.random() * maxAllowed) + 1;
                numbers.push(num);
                remaining -= num;
            }
            operators.push('-');
        }
    }

    return { numbers, operators };
}

// Function under test
function generateMultiDigitDirectCalculation(section, addends, formula) {
    const numbers = [];
    const operators = [];

    const numDigits = section;

    const digitSequences = [];
    for (let digitPos = 0; digitPos < numDigits; digitPos++) {
        const digitResult = generateDirectTo(9, addends, formula);
        digitSequences.push(digitResult.numbers);

        if (digitPos === 0) {
            operators.push(...digitResult.operators);
        }
    }

    for (let i = 0; i < addends; i++) {
        let number = 0;
        for (let digitPos = 0; digitPos < numDigits; digitPos++) {
            const digitValue = digitSequences[digitPos][i];
            const placeValue = Math.pow(10, numDigits - 1 - digitPos);
            number += digitValue * placeValue;
        }
        numbers.push(number);
    }

    return { numbers, operators };
}

// Test function
function testMultiDigitDirect() {
    console.log("Testing Multi-Digit Direct Calculation\n");
    console.log("=" .repeat(60));

    // Test 1: 2-digit addition
    console.log("\nTest 1: 2-digit Addition (section=2, addends=2)");
    for (let i = 0; i < 5; i++) {
        const result = generateMultiDigitDirectCalculation(2, 2, 'addition');
        const expr = `${result.numbers[0]} + ${result.numbers[1]}`;
        const sum = result.numbers[0] + result.numbers[1];

        // Extract digits
        const n1_tens = Math.floor(result.numbers[0] / 10);
        const n1_units = result.numbers[0] % 10;
        const n2_tens = Math.floor(result.numbers[1] / 10);
        const n2_units = result.numbers[1] % 10;
        const sum_tens = Math.floor(sum / 10);
        const sum_units = sum % 10;

        console.log(`  ${expr} = ${sum}`);
        console.log(`    Tens:  ${n1_tens} + ${n2_tens} = ${sum_tens} ${sum_tens <= 9 ? '✓' : '✗ OVERFLOW'}`);
        console.log(`    Units: ${n1_units} + ${n2_units} = ${sum_units} ${sum_units <= 9 ? '✓' : '✗ OVERFLOW'}`);
    }

    // Test 2: 2-digit subtraction
    console.log("\nTest 2: 2-digit Subtraction (section=2, addends=2)");
    for (let i = 0; i < 5; i++) {
        const result = generateMultiDigitDirectCalculation(2, 2, 'subtraction');
        const expr = `${result.numbers[0]} - ${result.numbers[1]}`;
        const diff = result.numbers[0] - result.numbers[1];

        // Extract digits
        const n1_tens = Math.floor(result.numbers[0] / 10);
        const n1_units = result.numbers[0] % 10;
        const n2_tens = Math.floor(result.numbers[1] / 10);
        const n2_units = result.numbers[1] % 10;
        const diff_tens = Math.floor(diff / 10);
        const diff_units = diff % 10;

        console.log(`  ${expr} = ${diff}`);
        console.log(`    Tens:  ${n1_tens} - ${n2_tens} = ${diff_tens} ${diff_tens >= 0 && diff_tens <= 9 ? '✓' : '✗ UNDERFLOW'}`);
        console.log(`    Units: ${n1_units} - ${n2_units} = ${diff_units} ${diff_units >= 0 && diff_units <= 9 ? '✓' : '✗ UNDERFLOW'}`);
    }

    // Test 3: 3-digit addition
    console.log("\nTest 3: 3-digit Addition (section=3, addends=3)");
    for (let i = 0; i < 3; i++) {
        const result = generateMultiDigitDirectCalculation(3, 3, 'addition');
        const expr = `${result.numbers[0]} + ${result.numbers[1]} + ${result.numbers[2]}`;
        const sum = result.numbers[0] + result.numbers[1] + result.numbers[2];

        // Extract digits
        const n1_h = Math.floor(result.numbers[0] / 100);
        const n1_t = Math.floor((result.numbers[0] % 100) / 10);
        const n1_u = result.numbers[0] % 10;
        const n2_h = Math.floor(result.numbers[1] / 100);
        const n2_t = Math.floor((result.numbers[1] % 100) / 10);
        const n2_u = result.numbers[1] % 10;
        const n3_h = Math.floor(result.numbers[2] / 100);
        const n3_t = Math.floor((result.numbers[2] % 100) / 10);
        const n3_u = result.numbers[2] % 10;
        const sum_h = Math.floor(sum / 100);
        const sum_t = Math.floor((sum % 100) / 10);
        const sum_u = sum % 10;

        console.log(`  ${expr} = ${sum}`);
        console.log(`    Hundreds: ${n1_h} + ${n2_h} + ${n3_h} = ${sum_h} ${sum_h <= 9 ? '✓' : '✗ OVERFLOW'}`);
        console.log(`    Tens:     ${n1_t} + ${n2_t} + ${n3_t} = ${sum_t} ${sum_t <= 9 ? '✓' : '✗ OVERFLOW'}`);
        console.log(`    Units:    ${n1_u} + ${n2_u} + ${n3_u} = ${sum_u} ${sum_u <= 9 ? '✓' : '✗ OVERFLOW'}`);
    }

    console.log("\n" + "=".repeat(60));
    console.log("Test complete!");
}

// Run the test
testMultiDigitDirect();
