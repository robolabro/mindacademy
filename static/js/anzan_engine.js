// Anzan exercise generation engine - pure logic extracted from anzan_simulator.html
// Used by the flashcard exercises mode. No DOM access on load.

const BIG_FRIENDS_ORDER = [
    {type:'plus',  N:1}, {type:'plus',  N:2}, {type:'plus',  N:3},
    {type:'plus',  N:4}, {type:'plus',  N:5},
    {type:'minus', N:1}, {type:'minus', N:2}, {type:'minus', N:3},
    {type:'minus', N:4}, {type:'minus', N:5},
    {type:'plus',  N:9}, {type:'minus', N:9},
    {type:'plus',  N:8}, {type:'minus', N:8},
    {type:'plus',  N:7}, {type:'minus', N:7},
    {type:'plus',  N:6}, {type:'minus', N:6},
];

const FAMILY_ORDER = [
    {type:'plus',  N:6}, {type:'minus', N:6},
    {type:'plus',  N:7}, {type:'minus', N:7},
    {type:'plus',  N:8}, {type:'minus', N:8},
    {type:'plus',  N:9}, {type:'minus', N:9},
];

function resolveDigitsAllowed(settings) {
    if (settings.digitsAllowed && settings.digitsAllowed.length > 0) {
        return [...settings.digitsAllowed].sort();
    }
    const d = settings.digits || 1;
    return Array.from({ length: d }, (_, k) => k + 1);
}

function digitCountOf(n) {
    return String(Math.abs(n)).length;
}

function minResultForDigits(digitsAllowed) {
    const minD = Math.min(...digitsAllowed);
    return minD > 1 ? Math.pow(10, minD - 1) : 0;
}

function buildNumberWithUnits(u, count) {
    if (count <= 1) return u;
    let lead = 0;
    for (let d = 0; d < count - 1; d++) {
        lead = lead * 10 + (1 + Math.floor(Math.random() * 9));
    }
    return lead * 10 + u;
}

function forEachAllowedTerm(digitsAllowed, cap, fn) {
    for (const c of digitsAllowed) {
        const start = c === 1 ? 1 : Math.pow(10, c - 1);
        const end = Math.min(cap, Math.pow(10, c) - 1);
        for (let t = start; t <= end; t++) {
            fn(t);
        }
    }
}

function smallFormulaApplicableUnits(formulaType, N) {
    const op = formulaType === 'plus' ? '+' : '-';
    const result = [];
    for (let u = 0; u <= 9; u++) {
        if (requiresSmallFriendsFormula(u, op, N)) {
            result.push(u);
        }
    }
    return result;
}

function bigFormulaApplicableUnits(formulaType, N, isFamily) {
    const result = [];
    const op = formulaType === 'plus' ? '+' : '-';
    for (let u = 0; u <= 9; u++) {
        const testValue = 10 + u; // value >= 10 so minus (borrow) is testable too
        const big = requiresBigFriendsFormula(testValue, op, N);
        const fam = requiresFamilyFormula(testValue, op, N);
        if (big && (isFamily ? fam : !fam)) {
            result.push(u);
        }
    }
    return result;
}

function isBigFriendsLevel(complexity) {
    return complexity.startsWith('big-') || complexity === 'big-friends-all';
}

function isFamilyLevel(complexity) {
    return complexity.startsWith('family-') || complexity === 'family-all';
}

function isAdvancedLevel(complexity) {
    return isSmallFriendsLevel(complexity) || isBigFriendsLevel(complexity) || isFamilyLevel(complexity);
}

function isSmallFriendsLevel(complexity) {
    return complexity.startsWith('small-') || complexity === 'small-friends-all' || complexity === 'small-friends-all-multi';
}

function isDirectCalculationLevel(complexity) {
    return ['direct-to-4', 'direct-to-5', 'direct-to-9', 'direct-counting'].includes(complexity);
}

function requiresSmallFriendsFormula(currentValue, operation, operand) {
    // For multi-digit numbers, work with last digits only
    const currentLastDigit = currentValue % 10;
    const operandLastDigit = operand % 10;
    const result = operation === '+' ? currentLastDigit + operandLastDigit : currentLastDigit - operandLastDigit;

    if (operation === '+') {
        // Adding from 1-4 to get 5-9 requires Small Friends formula
        // Formula is needed when transitioning from lower beads (1-4) to heaven bead region (5-9)
        // Example: 4+1=5 requires +1 = +5-4 (move heaven up, remove all 4 lower beads)
        // CRITICAL: Must check that OPERAND is also 1-4, not just the current value
        // Otherwise operations like 1+5=6, 1+6=7 are incorrectly considered as requiring formula
        if (currentLastDigit >= 1 && currentLastDigit <= 4 && operandLastDigit >= 1 && operandLastDigit <= 4 && result >= 5 && result <= 9) {
            return true;
        }
    } else if (operation === '-') {
        // Subtracting from 5 to get 1-4 requires Small Friends
        if (currentLastDigit === 5 && operandLastDigit >= 1 && operandLastDigit <= 4) {
            return true;
        }
        // Subtracting from 6-9 where we need to remove the heaven bead
        if (currentLastDigit >= 6 && currentLastDigit <= 9 && result >= 1 && result <= 4) {
            const lowerBeadsUsed = currentLastDigit - 5;
            // CRITICAL: Subtracting 5 from 6-9 is DIRECT (just remove heaven bead)
            // Only operations subtracting 1-4 where we need more than available lower beads require formula
            // Example: 6-2=4 requires formula (6=5+1, can't subtract 2 from 1 lower bead)
            // Example: 6-5=1 is DIRECT (just remove heaven bead, 1 lower bead remains)
            if (operandLastDigit === 5) {
                return false; // Subtracting 5 is always direct
            }
            // If we need to subtract more than the lower beads we have (and operand is 1-4)
            return operandLastDigit >= 1 && operandLastDigit <= 4 && operandLastDigit > lowerBeadsUsed;
        }
    }

    return false;
}

function requiresBigFriendsFormula(currentValue, operation, operand) {
    const units = currentValue % 10;
    if (operation === '+') {
        return (units + operand >= 10) && (operand >= 1 && operand <= 9);
    } else {
        return (units < operand) && (currentValue >= 10) && (operand >= 1 && operand <= 9);
    }
}

function requiresFamilyFormula(currentValue, operation, operand) {
    if (!requiresBigFriendsFormula(currentValue, operation, operand)) return false;
    const units = currentValue % 10;
    const complement = 10 - operand;
    if (operation === '+') {
        return requiresSmallFriendsFormula(units, '-', complement);
    } else {
        return requiresSmallFriendsFormula(units, '+', complement);
    }
}

function getAllowedBigFriendsFormulas(complexity) {
    if (complexity === 'big-friends-all') {
        return { bigFriends: [...BIG_FRIENDS_ORDER], family: [] };
    }
    if (complexity === 'family-all') {
        return { bigFriends: [...BIG_FRIENDS_ORDER], family: [...FAMILY_ORDER] };
    }

    // Parse big-plus-N or big-minus-N
    const bigMatch = complexity.match(/^big-(plus|minus)-(\d+)$/);
    if (bigMatch) {
        const type = bigMatch[1];
        const N = parseInt(bigMatch[2]);
        const currentIdx = BIG_FRIENDS_ORDER.findIndex(f => f.type === type && f.N === N);
        return {
            bigFriends: currentIdx >= 0 ? BIG_FRIENDS_ORDER.slice(0, currentIdx + 1) : [],
            family: []
        };
    }

    // Parse family-plus-N or family-minus-N
    const famMatch = complexity.match(/^family-(plus|minus)-(\d+)$/);
    if (famMatch) {
        const type = famMatch[1];
        const N = parseInt(famMatch[2]);
        const currentIdx = FAMILY_ORDER.findIndex(f => f.type === type && f.N === N);
        return {
            bigFriends: [...BIG_FRIENDS_ORDER],
            family: currentIdx >= 0 ? FAMILY_ORDER.slice(0, currentIdx + 1) : []
        };
    }

    return { bigFriends: [], family: [] };
}

function getComplexityLimit(complexity, digits = 1) {
    switch(complexity) {
        case 'direct-to-4':
            // Multi-digit: every column follows direct-to-4 rules, so each digit <= 4
            if (digits > 1) return parseInt('4'.repeat(digits));
            return 4;
        case 'direct-to-5':
            // Allow results up to 9 per column (heaven bead combinations)
            if (digits > 1) return parseInt('9'.repeat(digits));
            return 9;
        case 'direct-to-9':
            if (digits > 1) return parseInt('9'.repeat(digits));
            return 9;
        case 'direct-counting':
            // For multi-digit direct counting, the limit is based on number of digits
            if (digits > 1) {
                return parseInt('9'.repeat(digits)); // For 2 digits: 99, for 3 digits: 999, etc.
            }
            return 9; // For single-digit direct counting
        case 'small-plus-1':
        case 'small-plus-2':
        case 'small-plus-3':
        case 'small-plus-4':
        case 'small-minus-1':
        case 'small-minus-2':
        case 'small-minus-3':
        case 'small-minus-4':
        case 'small-friends-all':
            // Multi-digit: every column follows the level's rules, results up to 99/999
            if (digits > 1) return parseInt('9'.repeat(digits));
            return 9; // Small Friends formulas can work with numbers 1-9
        case 'small-friends-all-multi':
            // Multi-digit Small Friends: support 2+ digit numbers like direct-counting
            if (digits > 1) {
                return parseInt('9'.repeat(digits)); // For 2 digits: 99, for 3 digits: 999, etc.
            }
            return 9;
        default:
            // Big Friends and Family levels: the carry/borrow formulas cross the
            // tens boundary BY DEFINITION (9+1=10), so the running result must be
            // allowed up to 99 even when terms are single-digit
            if (isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) {
                return 99;
            }
            return null; // No limit for other complexity levels
    }
}

function getTermLimit(complexity) {
    switch(complexity) {
        case 'direct-to-4':
            return 4; // Terms can only be 1-4
        case 'direct-to-5':
            return 5; // Terms can only be 1-5
        case 'direct-to-9':
            return 9; // Terms can be 1-9
        case 'direct-counting':
            return 9; // Terms can be 1-9
        default:
            return null; // No term limit for other complexity levels
    }
}

function isAllowedOperation(currentValue, operation, operand, complexity) {
    const directTo4 = {
        '+': [[1,1],[1,2],[1,3],[2,1],[2,2],[3,1]],
        '-': [[1,1],[2,1],[2,2],[3,1],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4]]
    };
    const directTo5New = {
        '+': [[1,5],[2,5],[3,5],[4,5],[5,1],[5,2],[5,3],[5,4]],  // Include operațiile inverse cu 5
        '-': [[5,5],[6,1],[6,5],[7,1],[7,2],[7,5],[8,1],[8,2],[8,3],[8,5],[9,1],[9,2],[9,3],[9,4],[9,5]]  // Include 5-5
    };
    const directTo9New = {
        // Direct-to-9 additions: Include operațiile inverse (6+1, 6+2, etc.)
        '+': [
            [1,6],[1,7],[1,8],  // 1+6=7, 1+7=8, 1+8=9
            [2,6],[2,7],        // 2+6=8, 2+7=9
            [3,6],              // 3+6=9
            [6,1],[6,2],[6,3],  // Operațiile inverse: 6+1=7, 6+2=8, 6+3=9
            [7,1],[7,2],        // 7+1=8, 7+2=9
            [8,1]               // 8+1=9
        ],
        // Direct-to-9 subtractions: Doar operațiile care pot fi făcute DIRECT pe soroban
        // Exclud operațiile care necesită formule Small Friends
        '-': [
            [6,1],[6,5],[6,6],                              // 6-1, 6-5, 6-6 (DIRECT)
            [7,1],[7,2],[7,5],[7,6],[7,7],                  // 7-1, 7-2, 7-5, 7-6, 7-7 (DIRECT)
            [8,1],[8,2],[8,3],[8,5],[8,6],[8,7],[8,8],      // 8-1, 8-2, 8-3, 8-5, 8-6, 8-7, 8-8 (DIRECT)
            [9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9]  // 9-1 to 9-9 (toate DIRECT)
        ]
    };

    // Small Friends - Cumulative allowed operations (in addition to direct-to-9)
    // Each formula includes all operations from previous formulas PLUS direct-to-9
    // UPDATED: Allow both commutative forms (4+1 and 1+4) to enable easier exercise generation
    const smallPlus1 = {
        '+': [[4,1]]  // Only 4+1 (formula +1 = +5-4)
    };
    const smallPlus2 = {
        '+': [[3,2],[4,2]]  // Only 3+2, 4+2 (formula +2 = +5-3)
    };
    const smallPlus3 = {
        '+': [[2,3],[3,3],[4,3]]  // Only 2+3, 3+3, 4+3 (formula +3 = +5-2)
    };
    const smallPlus4 = {
        '+': [[1,4],[2,4],[3,4],[4,4]]  // Only 1+4, 2+4, 3+4, 4+4 (formula +4 = +5-1)
    };
    const smallMinus1 = {
        '-': [[5,1]]  // Only 5-1 (subtraction is not commutative)
    };
    const smallMinus2 = {
        '-': [[5,2],[6,2]]  // 5-2, 6-2
    };
    const smallMinus3 = {
        '-': [[5,3],[6,3],[7,3]]  // 5-3, 6-3, 7-3
    };
    const smallMinus4 = {
        '-': [[5,4],[6,4],[7,4],[8,4]]  // 5-4, 6-4, 7-4, 8-4
    };

    // Helper function to check if a single-digit operation is allowed
    function isSingleDigitAllowed(currentDigit, operandDigit, operation, complexity) {
        // Special case: Starting from 0
        // On soroban, starting from 0 (no beads), you can add any digit 1-9 directly
        if (currentDigit === 0 && operation === '+') {
            // For direct-to-4: can only add 1-4
            if (complexity === 'direct-to-4') {
                return operandDigit >= 1 && operandDigit <= 4;
            }
            // For direct-to-5: can add 1-5
            if (complexity === 'direct-to-5') {
                return operandDigit >= 1 && operandDigit <= 5;
            }
            // For direct-to-9 and direct-counting: can add 1-9
            if (complexity === 'direct-to-9' || complexity === 'direct-counting') {
                return operandDigit >= 1 && operandDigit <= 9;
            }
            // For Small Friends and above: from an empty column any digit 1-9
            // can be set directly (no formula needed)
            if (complexity.startsWith('small-')) {
                return operandDigit >= 1 && operandDigit <= 9;
            }
        }
        // Cannot subtract from 0 (would be negative)
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

        if (complexity.startsWith('small-')) {
            // Always include direct-to-9
            const ops9 = directTo9New[operation] || [];
            const inDirect9 = ops9.some(([v, o]) => v === currentDigit && o === operandDigit);
            if (inDirect9 || inDirect4 || inDirect5) {
                return true;
            }

            // Map formula sets to their operations
            const formulaOps = {
                'plus-1': smallPlus1,
                'plus-2': smallPlus2,
                'plus-3': smallPlus3,
                'plus-4': smallPlus4,
                'minus-1': smallMinus1,
                'minus-2': smallMinus2,
                'minus-3': smallMinus3,
                'minus-4': smallMinus4
            };

            // Interleaved order: +1, -1, +2, -2, +3, -3, +4, -4
            const interleavedOrder = [
                'plus-1', 'minus-1', 'plus-2', 'minus-2',
                'plus-3', 'minus-3', 'plus-4', 'minus-4'
            ];

            // Determine which formulas are known at this level
            let knownFormulas = [];
            if (complexity === 'small-friends-all' || complexity === 'small-friends-all-multi') {
                knownFormulas = interleavedOrder;
            } else {
                const m = complexity.match(/small-(plus|minus)-(\d)/);
                if (m) {
                    const currentKey = `${m[1]}-${m[2]}`;
                    const currentIdx = interleavedOrder.indexOf(currentKey);
                    // Include current level and all previous
                    knownFormulas = interleavedOrder.slice(0, currentIdx + 1);
                }
            }

            // Check if operation is in any known formula set
            for (const key of knownFormulas) {
                const ops = (formulaOps[key] || {})[operation] || [];
                if (ops.some(([v, o]) => v === currentDigit && o === operandDigit)) {
                    return true;
                }
            }

            return false;
        }

        // Big Friends and Family levels
        if (isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) {
            // Check if it's a Big Friends or Family operation
            const isBig = requiresBigFriendsFormula(currentDigit, operation, operandDigit);
            const isFam = isBig && requiresFamilyFormula(currentDigit, operation, operandDigit);

            if (isBig) {
                const allowed = getAllowedBigFriendsFormulas(complexity);
                if (isFam) {
                    // Family formula: only allowed at family levels with the right N
                    return allowed.family.some(f =>
                        f.type === (operation === '+' ? 'plus' : 'minus') && f.N === operandDigit
                    );
                } else {
                    // Pure Big Friends formula: check if operand N is allowed
                    return allowed.bigFriends.some(f =>
                        f.type === (operation === '+' ? 'plus' : 'minus') && f.N === operandDigit
                    );
                }
            }

            // Not a Big Friends operation on units digit: must be direct or small friends
            return isSingleDigitAllowed(currentDigit, operandDigit, operation, 'small-friends-all');
        }

        return true;
    }

    // For multi-digit numbers, check each digit independently
    if (currentValue > 9 || operand > 9) {
        // For big friends and family levels, carry/borrow on the UNITS column IS
        // allowed (that's the formula), but every higher column must also be a
        // valid operation (direct/small friends, with the carry factored in)
        if (isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) {
            const opDigit = operand % 10;
            // Pass currentValue (not units digit) so requiresBigFriendsFormula can check >= 10 for subtraction
            const isBig = requiresBigFriendsFormula(currentValue, operation, opDigit);
            const isFam = isBig && requiresFamilyFormula(currentValue, operation, opDigit);

            // 1. Validate the units column
            if (isBig) {
                const allowed = getAllowedBigFriendsFormulas(complexity);
                const unitsOk = isFam
                    ? allowed.family.some(f => f.type === (operation === '+' ? 'plus' : 'minus') && f.N === opDigit)
                    : allowed.bigFriends.some(f => f.type === (operation === '+' ? 'plus' : 'minus') && f.N === opDigit);
                if (!unitsOk) return false;
            } else if (opDigit !== 0) {
                if (!isSingleDigitAllowed(currentValue % 10, opDigit, operation, 'small-friends-all')) {
                    return false;
                }
            }

            // 2. Validate every higher column, folding in the units carry/borrow.
            //    Cascading carries (tens overflowing into hundreds) are rejected
            //    to keep exercises within the taught formulas.
            let cv = Math.floor(currentValue / 10);
            let ov = Math.floor(operand / 10);
            let adjust = isBig ? 1 : 0; // +1 carry for addition, +1 extra borrow for subtraction
            while (cv > 0 || ov > 0 || adjust > 0) {
                const cd = cv % 10;
                const od = (ov % 10) + adjust;
                adjust = 0;
                if (od !== 0) {
                    if (operation === '+') {
                        if (cd + od >= 10) return false; // cascading carry - rejected
                    } else {
                        if (cd < od) return false; // cascading borrow - rejected
                    }
                    if (!isSingleDigitAllowed(cd, od, operation, 'small-friends-all')) {
                        return false;
                    }
                }
                cv = Math.floor(cv / 10);
                ov = Math.floor(ov / 10);
            }
            return true;
        }

        // For non-big-friends levels: check EVERY column independently.
        // No carry/borrow allowed between columns, and each column's operation
        // must follow the level's single-digit rules. A 0 digit in the operand
        // means "no change" on that column (e.g. 24+10 leaves units untouched).
        let cv = currentValue;
        let ov = operand;
        while (cv > 0 || ov > 0) {
            const cd = cv % 10;
            const od = ov % 10;
            if (od !== 0) {
                if (operation === '+') {
                    if (cd + od >= 10) return false; // carry - not allowed
                } else {
                    if (cd < od) return false; // borrow - not allowed
                }
                if (!isSingleDigitAllowed(cd, od, operation, complexity)) {
                    return false;
                }
            }
            cv = Math.floor(cv / 10);
            ov = Math.floor(ov / 10);
        }

        return true;
    }

    // Single-digit case: use the original logic
    return isSingleDigitAllowed(currentValue, operand, operation, complexity);
}

