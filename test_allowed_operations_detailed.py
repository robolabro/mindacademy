#!/usr/bin/env python3
"""
Script detaliat pentru verificarea operațiilor permise și interzise în Calcul Direct
Testează atât operațiile permise cât și cele interzise (Prietenii mici)
"""

# Tabele de operații din cod (actualizate 2026-02-22)
directTo4 = {
    '+': [[1,1],[1,2],[1,3],[2,1],[2,2],[3,1]],
    '-': [[1,1],[2,1],[2,2],[3,1],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4]]
}

directTo5New = {
    '+': [[1,5],[2,5],[3,5],[4,5],[5,1],[5,2],[5,3],[5,4]],  # Include operațiile inverse cu 5
    '-': [[5,5],[6,1],[6,5],[7,1],[7,2],[7,5],[8,1],[8,2],[8,3],[8,5],[9,1],[9,2],[9,3],[9,4],[9,5]]  # Include 5-5
}

directTo9New = {
    '+': [
        [1,6],[1,7],[1,8],  # 1+6=7, 1+7=8, 1+8=9
        [2,6],[2,7],        # 2+6=8, 2+7=9
        [3,6],              # 3+6=9
        [6,1],[6,2],[6,3],  # Operațiile inverse: 6+1=7, 6+2=8, 6+3=9
        [7,1],[7,2],        # 7+1=8, 7+2=9
        [8,1]               # 8+1=9
    ],
    '-': [
        [6,6],                          # 6-6=0
        [7,6],[7,7],                    # 7-6=1, 7-7=0
        [8,6],[8,7],[8,8],              # 8-6=2, 8-7=1, 8-8=0
        [9,6],[9,7],[9,8],[9,9]         # 9-6=3, 9-7=2, 9-8=1, 9-9=0
    ]
}

# Operații INTERZISE (Prietenii mici)
forbidden_operations = {
    'additions': [
        [1,4], [2,3], [2,4], [3,2], [3,4], [4,1], [4,2], [4,3], [4,4]
    ],
    'subtractions': [
        [5,1], [5,2], [5,3], [5,4],
        [6,2], [6,3], [6,4],
        [7,3], [7,4],
        [8,4]
    ]
}

def combine_all_operations():
    """Combină toate operațiile din cele trei tabele (pentru direct-to-9)"""
    combined = {'+': [], '-': []}

    for op in ['+', '-']:
        combined[op].extend(directTo4.get(op, []))
        combined[op].extend(directTo5New.get(op, []))
        combined[op].extend(directTo9New.get(op, []))

    # Convertește la set pentru a elimina duplicatele
    combined['+'] = list(set(map(tuple, combined['+'])))
    combined['-'] = list(set(map(tuple, combined['-'])))

    return combined

def is_operation_allowed(current_value, operand, operation, all_operations):
    """Verifică dacă o operație este permisă"""
    ops = all_operations[operation]
    return (current_value, operand) in ops

def test_forbidden_operations():
    """Testează că operațiile interzise NU sunt permise"""
    all_ops = combine_all_operations()

    print("=" * 80)
    print("TEST: OPERAȚII INTERZISE (Prietenii mici)")
    print("=" * 80)
    print()

    all_correct = True

    # Test adunări interzise
    print("ADUNĂRI INTERZISE (trebuie să NU fie permise):")
    print("-" * 80)
    for current_val, operand in forbidden_operations['additions']:
        is_allowed = is_operation_allowed(current_val, operand, '+', all_ops)
        result = current_val + operand
        status = "❌ EROARE: PERMIS" if is_allowed else "✅ CORECT: INTERZIS"
        if is_allowed:
            all_correct = False
        print(f"{status}: {current_val}+{operand}={result}")

    print()

    # Test scăderi interzise
    print("SCĂDERI INTERZISE (trebuie să NU fie permise):")
    print("-" * 80)
    for current_val, operand in forbidden_operations['subtractions']:
        is_allowed = is_operation_allowed(current_val, operand, '-', all_ops)
        result = current_val - operand
        status = "❌ EROARE: PERMIS" if is_allowed else "✅ CORECT: INTERZIS"
        if is_allowed:
            all_correct = False
        print(f"{status}: {current_val}-{operand}={result}")

    print()
    print("=" * 80)
    if all_correct:
        print("🎉 TOATE OPERAȚIILE INTERZISE SUNT CORECT BLOCATE!")
    else:
        print("⚠️  ATENȚIE: UNELE OPERAȚII INTERZISE SUNT PERMISE ERONAT!")
    print("=" * 80)
    print()

