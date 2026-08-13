// Test to understand which states actually allow formula +1

function requiresSmallFriendsFormula(currentValue, operation, operand) {
    const currentLastDigit = currentValue % 10;
    const operandLastDigit = operand % 10;
    const result = operation === '+' ? currentLastDigit + operandLastDigit : currentLastDigit - operandLastDigit;

    if (operation === '+') {
        if (currentLastDigit >= 1 && currentLastDigit <= 4 && operandLastDigit >= 1 && operandLastDigit <= 4 && result >= 5 && result <= 9) {
            return true;
        }
    } else if (operation === '-') {
        if (currentLastDigit === 5 && operandLastDigit >= 1 && operandLastDigit <= 4) {
            return true;
        }
        if (currentLastDigit >= 6 && currentLastDigit <= 9 && result >= 1 && result <= 4) {
            const lowerBeadsUsed = currentLastDigit - 5;
            if (operandLastDigit === 5) {
                return false;
            }
            return operandLastDigit >= 1 && operandLastDigit <= 4 && operandLastDigit > lowerBeadsUsed;
        }
    }

    return false;
}

console.log('=== Testing Which States Allow Formula +1 ===\n');

console.log('Testing ADDITION with operand 1:');
for (let current = 1; current <= 9; current++) {
    const result = current + 1;
    if (result <= 9) {
        const usesFormula = requiresSmallFriendsFormula(current, '+', 1);
        console.log(`  ${current} + 1 = ${result}: ${usesFormula ? '✓ FORMULA' : '✗ Direct'}`);
    }
}

console.log('\nTesting ADDITION with operand 4:');
for (let current = 1; current <= 9; current++) {
    const result = current + 4;
    if (result <= 9) {
        const usesFormula = requiresSmallFriendsFormula(current, '+', 4);
        console.log(`  ${current} + 4 = ${result}: ${usesFormula ? '✓ FORMULA' : '✗ Direct'}`);
    }
}

console.log('\n=== Summary for Formula +1 ===');
console.log('Operations that ACTUALLY use formula +1:');
const formulaOps = [];
for (let current = 1; current <= 9; current++) {
    // Try +1
    if (current + 1 <= 9 && requiresSmallFriendsFormula(current, '+', 1)) {
        formulaOps.push(`${current}+1=${current+1}`);
    }
    // Try +4 (reverse of +1)
    if (current + 4 <= 9 && requiresSmallFriendsFormula(current, '+', 4)) {
        formulaOps.push(`${current}+4=${current+4}`);
    }
}

console.log(`Total operations: ${formulaOps.length}`);
formulaOps.forEach(op => console.log(`  ✓ ${op}`));

console.log('\n=== Key Insight ===');
console.log('For formula +1, only these states work:');
console.log('  currentResult = 4 → can do 4+1=5 (FORMULA)');
console.log('  currentResult = 1 → can do 1+4=5 (FORMULA)');
console.log('');
console.log('All other states in range 1-4 do NOT use the formula!');
console.log('  currentResult = 1 → 1+1=2 is DIRECT');
console.log('  currentResult = 2 → 2+1=3 is DIRECT');
console.log('  currentResult = 3 → 3+1=4 is DIRECT');
console.log('');
console.log('This explains why exercises rarely have formula +1!');
