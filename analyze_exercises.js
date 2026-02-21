// Script pentru analiza exercițiilor generate
const exercises = [
  "8 - 6 - 1 = 1",
  "3 + 6 - 8 = 1",
  "2 + 7 - 6 = 3",
  "9 - 2 - 6 = 1",
  "2 + 6 - 7 = 1",
  "6 - 5 + 8 = 9",
  "8 - 1 - 6 = 1",
  "8 - 5 + 6 = 9",
  "9 - 7 + 2 = 4",
  "9 - 1 - 7 = 1",
  "8 - 6 + 2 = 4",
  "8 - 7 + 6 = 7",
  "8 - 6 + 5 = 7",
  "8 - 7 + 8 = 9",
  "9 - 6 + 1 = 4",
  "9 - 6 - 2 = 1",
  "1 + 6 - 6 = 1",
  "6 - 5 + 8 - 1 = 8",
  "9 - 5 + 5 - 6 = 3",
  "9 - 1 - 6 + 7 = 9",
  "9 - 8 + 6 - 2 = 5",
  "7 - 5 + 7 - 5 = 4",
  "8 - 6 + 1 + 6 = 9",
  "7 - 5 + 7 - 8 = 1",
  "8 - 6 + 1 + 1 = 4",
  "8 - 2 - 5 + 7 = 8",
  "2 + 7 - 8 + 8 = 9",
  "3 + 6 - 7 + 2 = 4",
  "6 - 5 + 8 - 4 = 5",
  "9 - 6 + 5 - 7 = 1",
  "9 - 8 + 5 - 5 = 1",
  "6 - 5 + 6 - 1 = 6",
  "8 - 6 + 2 - 1 = 3",
  "8 - 1 - 6 + 1 = 2",
  "6 - 5 + 8 - 5 - 2 = 2",
  "8 - 7 + 1 + 7 - 6 = 3",
  "7 - 6 + 8 - 5 - 3 = 1",
  "9 - 5 - 3 + 2 + 6 = 9",
  "8 - 2 - 5 + 1 + 7 = 9",
  "9 - 3 - 5 + 8 - 7 = 2",
  "2 + 7 - 2 - 5 + 6 = 8",
  "9 - 7 - 1 + 1 + 6 = 8",
  "9 - 1 - 5 + 6 - 4 = 5",
  "9 - 6 + 5 - 7 + 6 = 7",
  "7 - 6 + 2 + 1 - 2 = 2",
  "7 - 6 + 6 - 5 + 5 = 7",
  "8 - 7 + 8 - 7 + 5 = 7",
  "3 + 5 - 6 + 1 + 6 = 9",
  "9 - 8 + 5 - 5 + 8 = 9",
  "4 - 3 + 7 - 7 + 7 = 8"
];

const stats = {
  '-6': 0,
  '-7': 0,
  '-8': 0,
  '-9': 0,
  'total_subtractions': 0,
  'total_terms': 0
};

exercises.forEach(ex => {
  // Parse exercițiul pentru a găsi toate operațiunile de scădere
  const parts = ex.split(' = ')[0].split(' ');

  for (let i = 0; i < parts.length; i++) {
    if (parts[i] === '-' && i + 1 < parts.length) {
      const operand = parts[i + 1];
      stats.total_subtractions++;

      if (operand === '6') stats['-6']++;
      else if (operand === '7') stats['-7']++;
      else if (operand === '8') stats['-8']++;
      else if (operand === '9') stats['-9']++;
    }
  }

  // Numără total termeni (operanzi)
  stats.total_terms += Math.floor((parts.length + 1) / 2);
});

console.log('\n=== STATISTICI TERMENI NEGATIVI MARI ===\n');
console.log('| Termen | Apariții | % din total scăderi |');
console.log('|--------|----------|---------------------|');

Object.keys(stats).forEach(key => {
  if (key.startsWith('-')) {
    const percentage = stats.total_subtractions > 0
      ? ((stats[key] / stats.total_subtractions) * 100).toFixed(1)
      : '0.0';
    console.log(`| ${key.padEnd(6)} | ${String(stats[key]).padStart(8)} | ${String(percentage).padStart(18)}% |`);
  }
});

console.log('\n=== STATISTICI GENERALE ===\n');
console.log(`Total exerciții: ${exercises.length}`);
console.log(`Total termeni: ${stats.total_terms}`);
console.log(`Total scăderi: ${stats.total_subtractions}`);
console.log(`Total -6/-7/-8/-9: ${stats['-6'] + stats['-7'] + stats['-8'] + stats['-9']}`);
console.log(`Procent scăderi cu numere mari (6-9): ${((stats['-6'] + stats['-7'] + stats['-8'] + stats['-9']) / stats.total_subtractions * 100).toFixed(1)}%`);
