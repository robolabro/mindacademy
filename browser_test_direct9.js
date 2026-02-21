/**
 * Script de testare pentru browser - verifică distribuția operațiilor în Calcul Direct cu 9
 *
 * INSTRUCȚIUNI:
 * 1. Deschideți pagina Anzan Simulator în browser
 * 2. Setați complexitatea la "Calcul Direct cu 9"
 * 3. Apăsați F12 pentru a deschide Developer Console
 * 4. Copiați și lipiți ÎNTREG acest script în consolă
 * 5. Apăsați Enter și așteptați rezultatele
 */

(function() {
    console.log('='.repeat(80));
    console.log('TESTARE: Calcul Direct cu 9 - Distribuția operațiilor');
    console.log('='.repeat(80));

    const settings = {
        digits: 1,
        terms: 3,
        operation: 'mixed',
        complexity: 'direct-to-9',
        fractions: 0
    };

    const numTests = 2000;
    const operationCounts = {};

    // Initialize counters
    for (let i = 1; i <= 9; i++) {
        operationCounts['+' + i] = 0;
        operationCounts['-' + i] = 0;
    }

    console.log(`\nGenerând ${numTests} exerciții cu setările:`, settings);
    console.log('Vă rog așteptați...\n');

    // Generate exercises
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

    const totalOps = numTests * (settings.terms - 1);

    // Display results
    console.log('Distribuția operațiilor în ' + numTests + ' exerciții:');
    console.log('-'.repeat(80));

    console.log('\n%cADUNĂRI:', 'color: blue; font-weight: bold');
    for (let i = 1; i <= 9; i++) {
        const key = '+' + i;
        const count = operationCounts[key];
        const percentage = ((count / totalOps) * 100).toFixed(1);
        const bar = '█'.repeat(Math.floor(count / 20));
        const color = count > 0 ? 'color: green' : 'color: red';
        console.log(`%c  ${key.padEnd(4)} : ${count.toString().padStart(4)} (${percentage.padStart(5)}%)  ${bar}`, color);
    }

    console.log('\n%cSCĂDERI:', 'color: blue; font-weight: bold');
    for (let i = 1; i <= 9; i++) {
        const key = '-' + i;
        const count = operationCounts[key];
        const percentage = ((count / totalOps) * 100).toFixed(1);
        const bar = '█'.repeat(Math.floor(count / 20));
        const color = count > 0 ? 'color: green' : 'color: red';
        console.log(`%c  ${key.padEnd(4)} : ${count.toString().padStart(4)} (${percentage.padStart(5)}%)  ${bar}`, color);
    }

    // Check for large negative numbers
    console.log('\n' + '='.repeat(80));
    const largeNegatives = ['-6', '-7', '-8', '-9'];
    const largNegativeCounts = largeNegatives.map(op => ({ op, count: operationCounts[op] }));
    const missingLargeNegatives = largNegativeCounts.filter(item => item.count === 0);

    if (missingLargeNegatives.length > 0) {
        console.log('%c⚠️  PROBLEMĂ: Următoarele operații cu numere mari negative LIPSESC:', 'color: red; font-weight: bold');
        console.log('%c   ' + missingLargeNegatives.map(item => item.op).join(', '), 'color: red');
    } else {
        const totalLargeNegatives = largNegativeCounts.reduce((sum, item) => sum + item.count, 0);
        const percentage = ((totalLargeNegatives / totalOps) * 100).toFixed(1);
        console.log('%c✓ Toate numerele mari negative (-6, -7, -8, -9) sunt prezente!', 'color: green; font-weight: bold');
        console.log(`%c  Total operații cu -6/-7/-8/-9: ${totalLargeNegatives} (${percentage}% din toate operațiile)`, 'color: green');
        console.log('  Detalii:');
        largNegativeCounts.forEach(item => {
            const pct = ((item.count / totalOps) * 100).toFixed(1);
            console.log(`    ${item.op}: ${item.count} (${pct}%)`);
        });
    }

    // Additional statistics
    console.log('\n' + '='.repeat(80));
    console.log('%cSTATISTICI ADIȚIONALE:', 'color: blue; font-weight: bold');

    const totalAdditions = Object.keys(operationCounts)
        .filter(k => k.startsWith('+'))
        .reduce((sum, k) => sum + operationCounts[k], 0);
    const totalSubtractions = Object.keys(operationCounts)
        .filter(k => k.startsWith('-'))
        .reduce((sum, k) => sum + operationCounts[k], 0);

    console.log(`  Total adunări: ${totalAdditions} (${((totalAdditions / totalOps) * 100).toFixed(1)}%)`);
    console.log(`  Total scăderi: ${totalSubtractions} (${((totalSubtractions / totalOps) * 100).toFixed(1)}%)`);

    const largeAdditions = ['+6', '+7', '+8'].reduce((sum, k) => sum + operationCounts[k], 0);
    const largeSubtractions = ['-6', '-7', '-8'].reduce((sum, k) => sum + operationCounts[k], 0);

    console.log(`  Adunări cu numere mari (+6/+7/+8): ${largeAdditions} (${((largeAdditions / totalOps) * 100).toFixed(1)}%)`);
    console.log(`  Scăderi cu numere mari (-6/-7/-8): ${largeSubtractions} (${((largeSubtractions / totalOps) * 100).toFixed(1)}%)`);

    console.log('\n' + '='.repeat(80));
    console.log('%cTest finalizat!', 'color: green; font-weight: bold');
    console.log('='.repeat(80));
})();