def test_specific_operations():
    """Testează operații specifice menționate de utilizator"""
    all_ops = combine_all_operations()

    print("=" * 80)
    print("TEST: OPERAȚII SPECIFICE MENȚIONATE")
    print("=" * 80)
    print()

    # Operații care TREBUIE să fie permise
    must_be_allowed = [
        (1, 1, '+'), (2, 2, '+'),  # Operații cu sine (adunări)
        (1, 5, '+'), (2, 5, '+'), (3, 5, '+'), (4, 5, '+'),  # Adunări cu 5
        (5, 1, '+'), (5, 2, '+'), (5, 3, '+'), (5, 4, '+'),  # Operații inverse cu 5
        (1, 6, '+'), (1, 7, '+'), (1, 8, '+'),  # Adunări cu 6-8
        (2, 6, '+'), (2, 7, '+'),  # 2 cu 6-7
        (3, 6, '+'),  # 3 cu 6
        (6, 1, '+'), (6, 2, '+'), (6, 3, '+'),  # Operații inverse cu 6
        (7, 1, '+'), (7, 2, '+'),  # Operații inverse cu 7
        (8, 1, '+'),  # Operații inverse cu 8
        (5, 5, '-'),  # 5-5 trebuie permis
        (6, 1, '-'), (7, 1, '-'), (7, 2, '-'),  # Scăderi mici
        (8, 1, '-'), (8, 2, '-'), (8, 3, '-'),  # Scăderi mici
        (9, 1, '-'), (9, 2, '-'), (9, 3, '-'), (9, 4, '-'),  # Scăderi mici
        (6, 6, '-'), (7, 7, '-'), (8, 8, '-'), (9, 9, '-'),  # Operații cu sine (scăderi mari)
        (1, 1, '-'), (2, 2, '-'),  # 1-1, 2-2 permise la calcul direct cu 4
    ]

    print("OPERAȚII CARE TREBUIE SĂ FIE PERMISE:")
    print("-" * 80)
    all_correct = True
    for current_val, operand, operation in must_be_allowed:
        is_allowed = is_operation_allowed(current_val, operand, operation, all_ops)
        if operation == '+':
            result = current_val + operand
        else:
            result = current_val - operand
        status = "✅ CORECT" if is_allowed else "❌ EROARE: INTERZIS"
        if not is_allowed:
            all_correct = False
        print(f"{status}: {current_val}{operation}{operand}={result}")

    print()
    print("=" * 80)
    if all_correct:
        print("🎉 TOATE OPERAȚIILE SPECIFICE SUNT CORECT PERMISE!")
    else:
        print("⚠️  ATENȚIE: UNELE OPERAȚII NECESARE SUNT INTERZISE ERONAT!")
    print("=" * 80)
    print()

def print_summary():
    """Afișează un sumar al tuturor operațiilor"""
    all_ops = combine_all_operations()

    print("=" * 80)
    print("SUMAR: TOTAL OPERAȚII PERMISE")
    print("=" * 80)
    print()

    total_additions = len(all_ops['+'])
    total_subtractions = len(all_ops['-'])
    total = total_additions + total_subtractions

    print(f"Total adunări permise: {total_additions}")
    print(f"Total scăderi permise: {total_subtractions}")
    print(f"TOTAL OPERAȚII: {total}")
    print()

    print("Breakdown pe nivel:")
    print("-" * 80)
    print(f"Direct-to-4: {len(directTo4['+'])} adunări + {len(directTo4['-'])} scăderi = {len(directTo4['+']) + len(directTo4['-'])} operații")
    print(f"Direct-to-5 NEW: {len(directTo5New['+'])} adunări + {len(directTo5New['-'])} scăderi = {len(directTo5New['+']) + len(directTo5New['-'])} operații noi")
    print(f"Direct-to-9 NEW: {len(directTo9New['+'])} adunări + {len(directTo9New['-'])} scăderi = {len(directTo9New['+']) + len(directTo9New['-'])} operații noi")
    print()
    print("=" * 80)
    print()

if __name__ == '__main__':
    print_summary()
    test_specific_operations()
    test_forbidden_operations()