function getValidOperations(currentResult, complexity, termsArray, operations, totalTerms, digitsAllowed = [1], operationSetting = 'mixed', difficulty = 'medium') {
    const validOps = [];
    const termLimit = getTermLimit(complexity);
    // Easy difficulty at direct-to-9: no operands containing digits 6-9
    const easyDirect9 = difficulty === 'easy' && complexity === 'direct-to-9';
    const hasLargeDigit = n => String(Math.abs(n)).split('').some(d => parseInt(d) >= 6);
    const maxDigits = Math.max(...digitsAllowed);
    const maxLimit = getComplexityLimit(complexity, maxDigits);
    // Strict multi-digit: intermediates must keep the minimum digit count
    const minInter = minResultForDigits(digitsAllowed);

    console.log('[getValidOperations] Finding valid operations for currentResult=', currentResult, 'complexity=', complexity, 'digitsAllowed=', digitsAllowed, 'maxLimit=', maxLimit, 'operation=', operationSetting);

    // Respect the teacher's operation setting (addition-only / subtraction-only / mixed)
    const allowAdd = operationSetting !== 'subtraction';
    const allowSub = operationSetting !== 'addition';

    const tryTerm = (term) => {
        // Try addition
        if (allowAdd) {
            const addResult = currentResult + term;
            if (addResult >= Math.max(1, minInter) && addResult <= maxLimit &&
                isAllowedOperation(currentResult, '+', term, complexity) &&
                !shouldAvoidTermRepetition(termsArray, term, totalTerms) &&
                !isSmallFriendsCombination(currentResult, '+', term) &&
                !isBigFriendsCombination(currentResult, '+', term, complexity) &&
                !isImmediateReverseOperation(operations, termsArray, '+', term)) {
                validOps.push({ op: '+', term: term });
            }
        }

        // Try subtraction
        if (allowSub) {
            const subResult = currentResult - term;
            if (subResult >= minInter && subResult <= maxLimit &&
                isAllowedOperation(currentResult, '-', term, complexity) &&
                !shouldAvoidTermRepetition(termsArray, term, totalTerms) &&
                !isSmallFriendsCombination(currentResult, '-', term) &&
                !isBigFriendsCombination(currentResult, '-', term, complexity) &&
                !isImmediateReverseOperation(operations, termsArray, '-', term)) {
                validOps.push({ op: '-', term: term });
            }
        }
    };

    // Only terms whose digit count is selected (e.g. [2] -> 2-digit terms only).
    // Terms ending in 0 ARE allowed for multi-digit (e.g. 24+10 - the units
    // column stays put); per-column validity is enforced by isAllowedOperation.
    const cap = maxLimit !== null ? maxLimit : parseInt('9'.repeat(maxDigits));
    forEachAllowedTerm(digitsAllowed, cap, (t) => {
        if (t <= 9 && t > termLimit) return; // respect single-digit term limit (1-4 / 1-5)
        if (easyDirect9 && hasLargeDigit(t)) return; // easy: skip 6-9 operands
        tryTerm(t);
    });

    console.log('[getValidOperations] Found', validOps.length, 'valid operations:',
        validOps.map(o => o.op + o.term).join(', '));

    return validOps;
}

function calculateResult(terms, operations) {
    let result = terms[0];
    for (let i = 0; i < operations.length; i++) {
        if (operations[i] === '+') {
            result += terms[i + 1];
        } else {
            result -= terms[i + 1];
        }
    }
    return Math.round(result * 100) / 100; // Round to 2 decimals
}

function shouldAvoidTermRepetition(termsArray, candidateTerm, totalTermCount = 3) {
    if (termsArray.length === 0) return false;

    // Configuration: Max consecutive repetitions only
    // REMOVED: Max total occurrences check (was limiting variety too much)
    // STRICT: Prevent any consecutive repetitions (no two identical terms in a row)
    const MAX_CONSECUTIVE_REPETITIONS = 1;

    // Count consecutive repetitions at the end of the array
    let consecutiveCount = 0;
    for (let i = termsArray.length - 1; i >= 0; i--) {
        if (Math.abs(termsArray[i]) === Math.abs(candidateTerm)) {
            consecutiveCount++;
        } else {
            break;
        }
    }

    if (consecutiveCount >= MAX_CONSECUTIVE_REPETITIONS) {
        console.log('[shouldAvoidTermRepetition] Avoiding term due to consecutive repetitions:', {
            term: candidateTerm,
            consecutiveCount,
            max: MAX_CONSECUTIVE_REPETITIONS
        });
        return true;
    }

    return false;
}

function isSmallFriendsCombination(currentValue, operation, operand) {
    // For multi-digit numbers, work with last digits only
    const currentLastDigit = currentValue % 10;
    const operandLastDigit = operand % 10;

    // Only check for operands 1-4 (Small Friends formulas)
    if (operandLastDigit < 1 || operandLastDigit > 4) {
        return false;
    }

    if (operation === '+') {
        // Check if this is one of the Small Friends addition combinations
        // +1: starting from 4 (4+1)
        // +2: starting from 3 or 4 (3+2, 4+2)
        // +3: starting from 2, 3, or 4 (2+3, 3+3, 4+3)
        // +4: starting from 1, 2, 3, or 4 (1+4, 2+4, 3+4, 4+4)
        const minStartingNumber = 5 - operandLastDigit; // For +1: 4, +2: 3, +3: 2, +4: 1
        return currentLastDigit >= minStartingNumber && currentLastDigit <= 4;
    } else if (operation === '-') {
        // Check if this is one of the Small Friends subtraction combinations
        // Forbidden combinations (require Small Friends formula):
        // 5-1, 5-2, 5-3, 5-4: subtracting from heaven bead only
        // 6-2, 6-3, 6-4: need to cross heaven bead with formula
        // 7-3, 7-4: need to cross heaven bead with formula
        // 8-4: need to cross heaven bead with formula

        if (currentLastDigit === 5) {
            // From 5: cannot subtract 1-4 directly (all require formula)
            return true;
        } else if (currentLastDigit === 6) {
            // From 6: can do 6-1 directly, but 6-2, 6-3, 6-4 require formula
            return operandLastDigit >= 2;
        } else if (currentLastDigit === 7) {
            // From 7: can do 7-1, 7-2 directly, but 7-3, 7-4 require formula
            return operandLastDigit >= 3;
        } else if (currentLastDigit === 8) {
            // From 8: can do 8-1, 8-2, 8-3 directly, but 8-4 requires formula
            return operandLastDigit >= 4;
        } else if (currentLastDigit === 9) {
            // From 9: can do 9-1, 9-2, 9-3, 9-4 directly (all have enough lower beads)
            return false;
        }
    }

    return false;
}

function isBigFriendsCombination(currentValue, operation, operand, complexity = null) {
    // For multi-digit numbers, work with last digits only
    const currentLastDigit = currentValue % 10;
    const operandLastDigit = operand % 10;

    // Only check for operands 6-9 (Big Friends formulas)
    if (operandLastDigit < 6 || operandLastDigit > 9) {
        return false;
    }

    // If complexity is provided and operation is explicitly allowed, don't block it
    if (complexity && isAllowedOperation(currentValue, operation, operand, complexity)) {
        return false;
    }

    if (operation === '+') {
        // For single-digit calculations (1-9), check if we can add directly
        const result = currentLastDigit + operandLastDigit;
        // If result > 9, it would require carrying/Big Friends formula
        if (result > 9) {
            return true;
        }
    } else if (operation === '-') {
        // For subtraction, if operand > currentValue (last digit), it would require borrowing/Big Friends
        if (operandLastDigit > currentLastDigit) {
            return true;
        }
        // Also check if subtracting would require removing beads we don't have
        // For values 6-9, we have heaven bead (5) + lower beads (currentLastDigit-5)
        if (currentLastDigit >= 6 && currentLastDigit <= 9) {
            const lowerBeadsUsed = currentLastDigit - 5;
            // If we need to subtract more than what's available on lower beads
            // and can't just remove heaven bead, it requires Big Friends
            if (operandLastDigit > lowerBeadsUsed && operandLastDigit !== currentLastDigit - 4) {
                return true;
            }
        }
    }

    return false;
}

function isImmediateReverseOperation(operations, termsArray, currentOp, currentTerm) {
    // Prevent simple patterns like +5-5, +6-6, -7+7, etc.
    // Check if the last operation was the opposite of the current one with the same term
    if (operations.length === 0 || termsArray.length === 0) {
        return false;
    }

    const lastOp = operations[operations.length - 1];
    const lastTerm = termsArray[termsArray.length - 1];

    // If last operation was + and current is -, or vice versa, with the same term
    if ((lastOp === '+' && currentOp === '-' || lastOp === '-' && currentOp === '+') &&
        lastTerm === currentTerm) {
        console.log('[isImmediateReverseOperation] Avoiding immediate reverse operation:', {
            last: lastOp + lastTerm,
            current: currentOp + currentTerm
        });
        return true;
    }

    return false;
}

function canPerformDirectly(currentValue, operation, operand, maxLimit, isLastOperation) {
    const result = operation === '+' ? currentValue + operand : currentValue - operand;

    // Check bounds - for multi-digit numbers, maxLimit applies to the entire number
    // but for single-digit maxLimit (4, 5, 9), we need special handling
    // Allow result = 0 for operations like 9-9, 8-8, 7-7, 6-6, etc.
    if (result < 0) return false;

    // For single-digit soroban logic (direct-to-4, direct-to-5, direct-to-9)
    if (maxLimit !== null && maxLimit <= 9) {
        // For multi-digit numbers, check digit-by-digit
        if (currentValue > 9 || operand > 9 || result > 9) {
            // Multi-digit case: extract last digits and check for carry/borrow
            const currentLastDigit = currentValue % 10;
            const operandLastDigit = operand % 10;

            if (operation === '+') {
                // Check if there's a carry from the last digit
                if (currentLastDigit + operandLastDigit >= 10) {
                    return false; // Carry between digits - not direct
                }
            } else {
                // Check if there's a borrow from the last digit
                if (currentLastDigit < operandLastDigit) {
                    return false; // Borrow between digits - not direct
                }
            }

            // Now validate the last digit operation using the single-digit rules below
            // Replace currentValue and operand with their last digits for validation
            currentValue = currentLastDigit;
            operand = operandLastDigit;

            // Recalculate result for last digit
            const lastDigitResult = operation === '+' ? currentValue + operand : currentValue - operand;

            // Last digit result should be within 0-9 (no carry/borrow)
            if (lastDigitResult < 0 || lastDigitResult > 9) return false;
        } else {
            // Single-digit case: check maxLimit
            if (result > maxLimit) return false;
        }
    } else if (maxLimit !== null) {
        // Large maxLimit: just check bounds
        if (result > maxLimit) return false;
    }

    // For direct calculation with limits (direct-to-4, direct-to-5, direct-to-9)
    if (maxLimit !== null && maxLimit <= 9) {
        if (operation === '+') {
            // From 1-4: can only add if result stays <= 4 (direct within lower beads)
            // If result would be 5+, it requires Small Friends formula (not direct)
            if (currentValue <= 4) {
                if (maxLimit === 4) {
                    // For direct-to-4: result must stay <= 4
                    return result <= 4;
                } else if (maxLimit === 5) {
                    // For direct-to-5: result can be 5 ONLY if it's the last operation
                    // Otherwise must stay <= 4 (to avoid getting stuck at 5)
                    if (result === 5) {
                        return isLastOperation; // Allow 5 only as final result
                    }
                    return result <= 4;
                } else if (maxLimit === 9) {
                    // For direct-to-9 and direct-counting with maxLimit=9
                    // From 1-4, we can add directly in these cases:
                    if (result <= 4) {
                        // Staying in lower beads (1-4) - always direct
                        return true;
                    } else if (result === 5) {
                        // Reaching exactly 5 - direct (just flip heaven bead)
                        return true;
                    } else if (result >= 6 && result <= 9) {
                        // Reaching 6-9 from 1-4 is direct if operand >= 5:
                        // - operand 5: flip heaven bead, lower beads stay (e.g., 1+5=6, 4+5=9)
                        // - operand 6-9: push heaven bead + (operand-5) lower beads
                        //   Heaven is always free (currentValue <= 4), and lower beads available
                        //   since result <= 9 guarantees (operand-5) <= (4-currentValue)
                        //   Examples: 1+6=7, 1+7=8, 1+8=9, 2+6=8, 2+7=9, 3+6=9
                        // NOT direct: operand 1-4 requires Small Friends (e.g., 4+3=7 → +5-2+3)
                        return operand >= 5;
                    }
                    return false;
                }
            } else if (currentValue === 5) {
                // From 5: can add 1-4 directly to get 6-9
                // (heaven bead already set, just add lower beads)
                if (maxLimit === 9 && operand >= 1 && operand <= 4) {
                    return true;
                }
                return false;
            } else if (currentValue >= 6) {
                // From 6-9: can add if we stay <= maxLimit and have beads available
                if (maxLimit === 9) {
                    const lowerBeadsUsed = currentValue - 5;
                    const lowerBeadsAvailable = 4 - lowerBeadsUsed;
                    return operand <= lowerBeadsAvailable && result <= 9;
                }
            }
        } else {
            // Subtraction
            if (currentValue <= 4) {
                // From 1-4: can subtract directly if we have enough lower beads
                // Allow result = 0 for operations like 1-1, 2-2, 3-3, 4-4
                return operand <= currentValue && result >= 0;
            } else if (currentValue === 5) {
                // From 5 (heaven bead only): can ONLY subtract 5 directly to get 0
                // Subtracting 1-4 from 5 requires Small Friends formulas: -1=+4-5, -2=+3-5, etc.
                // But we don't allow result 0, so no direct subtraction from 5
                return false;
            } else if (currentValue >= 6 && maxLimit === 9) {
                // From 6-9: can subtract in these cases:
                const lowerBeadsUsed = currentValue - 5;
                if (operand <= lowerBeadsUsed) {
                    // Case 1: Subtract from lower beads only (e.g., 7-1=6, 9-3=6)
                    return true;
                } else if (operand === 5) {
                    // Case 2: Subtract exactly 5 (remove heaven bead, keep lower beads)
                    // E.g., 6-5=1, 7-5=2, 8-5=3, 9-5=4
                    return true;
                } else if (operand === currentValue) {
                    // Case 3: Subtract all (result = 0) - allowed for operations like 9-9, 8-8, 7-7, 6-6
                    return true;
                } else if (operand > lowerBeadsUsed && operand < currentValue) {
                    // Case 4: Subtracting more than lower beads but less than total
                    // Need to check if we can do this directly
                    // E.g., 9-6=3 means removing heaven (5) and 1 lower bead
                    // This can be done as: remove 5, then remove 1 more = direct if operand-5 <= lowerBeadsUsed
                    return operand - 5 <= lowerBeadsUsed && operand - 5 >= 0;
                }
                return false;
            }
        }
    }

    return true;
}

function requiresCarryingFormula(currentValue, operation, operand) {
    if (operation === '+') {
        const result = currentValue + operand;

        // GOLDEN RULE: Any addition resulting in >= 10 requires a carrying formula
        // Examples: 9+1 (formula: +1=-9+10), 8+2 (formula: +2=-8+10), 7+3, 6+4, etc.
        if (result >= 10) {
            return true;
        }

        // Big Friends operands (6-9): These are ALWAYS considered formula exercises in training context
        // Even if they can technically be done directly (like 1+8=9), they are taught using formulas
        // This is pedagogically important to maintain consistency in formula training
        if (operand >= 6 && operand <= 9) {
            // For Big Friends operands, check if formula would typically be used
            // From the teaching perspective, +6,+7,+8,+9 are formula operations when:
            // - The result would require using the +10-complement approach
            // - Or when starting from values where direct manipulation is complex
            return isBigFriendsCombination(currentValue, operation, operand);
        }
    } else if (operation === '-') {
        // Check if subtraction would require borrowing from next column
        if (operand > currentValue) {
            return true;
        }

        // Big Friends operands (6-9): Check if formula is needed
        if (operand >= 6 && operand <= 9) {
            return isBigFriendsCombination(currentValue, operation, operand);
        }
    }

    return false;
}

function validateNoConsecutiveBigFriends(terms, operations) {
    let result = terms[0];
    let previousRequiredCarrying = false;

    // Check each step
    for (let i = 0; i < operations.length; i++) {
        const currentOp = operations[i];
        const currentTerm = terms[i + 1];

        // Check if current operation requires a carrying/complex formula
        const currentRequiresCarrying = requiresCarryingFormula(result, currentOp, currentTerm);

        // If both current and previous operations require carrying formulas, reject
        if (currentRequiresCarrying && previousRequiredCarrying) {
            console.log('[validateNoConsecutiveBigFriends] Consecutive carrying formulas detected at step', i + 1);
            console.log('[validateNoConsecutiveBigFriends] Current value before operation:', result,
                       'Operation:', currentOp, currentTerm, 'Result:',
                       currentOp === '+' ? result + currentTerm : result - currentTerm);
            console.log('[validateNoConsecutiveBigFriends] Terms so far:', terms.slice(0, i + 2),
                       'Operations:', operations.slice(0, i + 1));
            return false;
        }

        // Update result for next iteration
        if (currentOp === '+') {
            result += currentTerm;
        } else {
            result -= currentTerm;
        }

        // Update flag for next iteration
        previousRequiredCarrying = currentRequiresCarrying;
    }

    return true;
}

function validateIntermediateResults(terms, operations, complexity = null) {
    let result = terms[0];

    // For big friends and family, intermediate results can go to 99
    const isBigOrFamily = complexity && (isBigFriendsLevel(complexity) || isFamilyLevel(complexity));
    const maxResult = isBigOrFamily ? 99 : 9;

    // First term must be >= 0
    if (result < 0) {
        console.log('[validateIntermediateResults] First term is < 0:', result);
        return false;
    }

    // For Small Friends levels, first term must also be <= 9 (single digit)
    if (complexity && isSmallFriendsLevel(complexity) && result > 9) {
        console.log('[validateIntermediateResults] First term exceeds 9 for Small Friends:', result);
        return false;
    }

    // Check each intermediate step
    for (let i = 0; i < operations.length; i++) {
        if (operations[i] === '+') {
            result += terms[i + 1];
        } else {
            result -= terms[i + 1];
        }

        // Check that intermediate result doesn't go negative
        // FURTHER RELAXED: Allow passing through 0 (e.g., 5-5=0, then 0+3=3)
        if (result < 0) {
            console.log('[validateIntermediateResults] Intermediate result < 0 at step', i + 1, ':', result);
            console.log('[validateIntermediateResults] Terms so far:', terms.slice(0, i + 2), 'Operations:', operations.slice(0, i + 1));
            return false;
        }

        // For Small Friends levels, enforce upper bound of 9 (single digit limit)
        // This prevents invalid operations like 5+5=10 which exceed single-digit capacity
        if (complexity && isSmallFriendsLevel(complexity) && result > 9) {
            console.log('[validateIntermediateResults] Intermediate result exceeds 9 for Small Friends at step', i + 1, ':', result);
            console.log('[validateIntermediateResults] Terms so far:', terms.slice(0, i + 2), 'Operations:', operations.slice(0, i + 1));
            return false;
        }

        // For Big Friends and Family levels, enforce upper bound of 99 (2-digit limit)
        if (isBigOrFamily && result > maxResult) {
            console.log('[validateIntermediateResults] Intermediate result exceeds', maxResult, 'for Big/Family at step', i + 1, ':', result);
            return false;
        }
    }

    return true;
}

function canGenerateFormulaFromState(currentValue, operation, formulaNumber) {
    // Check if using the specific formula number would require the formula
    const result = operation === '+' ? currentValue + formulaNumber : currentValue - formulaNumber;

    // Must be in valid range
    if (result < 1 || result > 9) {
        return false;
    }

    // Check if this operation would require the formula
    return requiresSmallFriendsFormula(currentValue, operation, formulaNumber);
}

function getSmallFriendsFormulaNumber(complexity) {
    const match = complexity.match(/small-(plus|minus)-(\d)/);
    return match ? parseInt(match[2]) : null;
}

function getAvailableFormulasForLevel(complexity) {
    // Interleaved order: +1, -1, +2, -2, +3, -3, +4, -4
    const interleavedOrder = [
        {type:'plus', number:1}, {type:'minus', number:1},
        {type:'plus', number:2}, {type:'minus', number:2},
        {type:'plus', number:3}, {type:'minus', number:3},
        {type:'plus', number:4}, {type:'minus', number:4}
    ];

    if (complexity === 'small-friends-all' || complexity === 'small-friends-all-multi') {
        return {
            currentFormula: null,
            previousFormulas: interleavedOrder,
            canUseDirect: true,
            isPlus: null
        };
    }

    const match = complexity.match(/small-(plus|minus)-(\d)/);
    if (!match) return null;

    const isPlus = match[1] === 'plus';
    const currentFormula = parseInt(match[2]);
    const currentIdx = interleavedOrder.findIndex(f => f.type === match[1] && f.number === currentFormula);

    const previousFormulas = interleavedOrder.slice(0, currentIdx);

    return {
        currentFormula: currentFormula,
        previousFormulas: previousFormulas,
        canUseDirect: true,
        isPlus: isPlus
    };
}

function generateNumber(settings, isFirstTerm = false) {
    const { fractions, complexity } = settings;
    // Pick this term's digit count from the allowed selection (mixed exercises
    // sample per term; strict selections always produce that digit count)
    const allowedCounts = resolveDigitsAllowed(settings);
    const digits = allowedCounts[Math.floor(Math.random() * allowedCounts.length)];

    let num;

    // Generate base number based on complexity
    switch(complexity) {
        case 'direct-to-4':
            // Direct calculation with 4: EVERY digit follows direct-to-4 rules (1-4)
            // e.g. 2 digits: 24, 43, 12 (never 74 - the tens column also uses 1-4)
            if (digits === 1) {
                num = Math.floor(Math.random() * 4) + 1; // 1-4
            } else {
                num = 0;
                for (let d = 0; d < digits; d++) {
                    num = num * 10 + (Math.floor(Math.random() * 4) + 1); // each digit 1-4
                }
            }
            break;
        case 'direct-to-5':
            // Direct calculation with 5: use only 1-5 for the last digit
            // CRITICAL: For first term, use only 1-4 (not 5) to avoid getting stuck
            // From 5, you cannot add (requires Big Friends) or subtract (requires Small Friends) directly
            if (digits === 1) {
                if (isFirstTerm) {
                    num = Math.floor(Math.random() * 4) + 1; // 1-4 only for first term
                } else {
                    num = Math.floor(Math.random() * 5) + 1; // 1-5 for other terms
                }
            } else {
                // EVERY digit follows direct-to-5 rules; first term uses 1-4 per
                // column (from 5 nothing can be added/subtracted directly)
                num = 0;
                for (let d = 0; d < digits; d++) {
                    const digitMax = isFirstTerm ? 4 : 5;
                    num = num * 10 + (Math.floor(Math.random() * digitMax) + 1);
                }
            }
            break;
        case 'direct-to-9':
            // Direct calculation with 9: use 1-9 for the last digit
            if (digits === 1) {
                // Favor larger numbers (6-9) with 60% probability for increased difficulty
                const rand = Math.random();
                if (rand < 0.6) {
                    // 60% - Generate large numbers (6-9) to challenge kids with heaven+earth bead combinations
                    num = Math.floor(Math.random() * 4) + 6; // 6-9
                } else {
                    // 40% - Generate smaller numbers (1-5)
                    num = Math.floor(Math.random() * 5) + 1; // 1-5
                }
            } else {
                // For multi-digit numbers, generate number with last digit 1-9
                const max = parseInt('9'.repeat(digits));
                const min = parseInt('1' + '0'.repeat(digits - 1));
                num = Math.floor(Math.random() * (max - min + 1)) + min;
                // Ensure last digit is 1-9 (no 0)
                const lastDigit = num % 10;
                if (lastDigit === 0) {
                    num = Math.floor(num / 10) * 10 + (Math.floor(Math.random() * 9) + 1);
                }
            }
            break;
        case 'direct-counting':
            const max = parseInt('9'.repeat(digits));
            const min = digits > 1 ? parseInt('1' + '0'.repeat(digits - 1)) : 1;
            // For first term, ensure better distribution across the range
            if (isFirstTerm && digits === 1) {
                // Use weighted random to favor variety: 30% low (1-3), 40% mid (4-6), 30% high (7-9)
                const range = Math.random();
                if (range < 0.3) {
                    num = Math.floor(Math.random() * 3) + 1; // 1-3
                } else if (range < 0.7) {
                    num = Math.floor(Math.random() * 3) + 4; // 4-6
                } else {
                    num = Math.floor(Math.random() * 3) + 7; // 7-9
                }
            } else {
                num = Math.floor(Math.random() * (max - min + 1)) + min;
                // For multi-digit numbers, ensure last digit is NOT 0 (1-9 only)
                if (digits > 1) {
                    const lastDigit = num % 10;
                    if (lastDigit === 0) {
                        num = Math.floor(num / 10) * 10 + (Math.floor(Math.random() * 9) + 1);
                    }
                }
            }
            break;

        // Small Friends levels - Progressive logic: 50% direct + 50% small friends
        // UPDATED: Pass isFirstTerm to enable strategic first term generation
        case 'small-plus-1':
        case 'small-plus-2':
        case 'small-plus-3':
        case 'small-plus-4':
        case 'small-minus-1':
        case 'small-minus-2':
        case 'small-minus-3':
        case 'small-minus-4':
        case 'small-friends-all-multi':
        case 'small-friends-all':
            num = generateSmallFriendsNumber(complexity, digits, isFirstTerm);
            break;

        // Big Friends levels - Progressive logic: 33% direct + 33% small + 34% big
        case 'big-plus-1':
        case 'big-plus-2':
        case 'big-plus-3':
        case 'big-plus-4':
        case 'big-plus-5':
        case 'big-plus-6':
        case 'big-plus-7':
        case 'big-plus-8':
        case 'big-plus-9':
        case 'big-minus-1':
        case 'big-minus-2':
        case 'big-minus-3':
        case 'big-minus-4':
        case 'big-minus-5':
        case 'big-minus-6':
        case 'big-minus-7':
        case 'big-minus-8':
        case 'big-minus-9':
        case 'big-friends-all':
            num = generateBigFriendsNumber(complexity, digits);
            break;

        // Family - Progressive logic: 25% each level
        case 'family':
            num = generateFamilyNumber(digits);
            break;

        // Specific Family formula levels (family-plus-6, family-minus-6, etc.)
        case 'family-plus-6':
        case 'family-minus-6':
        case 'family-plus-7':
        case 'family-minus-7':
        case 'family-plus-8':
        case 'family-minus-8':
        case 'family-plus-9':
        case 'family-minus-9':
        case 'family-all':
            num = generateBigFriendsNumber(complexity, digits);
            break;

        // Mix - Progressive logic: all levels
        case 'mix':
            num = generateMixNumber(digits);
            break;

        default:
            // Fallback to direct counting
            const maxNum = parseInt('9'.repeat(digits));
            const minNum = digits > 1 ? parseInt('1' + '0'.repeat(digits - 1)) : 1;
            num = Math.floor(Math.random() * (maxNum - minNum + 1)) + minNum;
    }

    // Add decimals if needed
    if (fractions === 'one') {
        num += Math.floor(Math.random() * 10) / 10;
    } else if (fractions === 'two') {
        num += Math.floor(Math.random() * 100) / 100;
    }

    return num;
}

function generateSmallFriendsNumber(complexity, digits, isFirstTerm = false) {
    // For first term in Small Friends PLUS formulas, favor 1-4 to enable formula application
    // For Small Friends MINUS formulas, favor 5-9 to enable formula application
    if (isFirstTerm && digits === 1) {
        const match = complexity.match(/small-(plus|minus)-(\d)/);
        if (match) {
            const isPlusFormula = match[1] === 'plus';
            const formulaNumber = parseInt(match[2]);

            if (isPlusFormula) {
                // For PLUS formulas (+1, +2, +3, +4): favor starting from 1-4
                // This enables formula application: 4+1, 3+2, 2+3, 1+4, etc.
                // 70% chance to start with 1-4, 30% with 5-9 for variety
                if (Math.random() < 0.7) {
                    return Math.floor(Math.random() * 4) + 1; // 1-4
                } else {
                    return Math.floor(Math.random() * 5) + 5; // 5-9
                }
            } else {
                // For MINUS formulas (-1, -2, -3, -4): favor starting from 5-9
                // This enables formula application: 5-1, 6-2, 7-3, 8-4, etc.
                // 70% chance to start with 5-9, 30% with 1-4 for variety
                if (Math.random() < 0.7) {
                    return Math.floor(Math.random() * 5) + 5; // 5-9
                } else {
                    return Math.floor(Math.random() * 4) + 1; // 1-4
                }
            }
        }
    }

    // For non-first terms or multi-digit numbers, generate normally
    if (digits === 1) {
        return Math.floor(Math.random() * 9) + 1; // 1-9 (no 0)
    } else {
        const max = parseInt('9'.repeat(digits));
        const min = parseInt('1' + '0'.repeat(digits - 1));
        let num = Math.floor(Math.random() * (max - min + 1)) + min;
        // Ensure last digit is not 0
        const lastDigit = num % 10;
        if (lastDigit === 0) {
            num = Math.floor(num / 10) * 10 + (Math.floor(Math.random() * 9) + 1);
        }
        return num;
    }
}

function generateBigFriendsNumber(complexity, digits) {
    const rand = Math.random();
    if (rand < 0.33) {
        // 33% - Direct counting
        if (digits === 1) {
            return Math.floor(Math.random() * 9) + 1; // 1-9 (no 0)
        } else {
            const max = parseInt('9'.repeat(digits));
            const min = parseInt('1' + '0'.repeat(digits - 1));
            let num = Math.floor(Math.random() * (max - min + 1)) + min;
            // Ensure last digit is not 0
            const lastDigit = num % 10;
            if (lastDigit === 0) {
                num = Math.floor(num / 10) * 10 + (Math.floor(Math.random() * 9) + 1);
            }
            return num;
        }
    } else if (rand < 0.66) {
        // 33% - Small friends
        if (digits === 1) {
            return Math.floor(Math.random() * 9) + 1; // 1-9 (no 0)
        } else {
            const max = parseInt('9'.repeat(digits));
            const min = parseInt('1' + '0'.repeat(digits - 1));
            let num = Math.floor(Math.random() * (max - min + 1)) + min;
            // Ensure last digit is not 0
            const lastDigit = num % 10;
            if (lastDigit === 0) {
                num = Math.floor(num / 10) * 10 + (Math.floor(Math.random() * 9) + 1);
            }
            return num;
        }
    } else {
        // 34% - Big friends
        const max = parseInt('9'.repeat(digits));
        const min = digits > 1 ? parseInt('1' + '0'.repeat(digits - 1)) : 1;
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
}

function generateFamilyNumber(digits) {
    const rand = Math.random();
    if (rand < 0.25) {
        // 25% - Direct counting
        return Math.floor(Math.random() * 9) + 1; // 1-9 (no 0)
    } else if (rand < 0.5) {
        // 25% - Small friends
        return Math.floor(Math.random() * 9) + 1; // 1-9 (no 0)
    } else if (rand < 0.75) {
        // 25% - Big friends
        const max = parseInt('9'.repeat(digits));
        const min = digits > 1 ? parseInt('1' + '0'.repeat(digits - 1)) : 1;
        return Math.floor(Math.random() * (max - min + 1)) + min;
    } else {
        // 25% - Complex combinations
        const max = parseInt('9'.repeat(digits));
        const min = digits > 1 ? parseInt('1' + '0'.repeat(digits - 1)) : 1;
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
}

function generateMixNumber(digits) {
    const rand = Math.random();
    if (rand < 0.2) {
        // 20% - Direct counting
        return Math.floor(Math.random() * 10); // 0-9
    } else if (rand < 0.4) {
        // 20% - Small friends
        return Math.floor(Math.random() * 10); // 0-9
    } else if (rand < 0.6) {
        // 20% - Big friends
        const max = parseInt('9'.repeat(digits));
        const min = digits > 1 ? parseInt('1' + '0'.repeat(digits - 1)) : 1;
        return Math.floor(Math.random() * (max - min + 1)) + min;
    } else if (rand < 0.8) {
        // 20% - Family
        return generateFamilyNumber(digits);
    } else {
        // 20% - Complex/random
        const max = parseInt('9'.repeat(digits));
        const min = digits > 1 ? parseInt('1' + '0'.repeat(digits - 1)) : 1;
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
}

function generateExerciseTerms(settings) {
    const { terms, operation, negative, complexity } = settings;
    // Difficulty: easy = ~1 formula per 4 ops / no 6-9 operands at direct-to-9;
    // medium = balanced (default); hard = ~3 formulas per 4 ops (current +
    // previous formulas combined) / 6-9 operands required at direct-to-9
    const difficulty = settings.difficulty || 'medium';
    // digitsAllowed: e.g. [2] = strictly 2-digit numbers, [1,2] = mixed
    const digitsAllowed = resolveDigitsAllowed(settings);
    const digits = Math.max(...digitsAllowed);
    // Strict multi-digit: the running value must never drop below the
    // smallest selected digit count (e.g. [2] -> intermediates stay >= 10)
    const minInter = minResultForDigits(digitsAllowed);
    const maxLimit = getComplexityLimit(complexity, digits);

    // Formula-slot count per difficulty (ops = terms - 1)
    const formulaSlotCount = (ops, mediumCount) => {
        if (difficulty === 'easy') return Math.max(1, Math.round(ops * 0.25));
        if (difficulty === 'hard') return Math.max(1, Math.ceil(ops / 2));
        return mediumCount;
    };
    // Minimum gap between formula slots (hard packs them closer)
    const slotGap = difficulty === 'hard' ? 2 : 3;

    console.log('[generateExerciseTerms] Generating exercise with:', { terms, operation, negative, complexity, difficulty, digitsAllowed, minInter, maxLimit });

    // For direct calculation levels, regenerate if result is 0 or invalid
    // Dynamic attempts and timeout based on term count (more terms = more attempts needed)
    // UPDATED: Increased attempts for Small Friends formulas which are more restrictive
    let maxAttempts = terms <= 3 ? 100 : terms === 4 ? 150 : terms === 5 ? 300 : 200;
    // Multi-digit formula levels have a tighter state space - allow more retries
    if (digits > 1 && (isSmallFriendsLevel(complexity) || isBigFriendsLevel(complexity) || isFamilyLevel(complexity))) {
        maxAttempts *= 2;
    }
    let attempt = 0;
    let result;
    let termsArray = [];
    let operations = [];

    // Safety timeout: prevent infinite loops by tracking generation time
    // More terms = longer timeout (combinatorial explosion)
    // UPDATED: Increased timeout for Small Friends levels
    const startTime = Date.now();
    const maxGenerationTime = terms <= 3 ? 8000 : terms === 4 ? 12000 : terms === 5 ? 30000 : 20000;

    do {
        // Safety check: if generation takes more than max time, break out
        if (Date.now() - startTime > maxGenerationTime) {
            console.error('[generateExerciseTerms] Generation timeout exceeded (' + (maxGenerationTime / 1000) + 's)! Breaking out to prevent browser hang.');
            alert('Eroare la generarea exercițiului. Vă rugăm încercați din nou sau schimbați setările.');
            break;
        }
        termsArray = [];
        operations = [];

        // Generate first term (always positive)
        termsArray.push(generateNumber(settings, true));

        // Addition-only: the first term must leave room for all following
        // additions (each adds at least 1) within the level's result limit
        if (operation === 'addition' && isDirectCalculationLevel(complexity) && maxLimit !== null) {
            let ftGuard = 0;
            while (termsArray[0] + (terms - 1) > maxLimit && ftGuard++ < 50) {
                termsArray[0] = generateNumber(settings, true);
            }
        }

        // Pre-calculate term types distribution for Small Friends levels
        // This ensures exercises have a BALANCED mix of formulas
        // UPDATED: More flexible distribution - aim for current formula but allow fallback
        let termTypesDistribution = [];
        if (isSmallFriendsLevel(complexity) && digits > 1) {
            // MULTI-DIGIT Small Friends: formula on the units column at a random
            // position, remaining ops free (per-column rules via isAllowedOperation)
            const m = complexity.match(/^small-(plus|minus)-(\d)$/);
            if (m) {
                const fType = m[1];
                const fN = parseInt(m[2]);
                const remainingTerms = terms - 1;
                const numSlots = formulaSlotCount(remainingTerms, remainingTerms >= 5 ? 2 : 1);
                const positions = [];
                let posGuard = 0;
                // Avoid the last position (steering into the applicable state
                // works better with a free op after the formula)
                const posRange = Math.max(1, remainingTerms - 1);
                while (positions.length < numSlots && posGuard++ < 50) {
                    const pos = Math.floor(Math.random() * posRange);
                    if (positions.every(q => Math.abs(q - pos) >= slotGap)) positions.push(pos);
                }

                if (positions.includes(0)) {
                    // Formula first: first term's units must be in the applicable set
                    const appUnits = smallFormulaApplicableUnits(fType, fN);
                    if (appUnits.length > 0) {
                        const u = appUnits[Math.floor(Math.random() * appUnits.length)];
                        // Small friends applicable units are never 0, so any count works
                        const count = digitsAllowed[Math.floor(Math.random() * digitsAllowed.length)];
                        termsArray[0] = buildNumberWithUnits(u, count);
                    }
                }

                for (let j = 0; j < remainingTerms; j++) {
                    if (positions.includes(j)) {
                        termTypesDistribution.push({ type: 'small-current', formulaType: fType, formulaN: fN });
                    } else {
                        termTypesDistribution.push({ type: 'free', formulaType: null, formulaN: null });
                    }
                }
            }
            // small-friends-all / all-multi: leave distribution empty (free natural mix)
        } else if (isSmallFriendsLevel(complexity)) {
            const formulaNumber = getSmallFriendsFormulaNumber(complexity);
            const availableFormulas = getAvailableFormulasForLevel(complexity);
            const remainingTerms = terms - 1; // Exclude first term

            // The current formula count scales with difficulty; the rest
            // integrates previous formulas + direct calc for varied, natural
            // exercises (2+5-2-1+5) instead of repetitive patterns (5-1+1-1+5)
            let currentFormulaCount, otherTermsCount;
            currentFormulaCount = formulaSlotCount(remainingTerms, remainingTerms >= 5 ? 2 : 1);
            otherTermsCount = remainingTerms - currentFormulaCount;

            // Build distribution array with current formula terms
            for (let j = 0; j < currentFormulaCount; j++) {
                termTypesDistribution.push({
                    type: 'current',
                    formulaNumber: formulaNumber,
                    formulaType: availableFormulas.isPlus ? 'plus' : 'minus'
                });
            }

            // Distribute "other" terms between previous formulas and direct calculations
            if (otherTermsCount > 0) {
                if (availableFormulas.previousFormulas && availableFormulas.previousFormulas.length > 0) {
                    // Split remaining slots between previous formulas and direct calc:
                    // easy = all direct (simple filler ops), medium = ~50/50,
                    // hard = previous-formula heavy (total ~3 formulas per 4 ops)
                    const directRatio = difficulty === 'easy' ? 1 : difficulty === 'hard' ? 0.25 : 0.5;
                    const directCount = Math.ceil(otherTermsCount * directRatio);
                    const previousCount = otherTermsCount - directCount;

                    // Add previous formula terms
                    for (let j = 0; j < previousCount; j++) {
                        const randomFormula = availableFormulas.previousFormulas[
                            Math.floor(Math.random() * availableFormulas.previousFormulas.length)
                        ];
                        termTypesDistribution.push({
                            type: 'previous',
                            formulaNumber: randomFormula.number,
                            formulaType: randomFormula.type
                        });
                    }

                    // Add direct calculation terms
                    for (let j = 0; j < directCount; j++) {
                        termTypesDistribution.push({
                            type: 'direct',
                            formulaNumber: null,
                            formulaType: null
                        });
                    }
                } else {
                    // No previous formulas available, use direct calculations
                    for (let j = 0; j < otherTermsCount; j++) {
                        termTypesDistribution.push({
                            type: 'direct',
                            formulaNumber: null,
                            formulaType: null
                        });
                    }
                }
            }

            // Shuffle the distribution to avoid predictable patterns
            // Fisher-Yates shuffle algorithm
            for (let j = termTypesDistribution.length - 1; j > 0; j--) {
                const k = Math.floor(Math.random() * (j + 1));
                [termTypesDistribution[j], termTypesDistribution[k]] = [termTypesDistribution[k], termTypesDistribution[j]];
            }

            console.log('[generateExerciseTerms] Pre-calculated term types distribution:', {
                totalTerms: remainingTerms,
                currentFormulaCount,
                otherTermsCount,
                distribution: termTypesDistribution.map(t => t.type)
            });
        }

        // Pre-calculate term types distribution for Big Friends and Family levels
        if (isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) {
            const remainingTerms = terms - 1;

            // Parse current formula from complexity string
            const bigMatch = complexity.match(/^big-(plus|minus)-(\d+)$/);
            const famMatch = complexity.match(/^family-(plus|minus)-(\d+)$/);
            const isSpecificLevel = bigMatch || famMatch;
            const currentFormulaType = bigMatch ? bigMatch[1] : famMatch ? famMatch[1] : null;
            const currentFormulaN = bigMatch ? parseInt(bigMatch[2]) : famMatch ? parseInt(famMatch[2]) : null;
            const isFamilyFormula = !!famMatch;

            if (isSpecificLevel && currentFormulaN !== null) {
                // Formula applications at RANDOM positions (count per difficulty).
                // The free operations before each steer the running value
                // organically toward the applicable state - this gives varied,
                // natural exercises like 1+6+2+1+8 (7, 9, formula 9+1, 18)
                // instead of rigid repeated patterns like 9+1+9+1.
                const numFormulaSlots = formulaSlotCount(remainingTerms, remainingTerms >= 6 ? 2 : 1);
                const formulaPositions = [];
                let posGuard = 0;
                while (formulaPositions.length < numFormulaSlots && posGuard++ < 50) {
                    const pos = Math.floor(Math.random() * remainingTerms);
                    // Keep a gap between formula slots so the exercise has room
                    // to wander back to the applicable state naturally
                    if (formulaPositions.every(q => Math.abs(q - pos) >= slotGap)) {
                        formulaPositions.push(pos);
                    }
                }
                formulaPositions.sort((a, b) => a - b);

                if (formulaPositions[0] === 0) {
                    // Formula comes first: the first term must be in an applicable state
                    const appUnits = bigFormulaApplicableUnits(currentFormulaType, currentFormulaN, isFamilyFormula);
                    if (appUnits.length > 0) {
                        const u = appUnits[Math.floor(Math.random() * appUnits.length)];
                        const count = digitsAllowed[Math.floor(Math.random() * digitsAllowed.length)];
                        if (currentFormulaType === 'minus' || u === 0) {
                            // Minus formulas need a tens bead to borrow from (value >= 10)
                            termsArray[0] = count >= 2 ? buildNumberWithUnits(u, count) : 10 + u;
                        } else {
                            termsArray[0] = count >= 2 ? buildNumberWithUnits(u, count) : u;
                        }
                    }
                }

                for (let j = 0; j < remainingTerms; j++) {
                    if (formulaPositions.includes(j)) {
                        termTypesDistribution.push({
                            type: 'big-current',
                            formulaType: currentFormulaType,
                            formulaN: currentFormulaN,
                            isFamily: isFamilyFormula
                        });
                    } else {
                        termTypesDistribution.push({
                            type: 'small-or-direct',
                            formulaType: null,
                            formulaN: null
                        });
                    }
                }
            } else {
                // big-friends-all or family-all: no pre-distribution
                // termTypesDistribution stays empty; term generation uses isAllowedOperation directly
            }

            console.log('[generateExerciseTerms] Big Friends distribution:', {
                totalTerms: remainingTerms,
                distribution: termTypesDistribution.map(t => t.type + (t.formulaN ? `(${t.formulaType[0]}${t.formulaN})` : ''))
            });
        }

        // Generate remaining terms
        for (let i = 1; i < terms; i++) {
            let op;

            // For Small Friends levels, determine operation based on pre-allocated formula type
            if (isSmallFriendsLevel(complexity) && termTypesDistribution.length > 0) {
                const termIndex = i - 1;
                const termTypeConfig = termTypesDistribution[termIndex];

                // Force operation to match formula type for formula terms
                if (termTypeConfig.type === 'current' || termTypeConfig.type === 'previous') {
                    // Use formula type to determine operation
                    op = termTypeConfig.formulaType === 'plus' ? '+' : '-';
                } else {
                    // For direct calculations, use normal logic
                    if (operation === 'mixed') {
                        op = Math.random() > 0.5 ? '+' : '-';
                    } else {
                        op = operation === 'addition' ? '+' : '-';
                    }
                }
            // For Big Friends / Family levels with pre-allocated distribution
            } else if ((isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) && termTypesDistribution.length > 0) {
                const termIndex = i - 1;
                const termTypeConfig = termTypesDistribution[termIndex];

                if (termTypeConfig.type === 'big-current' || termTypeConfig.type === 'big-previous') {
                    op = termTypeConfig.formulaType === 'plus' ? '+' : '-';
                } else {
                    // small-or-direct: random operation
                    if (operation === 'mixed') {
                        op = Math.random() > 0.5 ? '+' : '-';
                    } else {
                        op = operation === 'addition' ? '+' : '-';
                    }
                }
            } else {
                // Normal operation selection for non-Small Friends levels
                if (operation === 'mixed') {
                    op = Math.random() > 0.5 ? '+' : '-';
                } else {
                    op = operation === 'addition' ? '+' : '-';
                }
            }

            operations.push(op);

            let term;
            let validTermFound = false;
            let termAttempts = 0;

            // For direct calculation levels, ensure operations can be performed directly
            if (isDirectCalculationLevel(complexity)) {
                const currentResult = calculateResult(termsArray, operations.slice(0, -1));

                // NEW APPROACH: Pre-calculate ONLY valid operations for current result
                // This ensures we never get stuck - we only choose from operations we know will work
                // Instead of trying all possible operations and checking validity during iteration,
                // we first build a list of guaranteed-valid operations, then randomly pick one
                let validOperations = getValidOperations(currentResult, complexity, termsArray, operations, terms, digitsAllowed, operation, difficulty);

                // Addition-only: keep budget for the remaining operations
                // (each remaining op adds at least 1, so leave enough headroom)
                if (operation === 'addition' && maxLimit !== null) {
                    const remainingOps = (terms - 1) - i;
                    validOperations = validOperations.filter(vo =>
                        currentResult + vo.term + remainingOps <= maxLimit);
                }

                // If no valid operations exist, regenerate the entire exercise
                if (validOperations.length === 0) {
                    console.log('[generateExerciseTerms] No valid operations for', complexity, 'at currentResult=', currentResult, ', regenerating exercise');
                    termsArray = [];
                    operations = [];
                    break;
                }

                // Choose randomly from the valid operations
                const randomOp = validOperations[Math.floor(Math.random() * validOperations.length)];
                term = randomOp.term;
                op = randomOp.op;
                operations[operations.length - 1] = op; // Update the operation we pushed earlier
                validTermFound = true;

                console.log('[generateExerciseTerms] Selected valid operation:', {
                    currentResult,
                    operation: op + term,
                    newResult: op === '+' ? currentResult + term : currentResult - term,
                    availableOptions: validOperations.length
                });
            } else if (isSmallFriendsLevel(complexity) && digits > 1) {
                // MULTI-DIGIT Small Friends: apply the formula on the units column
                // at its pre-allocated slot, steer free ops toward the applicable
                // state; every column is validated by isAllowedOperation
                const currentResult = calculateResult(termsArray, operations.slice(0, -1));
                const termIndex = i - 1;
                const slot = termTypesDistribution[termIndex];

                if (slot && slot.type === 'small-current') {
                    const N = slot.formulaN;
                    const fOp = slot.formulaType === 'plus' ? '+' : '-';
                    if (requiresSmallFriendsFormula(currentResult, fOp, N)) {
                        // Formula term: single-digit N, or multi-digit with units N
                        // (e.g. 45-21 exercises formula -1 on the units column)
                        const formulaOptions = [];
                        forEachAllowedTerm(digitsAllowed, maxLimit !== null ? maxLimit : 999, (tf) => {
                            if (tf % 10 !== N) return;
                            const nr = fOp === '+' ? currentResult + tf : currentResult - tf;
                            if (nr >= Math.max(1, minInter) && nr <= maxLimit &&
                                isAllowedOperation(currentResult, fOp, tf, complexity)) {
                                formulaOptions.push(tf);
                            }
                        });
                        if (formulaOptions.length > 0) {
                            op = fOp;
                            operations[operations.length - 1] = op;
                            term = formulaOptions[Math.floor(Math.random() * formulaOptions.length)];
                            validTermFound = true;
                            console.log('[generateExerciseTerms] Small Friends multi-digit formula term:', { currentResult, op, term });
                        }
                    }

                    if (!validTermFound && termIndex + 1 < termTypesDistribution.length &&
                        termTypesDistribution[termIndex + 1].type !== 'small-current') {
                        // Formula not applicable here: push its slot one position later
                        // and use this op to steer into the applicable state
                        termTypesDistribution[termIndex + 1] = { type: 'small-current', formulaType: slot.formulaType, formulaN: slot.formulaN };
                        termTypesDistribution[termIndex] = { type: 'free', formulaType: null, formulaN: null };
                    }
                }

                if (!validTermFound) {
                    // Free / steering op: any valid term with an allowed digit count
                    const opsToTry = operation === 'mixed' ? ['+', '-']
                        : [operation === 'addition' ? '+' : '-'];
                    const candidates = [];
                    const termCap = Math.min(maxLimit || 99, 999);
                    for (const o of opsToTry) {
                        forEachAllowedTerm(digitsAllowed, termCap, (t) => {
                            const nr = o === '+' ? currentResult + t : currentResult - t;
                            if (nr >= Math.max(1, minInter) && nr <= maxLimit && isAllowedOperation(currentResult, o, t, complexity)) {
                                candidates.push({ o, t, newResult: nr });
                            }
                        });
                    }

                    // Steer toward the next formula slot's applicable units
                    let nextFormulaIdx = -1;
                    for (let k = termIndex; k < termTypesDistribution.length; k++) {
                        if (termTypesDistribution[k] && termTypesDistribution[k].type === 'small-current') {
                            nextFormulaIdx = k;
                            break;
                        }
                    }
                    let pool = candidates;
                    if (nextFormulaIdx >= 0) {
                        const s = termTypesDistribution[nextFormulaIdx];
                        const targetUnits = smallFormulaApplicableUnits(s.formulaType, s.formulaN);
                        const isApplicable = v => targetUnits.includes(v % 10);
                        const freeOpsAfterThis = Math.max(0, nextFormulaIdx - termIndex - 1);
                        if (freeOpsAfterThis === 0) {
                            const hard = candidates.filter(c => isApplicable(c.newResult));
                            if (hard.length > 0) pool = hard;
                        } else {
                            const canReachInOneStep = v => {
                                let found = false;
                                for (const o2 of ['+', '-']) {
                                    if (found) break;
                                    forEachAllowedTerm(digitsAllowed, maxLimit !== null ? maxLimit : 999, (t2) => {
                                        if (found) return;
                                        const nv = o2 === '+' ? v + t2 : v - t2;
                                        if (nv >= Math.max(1, minInter) && nv <= maxLimit && isApplicable(nv) &&
                                            isAllowedOperation(v, o2, t2, complexity)) {
                                            found = true;
                                        }
                                    });
                                }
                                return found;
                            };
                            const soft = candidates.filter(c => !isApplicable(c.newResult) && canReachInOneStep(c.newResult));
                            if (soft.length > 0) pool = soft;
                        }
                    }

                    // Difficulty flavor for filler ops: hard prefers formula ops,
                    // easy prefers plain direct ops
                    if (difficulty === 'hard') {
                        const f = pool.filter(c => requiresSmallFriendsFormula(currentResult, c.o, c.t));
                        if (f.length > 0) pool = f;
                    } else if (difficulty === 'easy') {
                        const nf = pool.filter(c => !requiresSmallFriendsFormula(currentResult, c.o, c.t));
                        if (nf.length > 0) pool = nf;
                    }

                    if (pool.length > 0) {
                        const pick = pool[Math.floor(Math.random() * pool.length)];
                        op = pick.o;
                        operations[operations.length - 1] = op;
                        term = pick.t;
                        validTermFound = true;
                    }
                }

                if (!validTermFound) {
                    console.log('[generateExerciseTerms] Small Friends multi-digit: no valid term at', currentResult, ', regenerating');
                    termsArray = [];
                    operations = [];
                    break;
                }
            } else if (isSmallFriendsLevel(complexity)) {
                // For Small Friends levels, use progressive learning with GUARANTEED mix:
                // - 80% current formula (majority)
                // - 20% previous formulas + direct calculations (minority)
                // The distribution is pre-calculated to ensure every exercise has variety
                const currentResult = calculateResult(termsArray, operations.slice(0, -1));
                const formulaNumber = getSmallFriendsFormulaNumber(complexity);
                const availableFormulas = getAvailableFormulasForLevel(complexity);

                console.log('[generateExerciseTerms] Small Friends level:', {
                    complexity,
                    formulaNumber,
                    currentResult,
                    op,
                    availableFormulas
                });

                // Check if it's possible to generate a valid term for this operation
                // For addition: need currentResult + 1 <= 9 (can add at least 1)
                // For subtraction: need currentResult - 1 >= 1 (can subtract at least 1)
                // If not possible, switch operation instead of regenerating entire exercise
                if (op === '+' && currentResult >= 9) {
                    console.log('[generateExerciseTerms] Cannot add from currentResult=9, switching to subtraction:', { currentResult, op });
                    op = '-';
                    operations[operations.length - 1] = op;

                    // Update the term type configuration to match the new operation
                    const termIndex = i - 1;
                    if (termTypesDistribution[termIndex].type !== 'direct') {
                        termTypesDistribution[termIndex].formulaType = 'minus';
                    }
                } else if (op === '-' && currentResult <= 1) {
                    console.log('[generateExerciseTerms] Cannot subtract from currentResult=1, switching to addition:', { currentResult, op });
                    op = '+';
                    operations[operations.length - 1] = op;

                    // Update the term type configuration to match the new operation
                    const termIndex = i - 1;
                    if (termTypesDistribution[termIndex].type !== 'direct') {
                        termTypesDistribution[termIndex].formulaType = 'plus';
                    }
                }

                // Use pre-calculated term type from distribution instead of random selection
                // This guarantees that every exercise will have a mix of formulas
                const termIndex = i - 1; // Adjust for first term (which is always positive)
                const termTypeConfig = termTypesDistribution[termIndex];

                let targetType = termTypeConfig.type;
                let targetFormulaNumber = termTypeConfig.formulaNumber;
                let targetFormulaType = termTypeConfig.formulaType;

                console.log('[generateExerciseTerms] Using pre-allocated target from distribution:', {
                    termIndex,
                    targetType,
                    targetFormulaNumber,
                    targetFormulaType,
                    distributionPosition: `${termIndex + 1}/${termTypesDistribution.length}`
                });

                // Flag to track if we need to regenerate the entire exercise
                let shouldRegenerateExercise = false;

                // Generate term based on target type
                while (!validTermFound && termAttempts < 30) {
                    if (targetType === 'direct') {
                        // Generate a direct calculation term (operations with 4, 5, 9 that don't require formulas)
                        // For direct calculations, we can use any number that can be performed directly
                        const directOptions = [];

                        // Can we add/subtract 1-9 without formulas?
                        for (let t = 1; t <= 9; t++) {
                            const testResult = op === '+' ? currentResult + t : currentResult - t;
                            if (testResult >= 1 && testResult <= 9) {
                                // Check if this can be done directly (without formulas)
                                // AND that it's allowed for the current complexity level
                                const isAllowed = isAllowedOperation(currentResult, op, t, complexity);
                                if (!requiresSmallFriendsFormula(currentResult, op, t) && isAllowed) {
                                    directOptions.push(t);
                                }
                            }
                        }

                        if (directOptions.length > 0) {
                            // STRATEGIC GENERATION: Check if the next term should be the current formula
                            // If so, try to generate a term that leads to a favorable state for that formula
                            let preferredOptions = [];
                            const nextIndex = termIndex + 1;
                            if (nextIndex < termTypesDistribution.length &&
                                termTypesDistribution[nextIndex].type === 'current' &&
                                termTypesDistribution[nextIndex].formulaNumber === formulaNumber) {
                                // Next term should be the current formula, try to reach favorable state
                                const nextOp = termTypesDistribution[nextIndex].formulaType === 'plus' ? '+' : '-';

                                // Calculate which result we need for the formula to be applicable
                                // For formula +N: we need currentResult in range [1, min(4, 9-N)]
                                // For formula -N: we need currentResult to be 5 or in range [6, min(9, 5+N)]
                                for (const option of directOptions) {
                                    const intermediateResult = op === '+' ? currentResult + option : currentResult - option;

                                    if (nextOp === '+') {
                                        // For plus formula: need intermediateResult + formulaNumber to require Small Friends
                                        // This happens when intermediateResult is 1-4 and result would be 5-9
                                        const wouldRequireFormula = intermediateResult >= 1 &&
                                                                    intermediateResult <= 4 &&
                                                                    intermediateResult + formulaNumber >= 5 &&
                                                                    intermediateResult + formulaNumber <= 9;
                                        if (wouldRequireFormula &&
                                            isAllowedOperation(intermediateResult, nextOp, formulaNumber, complexity)) {
                                            preferredOptions.push(option);
                                        }
                                    } else {
                                        // For minus formula: need intermediateResult - formulaNumber to require Small Friends
                                        const wouldRequireFormula = ((intermediateResult === 5 && formulaNumber >= 1 && formulaNumber <= 4) ||
                                                                    (intermediateResult >= 6 && intermediateResult <= 9 &&
                                                                     intermediateResult - formulaNumber >= 1 &&
                                                                     intermediateResult - formulaNumber <= 4 &&
                                                                     formulaNumber > (intermediateResult - 5)));
                                        if (wouldRequireFormula &&
                                            isAllowedOperation(intermediateResult, nextOp, formulaNumber, complexity)) {
                                            preferredOptions.push(option);
                                        }
                                    }
                                }

                                if (preferredOptions.length > 0) {
                                    console.log('[generateExerciseTerms] Found', preferredOptions.length, 'strategic options that lead to formula state:', {
                                        currentResult, op, preferredOptions, nextFormula: formulaNumber
                                    });
                                }
                            }

                            // Use preferred options if available, otherwise use all direct options
                            let optionsToUse = preferredOptions.length > 0 ? preferredOptions : directOptions;

                            // BOOST digit 5 usage: Prioritize 5 if available to meet Small Friends digit 5 requirement
                            // Check how many 5s we have in current terms
                            const currentFivesCount = termsArray.filter(t => Math.abs(t) === 5).length;
                            const currentFivesPercentage = termsArray.length > 0 ? currentFivesCount / termsArray.length : 0;
                            const targetPercentage = terms <= 3 ? 0.6 : terms === 4 ? 0.5 : terms === 5 ? 0.4 : 0.3;

                            // BOOST digit 5 usage: If we need more 5s and 5 is available, prioritize it
                            let prioritizeFive = false;
                            if (currentFivesPercentage < targetPercentage && optionsToUse.includes(5)) {
                                // 70% chance to use 5 when below target
                                if (Math.random() < 0.7) {
                                    prioritizeFive = true;
                                    console.log('[generateExerciseTerms] Prioritizing digit 5 to meet target percentage:', {
                                        currentPercentage: (currentFivesPercentage * 100).toFixed(0) + '%',
                                        targetPercentage: (targetPercentage * 100).toFixed(0) + '%'
                                    });
                                }
                            }

                            // Shuffle options to maintain variety
                            let shuffledOptions;
                            if (prioritizeFive) {
                                // Keep 5 at front, shuffle the rest
                                const withoutFive = optionsToUse.filter(opt => opt !== 5);
                                for (let i = withoutFive.length - 1; i > 0; i--) {
                                    const j = Math.floor(Math.random() * (i + 1));
                                    [withoutFive[i], withoutFive[j]] = [withoutFive[j], withoutFive[i]];
                                }
                                shuffledOptions = [5, ...withoutFive];
                            } else {
                                // Regular shuffle
                                shuffledOptions = optionsToUse.slice();
                                for (let i = shuffledOptions.length - 1; i > 0; i--) {
                                    const j = Math.floor(Math.random() * (i + 1));
                                    [shuffledOptions[i], shuffledOptions[j]] = [shuffledOptions[j], shuffledOptions[i]];
                                }
                            }

                            for (const option of shuffledOptions) {
                                if (!shouldAvoidTermRepetition(termsArray, option, terms)) {
                                    term = option;
                                    validTermFound = true;
                                    console.log('[generateExerciseTerms] Found direct calculation term:', {
                                        currentResult, op, term, result: op === '+' ? currentResult + term : currentResult - term
                                    });
                                    break;
                                }
                            }

                            // If all options blocked by repetition, use first option anyway
                            if (!validTermFound) {
                                term = shuffledOptions[0];
                                validTermFound = true;
                                console.log('[generateExerciseTerms] Using direct term with relaxed repetition:', {
                                    currentResult, op, term,
                                    reason: 'All direct options blocked by repetition'
                                });
                            }
                        } else {
                            // No direct options, fallback to formula
                            targetType = 'current';
                            targetFormulaNumber = formulaNumber;
                            targetFormulaType = availableFormulas.isPlus ? 'plus' : 'minus';
                            // Update operation to match formula type
                            op = targetFormulaType === 'plus' ? '+' : '-';
                            operations[operations.length - 1] = op;
                        }
                    } else {
                        // Generate a formula term (current or previous)
                        // Operation is already set correctly to match targetFormulaType

                        // Improved adaptive formula selection:
                        // 1. Collect all valid formula numbers from current state
                        // 2. Prefer target formula number if valid
                        // 3. Use any valid alternative formula to maintain type guarantee
                        // 4. Only fall back to direct calculation if no formulas work

                        // Collect all valid formula numbers for the current state
                        const validFormulaNumbers = [];
                        for (let fNum = 1; fNum <= 4; fNum++) {
                            if (canGenerateFormulaFromState(currentResult, op, fNum)) {
                                const isAllowed = isAllowedOperation(currentResult, op, fNum, complexity);
                                if (isAllowed) {
                                    validFormulaNumbers.push(fNum);
                                }
                            }
                        }

                        console.log('[generateExerciseTerms] Valid formula numbers from current state:', {
                            currentResult, op, validFormulaNumbers, targetFormulaNumber
                        });

                        // If no valid formula numbers exist, try to navigate back to favorable state
                        // UPDATED: Smart navigation - try to get back to favorable range for formula application
                        if (validFormulaNumbers.length === 0) {
                            // For current formula type, try to navigate to favorable state by switching operation
                            if (targetType === 'current') {
                                const currentDigit = currentResult % 10;

                                // For PLUS formulas: need currentResult 1-4 to apply formula
                                if (availableFormulas.isPlus && currentDigit > 4) {
                                    // Try switching to subtraction to get back to 1-4 range
                                    console.log('[generateExerciseTerms] Current state unfavorable for PLUS formula, trying subtraction to navigate back');
                                    op = '-';
                                    operations[operations.length - 1] = op;

                                    // Find a subtraction that brings us to 1-4
                                    const navigateOptions = [];
                                    for (let t = 1; t <= 9; t++) {
                                        const resultDigit = (currentDigit - t + 10) % 10;
                                        if (resultDigit >= 1 && resultDigit <= 4 && currentResult - t >= 1) {
                                            const isAllowed = isAllowedOperation(currentResult, '-', t, complexity);
                                            if (isAllowed && !requiresSmallFriendsFormula(currentResult, '-', t)) {
                                                navigateOptions.push(t);
                                            }
                                        }
                                    }

                                    if (navigateOptions.length > 0) {
                                        term = navigateOptions[Math.floor(Math.random() * navigateOptions.length)];
                                        validTermFound = true;
                                        console.log('[generateExerciseTerms] Navigating to favorable state with subtraction:', {
                                            currentResult, term, newResult: currentResult - term
                                        });
                                    }
                                }
                                // For MINUS formulas: need currentResult 5-9 to apply formula
                                else if (!availableFormulas.isPlus && currentDigit < 5) {
                                    // Try switching to addition to get to 5-9 range
                                    console.log('[generateExerciseTerms] Current state unfavorable for MINUS formula, trying addition to navigate back');
                                    op = '+';
                                    operations[operations.length - 1] = op;

                                    // Find an addition that brings us to 5-9
                                    const navigateOptions = [];
                                    for (let t = 1; t <= 9; t++) {
                                        const resultDigit = (currentDigit + t) % 10;
                                        if (resultDigit >= 5 && resultDigit <= 9 && currentResult + t <= 9) {
                                            const isAllowed = isAllowedOperation(currentResult, '+', t, complexity);
                                            if (isAllowed && !requiresSmallFriendsFormula(currentResult, '+', t)) {
                                                navigateOptions.push(t);
                                            }
                                        }
                                    }

                                    if (navigateOptions.length > 0) {
                                        term = navigateOptions[Math.floor(Math.random() * navigateOptions.length)];
                                        validTermFound = true;
                                        console.log('[generateExerciseTerms] Navigating to favorable state with addition:', {
                                            currentResult, term, newResult: currentResult + term
                                        });
                                    }
                                }
                            }

                            // If navigation didn't work, try previous formulas
                            if (!validTermFound && availableFormulas.previousFormulas &&
                                availableFormulas.previousFormulas.length > 0 && targetType !== 'previous') {
                                console.log('[generateExerciseTerms] No current formula possible, trying previous formulas');
                                targetType = 'previous';
                                const randomPrevious = availableFormulas.previousFormulas[
                                    Math.floor(Math.random() * availableFormulas.previousFormulas.length)
                                ];
                                targetFormulaNumber = randomPrevious.number;
                                targetFormulaType = randomPrevious.type;
                                continue;
                            }

                            // Last resort: fall back to direct calculation
                            if (!validTermFound) {
                                console.log('[generateExerciseTerms] No formulas possible from state, switching to direct calculation');
                                targetType = 'direct';
                                continue;
                            }
                        }

                        // Only proceed with formula selection if we haven't found a term yet (via navigation)
                        if (!validTermFound) {
                            // Select formula number: prefer target, but accept any valid option
                            let candidateNumbers = validFormulaNumbers.slice();

                            // Prioritize target formula number if it's in the valid list
                            if (targetFormulaNumber && validFormulaNumbers.includes(targetFormulaNumber)) {
                                candidateNumbers = [targetFormulaNumber, ...validFormulaNumbers.filter(n => n !== targetFormulaNumber)];
                            }

                            // Try candidates in order, checking repetition constraints
                            for (const fNum of candidateNumbers) {
                                if (!shouldAvoidTermRepetition(termsArray, fNum, terms)) {
                                    term = fNum;
                                    const result = op === '+' ? currentResult + term : currentResult - term;
                                    validTermFound = true;
                                    console.log('[generateExerciseTerms] Found formula term:', {
                                        currentResult, op, term, result,
                                        targetType, targetFormulaNumber,
                                        wasTargetUsed: term === targetFormulaNumber
                                    });
                                    break;
                                }
                            }

                            // If all valid formulas are blocked by repetition, relax constraint slightly
                            if (!validTermFound && validFormulaNumbers.length > 0) {
                                // Use the first valid formula even if it repeats (better than regenerating)
                                term = candidateNumbers[0];
                                const result = op === '+' ? currentResult + term : currentResult - term;
                                validTermFound = true;
                                console.log('[generateExerciseTerms] Using formula with relaxed repetition constraint:', {
                                    currentResult, op, term, result,
                                    reason: 'All valid formulas blocked by repetition'
                                });
                            }
                        }
                    }

                    termAttempts++;
                }

                // If we need to regenerate the entire exercise (formula couldn't be generated),
                // skip fallback and break out to trigger regeneration
                if (shouldRegenerateExercise) {
                    console.log('[generateExerciseTerms] Skipping fallback, will regenerate entire exercise');
                    termsArray = [];
                    operations = [];
                    break; // Exit the terms generation loop
                }

                // If no valid term found after all attempts, try direct calculation as final fallback
                if (!validTermFound) {
                    console.log('[generateExerciseTerms] Attempting direct calculation as final fallback');

                    // Collect valid direct calculation options
                    const fallbackOptions = [];
                    for (let t = 1; t <= 9; t++) {
                        const testResult = op === '+' ? currentResult + t : currentResult - t;
                        const isAllowed = isAllowedOperation(currentResult, op, t, complexity);
                        if (testResult >= 1 && testResult <= 9 &&
                            !requiresSmallFriendsFormula(currentResult, op, t) &&
                            isAllowed) {
                            fallbackOptions.push(t);
                        }
                    }

                    // Try options without repetition first, then with relaxed constraint
                    for (const t of fallbackOptions) {
                        if (!shouldAvoidTermRepetition(termsArray, t, terms)) {
                            term = t;
                            validTermFound = true;
                            console.log('[generateExerciseTerms] Using direct calculation fallback:', {
                                currentResult, op, term, result: op === '+' ? currentResult + t : currentResult - t
                            });
                            break;
                        }
                    }

                    // If all blocked by repetition, use first valid option
                    if (!validTermFound && fallbackOptions.length > 0) {
                        term = fallbackOptions[0];
                        validTermFound = true;
                        console.log('[generateExerciseTerms] Using direct fallback with relaxed repetition:', {
                            currentResult, op, term
                        });
                    }
                }

                // If still no valid term, try switching operation as last resort before regenerating
                if (!validTermFound) {
                    const originalOp = op;
                    op = op === '+' ? '-' : '+';
                    operations[operations.length - 1] = op;

                    console.log('[generateExerciseTerms] Switching operation as last resort:', {
                        currentResult, originalOp, newOp: op
                    });

                    // Collect valid options with switched operation
                    const switchedOptions = [];
                    for (let t = 1; t <= 9; t++) {
                        const testResult = op === '+' ? currentResult + t : currentResult - t;
                        const isAllowed = isAllowedOperation(currentResult, op, t, complexity);
                        if (testResult >= 1 && testResult <= 9 && isAllowed) {
                            switchedOptions.push(t);
                        }
                    }

                    // Try options without repetition first
                    for (const t of switchedOptions) {
                        if (!shouldAvoidTermRepetition(termsArray, t, terms)) {
                            term = t;
                            validTermFound = true;
                            console.log('[generateExerciseTerms] Found valid term with switched operation:', {
                                currentResult, op, term, result: op === '+' ? currentResult + t : currentResult - t
                            });
                            break;
                        }
                    }

                    // If all blocked by repetition, use first valid option
                    if (!validTermFound && switchedOptions.length > 0) {
                        term = switchedOptions[0];
                        validTermFound = true;
                        console.log('[generateExerciseTerms] Using switched operation with relaxed repetition:', {
                            currentResult, op, term
                        });
                    }
                }

                // If still no valid term after trying both operations, regenerate the entire exercise
                if (!validTermFound) {
                    console.log('[generateExerciseTerms] No valid term possible with either operation, regenerating exercise:', {
                        currentResult, targetFormulaNumber, targetType
                    });
                    // Break out and regenerate the entire exercise
                    termsArray = [];
                    operations = [];
                    break;
                }
            } else if ((isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) && termTypesDistribution.length > 0) {
                const currentResult = calculateResult(termsArray, operations.slice(0, -1));
                const termIndex = i - 1;
                const termTypeConfig = termTypesDistribution[termIndex];

                if (termTypeConfig.type === 'big-current' || termTypeConfig.type === 'big-previous') {
                    const N = termTypeConfig.formulaN;
                    const formulaOp = termTypeConfig.formulaType === 'plus' ? '+' : '-';
                    const needsFamily = termTypeConfig.isFamily;

                    // Check if current state allows this formula
                    let canApply = false;
                    if (formulaOp === '+') {
                        const bigFriendsOk = requiresBigFriendsFormula(currentResult, '+', N);
                        const familyOk = requiresFamilyFormula(currentResult, '+', N);
                        canApply = bigFriendsOk && (needsFamily ? familyOk : !familyOk);
                    } else {
                        const bigFriendsOk = requiresBigFriendsFormula(currentResult, '-', N);
                        const familyOk = requiresFamilyFormula(currentResult, '-', N);
                        canApply = bigFriendsOk && (needsFamily ? familyOk : !familyOk);
                    }

                    if (canApply) {
                        // The formula term can be single-digit (just N) or multi-digit
                        // with units digit N (e.g. 21 for formula +1 in 2-digit mode);
                        // higher columns are validated per column by isAllowedOperation
                        const formulaOptions = [];
                        forEachAllowedTerm(digitsAllowed, maxLimit !== null ? maxLimit : 999, (tf) => {
                            if (tf % 10 !== N) return;
                            const nr = op === '+' ? currentResult + tf : currentResult - tf;
                            if (nr >= Math.max(1, minInter) && nr <= maxLimit &&
                                isAllowedOperation(currentResult, op, tf, complexity)) {
                                formulaOptions.push(tf);
                            }
                        });
                        if (formulaOptions.length > 0) {
                            term = formulaOptions[Math.floor(Math.random() * formulaOptions.length)];
                            validTermFound = true;
                            console.log('[generateExerciseTerms] Big Friends formula term:', {
                                currentResult, op, term, type: termTypeConfig.type
                            });
                        }
                    }

                    if (!validTermFound) {
                        console.log('[generateExerciseTerms] Big Friends formula not applicable at currentResult=' + currentResult + ', steering instead');
                    }
                }

                if (!validTermFound) {
                    // STEERING: pick a term that puts the running value in a state where
                    // the NEXT formula slot is applicable. Consider BOTH operations.
                    const opsToTry = operation === 'mixed' ? ['+', '-']
                        : [operation === 'addition' ? '+' : '-'];

                    // All valid candidates (op, term) at the current state,
                    // restricted to the selected digit counts
                    const candidates = [];
                    for (const o of opsToTry) {
                        forEachAllowedTerm(digitsAllowed, maxLimit !== null ? maxLimit : 999, (t) => {
                            const newResult = o === '+' ? currentResult + t : currentResult - t;
                            if (newResult >= Math.max(1, minInter) && newResult <= maxLimit &&
                                isAllowedOperation(currentResult, o, t, complexity)) {
                                candidates.push({ o, t, newResult });
                            }
                        });
                    }

                    // MULTI-STEP STEERING toward the next formula slot:
                    // - the op right BEFORE the formula must land in the applicable state
                    // - earlier free ops stay natural, but prefer values from which the
                    //   applicable state remains reachable in one allowed step
                    let nextFormulaIdx = -1;
                    for (let k = termIndex; k < termTypesDistribution.length; k++) {
                        const s = termTypesDistribution[k];
                        if (s.type === 'big-current' || s.type === 'big-previous') {
                            nextFormulaIdx = k;
                            break;
                        }
                    }

                    let pool = candidates;
                    if (nextFormulaIdx >= 0) {
                        const slot = termTypesDistribution[nextFormulaIdx];
                        const targetUnits = bigFormulaApplicableUnits(
                            slot.formulaType, slot.formulaN, !!slot.isFamily);
                        const needsTens = slot.formulaType === 'minus';
                        const isApplicable = v => targetUnits.includes(v % 10) && (!needsTens || v >= 10);

                        // Free ops remaining before the formula slot AFTER this one
                        // (if THIS slot is the failed formula slot itself, treat as 0)
                        const freeOpsAfterThis = Math.max(0, nextFormulaIdx - termIndex - 1);

                        if (freeOpsAfterThis === 0) {
                            // Last chance: this op must land in the applicable state
                            const hard = candidates.filter(c => isApplicable(c.newResult));
                            if (hard.length > 0) pool = hard;
                        } else {
                            // Natural op, but keep the applicable state reachable in one step
                            // and don't consume it early (the pre-formula op should land it)
                            const canReachInOneStep = v => {
                                let found = false;
                                for (const o2 of ['+', '-']) {
                                    if (found) break;
                                    forEachAllowedTerm(digitsAllowed, maxLimit !== null ? maxLimit : 999, (t2) => {
                                        if (found) return;
                                        const nv = o2 === '+' ? v + t2 : v - t2;
                                        if (nv >= Math.max(1, minInter) && nv <= maxLimit && isApplicable(nv) &&
                                            isAllowedOperation(v, o2, t2, complexity)) {
                                            found = true;
                                        }
                                    });
                                }
                                return found;
                            };
                            const soft = candidates.filter(c =>
                                !isApplicable(c.newResult) && canReachInOneStep(c.newResult));
                            if (soft.length > 0) pool = soft;
                        }
                    }

                    // Difficulty flavor for filler ops: hard prefers formula ops
                    // (previous big/small formulas), easy prefers plain direct ops
                    if (difficulty === 'hard') {
                        const f = pool.filter(c =>
                            requiresBigFriendsFormula(currentResult, c.o, c.t % 10) ||
                            requiresSmallFriendsFormula(currentResult, c.o, c.t));
                        if (f.length > 0) pool = f;
                    } else if (difficulty === 'easy') {
                        const nf = pool.filter(c =>
                            !requiresBigFriendsFormula(currentResult, c.o, c.t % 10) &&
                            !requiresSmallFriendsFormula(currentResult, c.o, c.t));
                        if (nf.length > 0) pool = nf;
                    }

                    if (pool.length > 0) {
                        const pick = pool[Math.floor(Math.random() * pool.length)];
                        op = pick.o;
                        operations[operations.length - 1] = op;
                        term = pick.t;
                        validTermFound = true;
                        console.log('[generateExerciseTerms] Big Friends steering term:', {
                            currentResult, op, term, newResult: pick.newResult,
                            steered: pool !== candidates
                        });
                    }
                }

                // No valid candidate at all: regenerate the whole exercise
                // (never push a term that breaks soroban rules)
                if (!validTermFound) {
                    console.log('[generateExerciseTerms] Big Friends: no valid term at currentResult=' + currentResult + ', regenerating exercise');
                    termsArray = [];
                    operations = [];
                    break;
                }
            } else if (isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) {
                // For -all levels (termTypesDistribution empty): natural mix via isAllowedOperation
                // This allows Big Friends formulas to appear naturally alongside small/direct ones
                const currentResult2 = calculateResult(termsArray, operations.slice(0, -1));

                // Switch op if at boundary
                if (op === '+' && currentResult2 >= maxLimit) {
                    op = '-';
                    operations[operations.length - 1] = op;
                } else if (op === '-' && currentResult2 <= 0) {
                    op = '+';
                    operations[operations.length - 1] = op;
                }

                // Collect all valid terms (allowed digit counts), separating formula ops
                const allValidOptions = [];
                const bigOptions = [];
                forEachAllowedTerm(digitsAllowed, maxLimit !== null ? maxLimit : 999, (t) => {
                    const testResult = op === '+' ? currentResult2 + t : currentResult2 - t;
                    if (testResult >= Math.max(1, minInter) && testResult <= maxLimit && isAllowedOperation(currentResult2, op, t, complexity)) {
                        allValidOptions.push(t);
                        if (requiresBigFriendsFormula(currentResult2, op, t % 10)) {
                            bigOptions.push(t);
                        }
                    }
                });

                if (allValidOptions.length > 0) {
                    // Formula-op preference scales with difficulty
                    const formulaBias = difficulty === 'hard' ? 0.9 : difficulty === 'easy' ? 0.3 : 0.7;
                    const pickFrom = (bigOptions.length > 0 && Math.random() < formulaBias) ? bigOptions : allValidOptions;
                    term = pickFrom[Math.floor(Math.random() * pickFrom.length)];
                    validTermFound = true;
                } else {
                    // Try opposite operation
                    const altOp = op === '+' ? '-' : '+';
                    forEachAllowedTerm(digitsAllowed, maxLimit !== null ? maxLimit : 999, (t) => {
                        if (validTermFound) return;
                        const testResult = altOp === '+' ? currentResult2 + t : currentResult2 - t;
                        if (testResult >= Math.max(1, minInter) && testResult <= maxLimit && isAllowedOperation(currentResult2, altOp, t, complexity)) {
                            op = altOp;
                            operations[operations.length - 1] = op;
                            term = t;
                            validTermFound = true;
                        }
                    });
                }
            } else {
                // For other complexity levels, use standard generation
                // Try to avoid excessive repetition
                let standardAttempts = 0;
                while (!validTermFound && standardAttempts < 20) {
                    term = generateNumber(settings, false);

                    // Handle negative numbers
                    if (negative === 'yes' && Math.random() > 0.7) {
                        term = -term;
                    }

                    // Check for excessive repetition
                    if (!shouldAvoidTermRepetition(termsArray, term, terms)) {
                        validTermFound = true;
                    }
                    standardAttempts++;
                }

                // If no valid term found after attempts, use the last generated one anyway
                if (!validTermFound) {
                    validTermFound = true;
                }
            }

            termsArray.push(term);
        }

        // If we didn't generate all terms, try again
        if (termsArray.length < terms) {
            attempt++;
            continue;
        }

        // Calculate final result
        result = calculateResult(termsArray, operations);

        // Ensure result is valid (positive, keeps the minimum digit count, within bounds)
        if (isDirectCalculationLevel(complexity) || isSmallFriendsLevel(complexity) || isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) {
            if (result < Math.max(1, minInter) || result > maxLimit) {
                attempt++;
                if (attempt >= maxAttempts) {
                    // If max attempts reached, return what we have
                    break;
                }
                continue; // Regenerate
            }
        }

        // For Big Friends/Family levels, validate all intermediate results are in [0, maxLimit]
        if (isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) {
            if (!validateIntermediateResults(termsArray, operations, complexity)) {
                attempt++;
                if (attempt >= maxAttempts) { break; }
                continue;
            }
        }

        // Strict multi-digit mode: every intermediate result (and the first term)
        // must keep the minimum selected digit count (e.g. [2] -> never below 10,
        // so 79-72=7 is rejected: the tens column must not collapse)
        if (minInter > 0) {
            let running = termsArray[0];
            let strictOk = running >= minInter;
            for (let k = 0; strictOk && k < operations.length; k++) {
                running = operations[k] === '+' ? running + termsArray[k + 1] : running - termsArray[k + 1];
                if (running < minInter) strictOk = false;
            }
            if (!strictOk) {
                console.log('[generateExerciseTerms] Strict digit mode: intermediate below', minInter, '- regenerating');
                attempt++;
                if (attempt >= maxAttempts) { break; }
                continue;
            }
        }

        // For direct-to-5 complexity, ensure at least one term is 5 (either +5 or -5)
        // This guarantees practice with the heaven bead (5) in every exercise
        // (single-digit only - multi-digit exercises use per-column rules instead)
        if (complexity === 'direct-to-5' && digits === 1) {
            const hasFive = termsArray.some(term => Math.abs(term) === 5);
            if (!hasFive) {
                console.log('[generateExerciseTerms] direct-to-5: No term with value 5, regenerating exercise. Attempt:', attempt + 1, '/', maxAttempts);
                console.log('[generateExerciseTerms] Current terms:', termsArray, 'Result:', result);
                attempt++;
                if (attempt >= maxAttempts) {
                    // If max attempts reached, force add a 5 to make it valid
                    console.warn('[generateExerciseTerms] Max attempts reached! Forcing number 5 into exercise.');
                    // Replace a random term (not the first) with 5
                    if (termsArray.length > 1) {
                        const randomIndex = Math.floor(Math.random() * (termsArray.length - 1)) + 1;
                        const oldTerm = termsArray[randomIndex];
                        termsArray[randomIndex] = 5;
                        console.log('[generateExerciseTerms] Replaced term at index', randomIndex, 'from', oldTerm, 'to 5');
                        // Recalculate result with the forced 5
                        result = calculateResult(termsArray, operations);
                        console.log('[generateExerciseTerms] New result after forcing 5:', result);

                        // CRITICAL: Validate that all intermediate results stay >= 0 (and <= 9 for Small Friends)
                        // Otherwise we could generate invalid exercises with invalid intermediate results
                        if (!validateIntermediateResults(termsArray, operations, complexity)) {
                            console.warn('[generateExerciseTerms] Forcing 5 created invalid intermediate results. Continuing regeneration.');
                            attempt++;
                            continue;
                        }

                        // CRITICAL: Validate no consecutive Big Friends formulas
                        // This prevents confusing situations like 9 + 1 after already using Big Friends
                        if (!validateNoConsecutiveBigFriends(termsArray, operations)) {
                            console.warn('[generateExerciseTerms] Forcing 5 created consecutive Big Friends formulas. Continuing regeneration.');
                            attempt++;
                            continue;
                        }

                        // CRITICAL: Validate that ALL operations are allowed for the current complexity level
                        let allOpsValid = true;
                        for (let i = 0; i < operations.length; i++) {
                            const prevResult = calculateResult(termsArray.slice(0, i + 1), operations.slice(0, i));
                            if (!isAllowedOperation(prevResult, operations[i], termsArray[i + 1], complexity)) {
                                allOpsValid = false;
                                break;
                            }
                        }
                        if (!allOpsValid) {
                            console.warn('[generateExerciseTerms] Forcing 5 created invalid operations for complexity level. Continuing regeneration.');
                            attempt++;
                            continue;
                        }
                    }
                    break;
                }
                continue; // Regenerate
            }
        }

        // For direct-to-9 complexity, ensure sufficient practice with large numbers (6-9)
        // Goal: Dynamic percentage of non-first terms should be 6-9 based on term count
        // 3 terms: 70%, 4 terms: 50%, 5+ terms: 40%
        // Large-numbers requirement: single-digit mixed mode only.
        // In addition-only mode the running result is capped at 9, so large
        // terms are rarely possible; multi-digit exercises use per-column rules.
        // Easy difficulty skips this entirely (6-9 operands are filtered out).
        if (complexity === 'direct-to-9' && digits === 1 && operation !== 'addition' && difficulty !== 'easy') {
            // Check if at least one large number exists
            const hasLargeNumber = termsArray.some(term => Math.abs(term) >= 6 && Math.abs(term) <= 9);

            // MODIFIED: Count large numbers in ALL positions (including first term)
            // Previous version excluded first term, limiting variety
            const largeNumbersCount = termsArray.filter(term => Math.abs(term) >= 6 && Math.abs(term) <= 9).length;
            const largeNumberPercentage = termsArray.length > 0 ? (largeNumbersCount / termsArray.length) : 0;

            // Dynamic target percentage based on term count
            // More terms = lower percentage requirement
            // Hard difficulty demands substantially more 6-9 operands
            let targetPercentage;
            if (difficulty === 'hard') {
                targetPercentage = terms <= 3 ? 0.67 : terms === 4 ? 0.5 : 0.4;
            } else if (terms <= 3) {
                targetPercentage = 0.34; // 34% for 3 terms (~1 large number)
            } else if (terms === 4) {
                targetPercentage = 0.25; // 25% for 4 terms (~1 large number)
            } else {
                targetPercentage = 0.20; // 20% for 5+ terms (~1 large number)
            }

            // Require: at least 1 large number total AND meets dynamic percentage requirement
            const meetsRequirement = hasLargeNumber && largeNumberPercentage >= targetPercentage;

            if (!meetsRequirement) {
                console.log('[generateExerciseTerms] direct-to-9: Insufficient large numbers (6-9). Current: ' +
                    (largeNumberPercentage * 100).toFixed(0) + '% of all terms. Target: >' + (targetPercentage * 100).toFixed(0) + '%. Attempt:',
                    attempt + 1, '/', maxAttempts);
                console.log('[generateExerciseTerms] Current terms:', termsArray, 'Result:', result);
                attempt++;
                if (attempt >= maxAttempts) {
                    // If max attempts reached, try to intelligently add large numbers without violating constraints
                    console.warn('[generateExerciseTerms] Max attempts reached! Attempting to add large numbers (6-9) while respecting constraints.');
                    if (termsArray.length > 1) {
                        // Calculate how many terms we need to replace to reach target percentage
                        const targetCount = Math.ceil(termsArray.length * targetPercentage);
                        const needToAdd = targetCount - largeNumbersCount;

                        console.log('[generateExerciseTerms] Need to add', needToAdd, 'more large numbers to reach', (targetPercentage * 100).toFixed(0) + '% target');

                        // Try to replace terms with large numbers that don't violate constraints
                        let successfulReplacements = 0;
                        const maxReplacementAttempts = needToAdd * 10; // Try harder to find valid replacements
                        let replacementAttempt = 0;

                        while (successfulReplacements < needToAdd && replacementAttempt < maxReplacementAttempts) {
                            replacementAttempt++;

                            // MODIFIED: Pick a random term index (including first term)
                            const randomIndex = Math.floor(Math.random() * termsArray.length);

                            // Skip if this position already has a large number
                            if (Math.abs(termsArray[randomIndex]) >= 6) {
                                continue;
                            }

                            // Try a random large number (6-9)
                            const randomLargeNum = Math.floor(Math.random() * 4) + 6;

                            // Create a test copy to validate the replacement
                            const testTerms = [...termsArray];
                            testTerms[randomIndex] = randomLargeNum;

                            // Calculate what the intermediate result would be at this position
                            const precedingTerms = testTerms.slice(0, randomIndex);
                            const precedingOps = operations.slice(0, randomIndex - 1);
                            const currentResult = calculateResult(precedingTerms, precedingOps);
                            const op = operations[randomIndex - 1];

                            // Validate this replacement doesn't create formula requirements or invalid results
                            const wouldRequireSmallFriends = isSmallFriendsCombination(currentResult, op, randomLargeNum);
                            const wouldRequireBigFriends = isBigFriendsCombination(currentResult, op, randomLargeNum, complexity);
                            const intermediateResult = op === '+' ? currentResult + randomLargeNum : currentResult - randomLargeNum;
                            const intermediateValid = intermediateResult >= 1; // RELAXED: removed <= 9 restriction

                            // Calculate final result with this replacement
                            const testResult = calculateResult(testTerms, operations);
                            const finalResultValid = testResult >= 1 && testResult <= 9;

                            // Validate all intermediate results would still be valid
                            const allIntermediatesValid = validateIntermediateResults(testTerms, operations, complexity);

                            // Validate no consecutive Big Friends formulas
                            const noConsecutiveBigFriends = validateNoConsecutiveBigFriends(testTerms, operations);

                            // Validate that ALL operations in the exercise (not just the replaced one)
                            // are still valid for direct calculation after the replacement.
                            // Replacing a term changes the running total, which can make subsequent
                            // operations require small/big friends formulas.
                            let allOpsStillDirect = true;
                            let runningVal = testTerms[0];
                            for (let k = 0; k < operations.length; k++) {
                                const stepOp = operations[k];
                                const stepTerm = testTerms[k + 1];
                                const isLastStep = (k === operations.length - 1);
                                if (isSmallFriendsCombination(runningVal, stepOp, stepTerm) ||
                                    isBigFriendsCombination(runningVal, stepOp, stepTerm, complexity) ||
                                    !isAllowedOperation(runningVal, stepOp, stepTerm, complexity)) { // R1 (replaces canPerformDirectly)
                                    // !canPerformDirectly(runningVal, stepOp, stepTerm, maxLimit, isLastStep)) { // R1 DISABLED
                                    allOpsStillDirect = false;
                                    break;
                                }
                                runningVal = stepOp === '+' ? runningVal + stepTerm : runningVal - stepTerm;
                            }

                            if (!wouldRequireSmallFriends && !wouldRequireBigFriends &&
                                intermediateValid && finalResultValid && allIntermediatesValid && noConsecutiveBigFriends &&
                                allOpsStillDirect) {
                                // This replacement is valid!
                                const oldTerm = termsArray[randomIndex];
                                termsArray[randomIndex] = randomLargeNum;
                                successfulReplacements++;
                                console.log('[generateExerciseTerms] Replaced term at index', randomIndex, 'from', oldTerm, 'to', randomLargeNum);
                            }
                        }

                        // Recalculate result with the replaced large numbers
                        result = calculateResult(termsArray, operations);
                        console.log('[generateExerciseTerms] After intelligent replacement: added', successfulReplacements, 'large numbers. New result:', result);

                        // If we couldn't add enough large numbers while respecting constraints, continue regenerating
                        if (successfulReplacements < needToAdd) {
                            console.warn('[generateExerciseTerms] Could not add enough large numbers without violating constraints. Continuing regeneration.');
                            attempt++;
                            continue;
                        }

                        // Final validation: ensure result is within 1-9
                        if (result < 1 || result > 9) {
                            console.warn('[generateExerciseTerms] Final result', result, 'is outside valid range [1-9]. Continuing regeneration.');
                            attempt++;
                            continue;
                        }
                    }
                    break;
                }
                continue; // Regenerate
            }
        }

        // For Small Friends complexity, ensure sufficient practice with digit 5
        // MODIFIED: Dynamic percentage of ALL terms should be 5 based on term count
        // This promotes pedagogical exercises like: 4+5-2-5+1 or 3-2+5+2-5
        // Including first term for more variety
        // (single-digit only: multi-digit terms are 2-3 digit numbers, a literal
        // term of 5 is rare and the requirement burns every generation attempt)
        if (isSmallFriendsLevel(complexity) && digits === 1) {
            // Check if at least one term is 5
            const hasFive = termsArray.some(term => Math.abs(term) === 5);

            // MODIFIED: Count digit 5 in ALL positions (including first term)
            const fivesCount = termsArray.filter(term => Math.abs(term) === 5).length;
            const fivePercentage = termsArray.length > 0 ? (fivesCount / termsArray.length) : 0;

            // Dynamic target percentage based on term count (adjusted for all terms)
            let targetPercentage;
            if (terms <= 3) {
                targetPercentage = 0.6; // 60% for 3 terms (was 80% of non-first)
            } else if (terms === 4) {
                targetPercentage = 0.5; // 50% for 4 terms (was 70% of non-first)
            } else if (terms === 5) {
                targetPercentage = 0.4; // 40% for 5 terms (was 60% of non-first)
            } else {
                targetPercentage = 0.3; // 30% for 6+ terms (was 50% of non-first)
            }

            // Require: at least 1 digit 5 total AND meets dynamic percentage requirement
            const meetsRequirement = hasFive && fivePercentage >= targetPercentage;

            if (!meetsRequirement) {
                console.log('[generateExerciseTerms] Small Friends: Insufficient digit 5 usage. Current: ' +
                    (fivePercentage * 100).toFixed(0) + '% of all terms. Target: >=' + (targetPercentage * 100).toFixed(0) + '%. Attempt:',
                    attempt + 1, '/', maxAttempts);
                console.log('[generateExerciseTerms] Current terms:', termsArray, 'Result:', result);
                attempt++;
                if (attempt >= maxAttempts) {
                    // If max attempts reached, try to intelligently add digit 5 without violating constraints
                    console.warn('[generateExerciseTerms] Max attempts reached! Attempting to add digit 5 while respecting Small Friends constraints.');
                    if (termsArray.length > 1) {
                        // Calculate how many terms we need to replace to reach target percentage
                        const targetCount = Math.ceil(termsArray.length * targetPercentage);
                        const needToAdd = targetCount - fivesCount;

                        console.log('[generateExerciseTerms] Need to add', needToAdd, 'more digit 5s to reach', (targetPercentage * 100).toFixed(0) + '% target');

                        // Try to replace terms with 5 that don't violate constraints
                        let successfulReplacements = 0;
                        const maxReplacementAttempts = needToAdd * 10; // Try harder to find valid replacements
                        let replacementAttempt = 0;

                        while (successfulReplacements < needToAdd && replacementAttempt < maxReplacementAttempts) {
                            replacementAttempt++;

                            // MODIFIED: Pick a random term index (including first term)
                            const randomIndex = Math.floor(Math.random() * termsArray.length);

                            // Skip if this position already has a 5
                            if (Math.abs(termsArray[randomIndex]) === 5) {
                                continue;
                            }

                            // Create a test copy to validate the replacement
                            const testTerms = [...termsArray];
                            testTerms[randomIndex] = 5;

                            // Calculate what the intermediate result would be at this position
                            const precedingTerms = testTerms.slice(0, randomIndex);
                            const precedingOps = operations.slice(0, randomIndex - 1);
                            const currentResult = calculateResult(precedingTerms, precedingOps);
                            const op = operations[randomIndex - 1];

                            // For Small Friends, we want to ensure that using 5 is VALID at this position
                            // Check if this would require a Small Friends formula (which is GOOD for Small Friends levels)
                            const intermediateResult = op === '+' ? currentResult + 5 : currentResult - 5;
                            const intermediateValid = intermediateResult >= 1 && intermediateResult <= 9; // Must stay within single-digit range

                            // Calculate final result with this replacement
                            const testResult = calculateResult(testTerms, operations);
                            const finalResultValid = testResult >= 1 && testResult <= 9;

                            // Validate all intermediate results would still be valid
                            const allIntermediatesValid = validateIntermediateResults(testTerms, operations, complexity);

                            // Validate no consecutive Big Friends formulas
                            const noConsecutiveBigFriends = validateNoConsecutiveBigFriends(testTerms, operations);

                            // NEW: Validate that ALL operations are allowed for the current complexity level
                            // This is critical for Small Friends levels to prevent invalid operations
                            let allOperationsAllowed = true;
                            for (let i = 0; i < operations.length; i++) {
                                const prevResult = calculateResult(testTerms.slice(0, i + 1), operations.slice(0, i));
                                const operand = testTerms[i + 1];
                                const operation = operations[i];
                                if (!isAllowedOperation(prevResult, operation, operand, complexity)) {
                                    allOperationsAllowed = false;
                                    break;
                                }
                            }

                            if (intermediateValid && finalResultValid && allIntermediatesValid && noConsecutiveBigFriends && allOperationsAllowed) {
                                // This replacement is valid!
                                const oldTerm = termsArray[randomIndex];
                                termsArray[randomIndex] = 5;
                                successfulReplacements++;
                                console.log('[generateExerciseTerms] Replaced term at index', randomIndex, 'from', oldTerm, 'to 5');
                            }
                        }

                        // Recalculate result with the replaced 5s
                        result = calculateResult(termsArray, operations);
                        console.log('[generateExerciseTerms] After intelligent replacement: added', successfulReplacements, 'digit 5s. New result:', result);

                        // If we couldn't add enough 5s while respecting constraints, continue regenerating
                        if (successfulReplacements < needToAdd) {
                            console.warn('[generateExerciseTerms] Could not add enough digit 5s without violating constraints. Continuing regeneration.');
                            attempt++;
                            continue;
                        }

                        // Final validation: ensure result is within 1-9
                        if (result < 1 || result > 9) {
                            console.warn('[generateExerciseTerms] Final result', result, 'is outside valid range [1-9]. Continuing regeneration.');
                            attempt++;
                            continue;
                        }
                    }
                    break;
                }
                continue; // Regenerate
            }
        }

        // X-X rule: subtracting the same number (result=0) cannot be first or last operation
        if (operations.length > 0) {
            // Check first operation: termsArray[0] - termsArray[1] = 0 is forbidden as first
            if (operations[0] === '-' && termsArray[1] === termsArray[0]) {
                attempt++;
                if (attempt >= maxAttempts) { break; }
                continue;
            }
            // Check last operation: if last op is '-' and last term equals intermediate result
            const lastOpIdx = operations.length - 1;
            if (operations[lastOpIdx] === '-') {
                const secondToLastResult = calculateResult(termsArray.slice(0, -1), operations.slice(0, -1));
                if (secondToLastResult === termsArray[termsArray.length - 1]) {
                    attempt++;
                    if (attempt >= maxAttempts) { break; }
                    continue;
                }
            }
        }

        // NEW VALIDATION: For Small Friends levels, verify actual formula usage matches distribution
        // This ensures exercises actually practice the target formula, not just use digit 5
        if (isSmallFriendsLevel(complexity) && termTypesDistribution && termTypesDistribution.length > 0) {
            // Count how many terms were allocated as 'current' formula in the distribution
            // ('current' for single-digit, 'small-current' for multi-digit exercises)
            const intendedFormulaCount = termTypesDistribution.filter(t => t.type === 'current' || t.type === 'small-current').length;

            // Count how many operations actually require the Small Friends formula
            let actualFormulaCount = 0;
            for (let i = 0; i < operations.length; i++) {
                const currentResult = calculateResult(termsArray.slice(0, i + 1), operations.slice(0, i));
                const term = termsArray[i + 1];
                const op = operations[i];

                if (requiresSmallFriendsFormula(currentResult, op, term)) {
                    actualFormulaCount++;
                }
            }

            // Calculate actual formula percentage vs intended
            const actualFormulaPercentage = operations.length > 0 ? actualFormulaCount / operations.length : 0;
            const intendedFormulaPercentage = termTypesDistribution.length > 0 ? intendedFormulaCount / termTypesDistribution.length : 0;

            // CRITICAL: Require at least 80% of intended formulas to be actually used
            // This prevents exercises where distribution says "use formula" but generation falls back to direct
            const minRequiredFormulaPercentage = intendedFormulaPercentage * 0.8;

            if (actualFormulaPercentage < minRequiredFormulaPercentage) {
                console.log('[generateExerciseTerms] Small Friends: Insufficient formula usage. Intended:',
                    intendedFormulaCount, '('+( intendedFormulaPercentage * 100).toFixed(0)+'%)',
                    'Actual:', actualFormulaCount, '('+(actualFormulaPercentage * 100).toFixed(0)+'%)',
                    'Required:', (minRequiredFormulaPercentage * 100).toFixed(0)+'%',
                    'Attempt:', attempt + 1, '/', maxAttempts);
                console.log('[generateExerciseTerms] Terms:', termsArray, 'Operations:', operations);
                attempt++;
                if (attempt >= maxAttempts) {
                    console.warn('[generateExerciseTerms] Max attempts reached, returning exercise with insufficient formula usage');
                    break;
                }
                continue; // Regenerate
            }

            console.log('[generateExerciseTerms] Formula usage validation passed:', {
                intendedCount: intendedFormulaCount,
                actualCount: actualFormulaCount,
                percentage: (actualFormulaPercentage * 100).toFixed(0) + '%',
                required: (minRequiredFormulaPercentage * 100).toFixed(0) + '%'
            });

            // Additionally: the CURRENT formula itself must appear (not just any
            // small friends op) - e.g. small-minus-1 must contain an actual 5-1
            const specificMatch = complexity.match(/^small-(plus|minus)-(\d)$/);
            if (specificMatch && intendedFormulaCount > 0) {
                const fOp = specificMatch[1] === 'plus' ? '+' : '-';
                const fN = parseInt(specificMatch[2]);
                let actualCurrentCount = 0;
                for (let i = 0; i < operations.length; i++) {
                    const cr = calculateResult(termsArray.slice(0, i + 1), operations.slice(0, i));
                    const t = termsArray[i + 1];
                    if (operations[i] === fOp && Math.abs(t) % 10 === fN &&
                        requiresSmallFriendsFormula(cr, fOp, fN)) {
                        actualCurrentCount++;
                    }
                }
                if (actualCurrentCount < 1) {
                    console.log('[generateExerciseTerms] Small Friends: current formula', fOp + fN, 'not present. Attempt:', attempt + 1);
                    attempt++;
                    if (attempt >= maxAttempts) { break; }
                    continue;
                }
            }
        }

        // VALIDATION: For Big Friends levels, verify the CURRENT formula is actually used
        if ((isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) && termTypesDistribution && termTypesDistribution.length > 0) {
            const currentSlots = termTypesDistribution.filter(t => t.type === 'big-current');
            const intendedBigCount = currentSlots.length;
            if (intendedBigCount > 0) {
                const fN = currentSlots[0].formulaN;
                const fOp = currentSlots[0].formulaType === 'plus' ? '+' : '-';
                const fIsFamily = !!currentSlots[0].isFamily;

                let actualCurrentCount = 0;
                for (let i = 0; i < operations.length; i++) {
                    const curResult = calculateResult(termsArray.slice(0, i + 1), operations.slice(0, i));
                    const t = termsArray[i + 1];
                    const o = operations[i];
                    // Multi-digit terms count if their UNITS digit applies the formula
                    // (e.g. +51 at units 9 exercises formula +1 on the units column)
                    const tUnits = Math.abs(t) % 10;
                    if (o === fOp && tUnits === fN && requiresBigFriendsFormula(curResult, o, tUnits)) {
                        const isFam = requiresFamilyFormula(curResult, o, tUnits);
                        if (fIsFamily ? isFam : !isFam) {
                            actualCurrentCount++;
                        }
                    }
                }
                // Require at least 70% of the intended (alternating) formula slots
                const minRequired = Math.max(1, Math.ceil(intendedBigCount * 0.7));

                if (actualCurrentCount < minRequired) {
                    console.log('[generateExerciseTerms] Big Friends: Insufficient CURRENT formula usage.',
                        'Intended:', intendedBigCount, 'Actual:', actualCurrentCount,
                        'MinRequired:', minRequired,
                        'Attempt:', attempt + 1);
                    attempt++;
                    if (attempt >= maxAttempts) { break; }
                    continue;
                }
            }
        }

        // Final validation: Check for consecutive Big Friends formulas
        // SKIPPED for Big Friends / Family levels: consecutive carry formulas ARE
        // the training goal there (e.g. 8+2, 10-1, 9+4 back-to-back is correct)
        // SKIPPED for multi-digit exercises: requiresCarryingFormula treats any
        // result >= 10 as a carry, which is normal for 2-3 digit numbers; real
        // carries are already forbidden per-column by isAllowedOperation
        if (digits === 1 &&
            !(isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) &&
            !validateNoConsecutiveBigFriends(termsArray, operations)) {
            console.warn('[generateExerciseTerms] Exercise has consecutive Big Friends formulas. Regenerating. Attempt:', attempt + 1, '/', maxAttempts);
            console.log('[generateExerciseTerms] Current terms:', termsArray, 'Operations:', operations);
            attempt++;
            if (attempt >= maxAttempts) {
                // If max attempts reached, continue to return the exercise anyway
                console.warn('[generateExerciseTerms] Max attempts reached, returning exercise with consecutive Big Friends anyway');
                break;
            }
            continue; // Regenerate
        }

        // Valid result found
        console.log('[generateExerciseTerms] Generated valid exercise:', { termsCount: termsArray.length, terms: termsArray, operations });
        return { terms: termsArray, operations: operations };

    } while ((isDirectCalculationLevel(complexity) || isSmallFriendsLevel(complexity) || isBigFriendsLevel(complexity) || isFamilyLevel(complexity)) && attempt < maxAttempts);

    // Fallback: return last generated result even if not perfect
    console.log('[generateExerciseTerms] Returning fallback exercise:', { termsCount: termsArray.length, terms: termsArray, operations });
    return { terms: termsArray, operations: operations };
}
