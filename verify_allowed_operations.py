#!/usr/bin/env python3
"""
Script pentru verificarea operațiilor permise în Calcul Direct (direct-to-9)
Extrage toate operațiile din tabelele de directă și le afișează organizat.
"""

# Tabele de operații din cod (anzan_simulator.html)
directTo4 = {
    '+': [[1,1],[1,2],[1,3],[2,1],[2,2],[3,1]],
    '-': [[1,1],[2,1],[2,2],[3,1],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4]]
}

directTo5New = {
    '+': [[1,5],[2,5],[3,5],[4,5]],
    '-': [[6,1],[6,5],[7,1],[7,2],[7,5],[8,1],[8,2],[8,3],[8,5],[9,1],[9,2],[9,3],[9,4],[9,5]]
}

directTo9New = {
    '+': [
        [1,6],[1,7],[1,8],  # 1+6=7, 1+7=8, 1+8=9
        [2,6],[2,7],        # 2+6=8, 2+7=9
        [3,6],              # 3+6=9
        [4,5]               # 4+5=9
    ],
    '-': [
        [6,1],[6,5],[6,6],                          # 6-1=5, 6-5=1, 6-6=0
        [7,1],[7,2],[7,5],[7,6],[7,7],              # 7-1=6, 7-2=5, 7-5=2, 7-6=1, 7-7=0
        [8,1],[8,2],[8,3],[8,5],[8,6],[8,7],[8,8],  # 8-1=7, 8-2=6, 8-3=5, 8-5=3, 8-6=2, 8-7=1, 8-8=0
        [9,1],[9,2],[9,3],[9,4],[9,5],[9,6],[9,7],[9,8],[9,9]  # All subtractions from 9
    ]
}

def combine_all_operations():
    """Combină toate operațiile din cele trei tabele (pentru direct-to-9)"""
    combined = {'+': [], '-': []}

    # Adună operațiile din toate tabelele
    for op in ['+', '-']:
        combined[op].extend(directTo4.get(op, []))
        combined[op].extend(directTo5New.get(op, []))
        combined[op].extend(directTo9New.get(op, []))

    # Elimină duplicatele
    combined['+'] = list(set(map(tuple, combined['+'])))
    combined['-'] = list(set(map(tuple, combined['-'])))

    return combined

def get_operations_for_value(value, all_operations):
    """Returnează toate operațiile permise pentru o valoare dată"""
    operations = []

    # Adunări
    for current_val, operand in all_operations['+']:
        if current_val == value:
            operations.append(f'+{operand}')

    # Scăderi
    for current_val, operand in all_operations['-']:
        if current_val == value:
            operations.append(f'-{operand}')

    return sorted(operations, key=lambda x: (x[0], int(x[1:])))

def print_operations_table():
    """Afișează tabelul complet de operații permise pentru fiecare cifră"""
    all_ops = combine_all_operations()

    print("=" * 60)
    print("OPERAȚII PERMISE ÎN CALCUL DIRECT (direct-to-9)")
    print("=" * 60)
    print()

    for value in range(1, 10):
        ops = get_operations_for_value(value, all_ops)
        ops_str = ' '.join(ops) if ops else '(nicio operație)'
        print(f"+{value} : {ops_str}")

    print()
    print("=" * 60)

def verify_user_list():
    """Verifică lista furnizată de utilizator cu cea din cod"""
    user_operations = {
        1: ['+2', '+3', '+5', '+6', '+7', '+8'],
        2: ['+1', '+5', '+6', '+7', '-1'],
        3: ['+1', '+5', '+6', '-1', '-2'],
        4: ['+5', '-1', '-2', '-3'],
        5: ['+1', '+2', '+3', '+4'],
        6: ['+1', '+2', '+3', '-1', '-5'],
        7: ['+1', '+2', '-1', '-2', '-5', '-6'],
        8: ['+1', '-1', '-2', '-3', '-5', '-6', '-7'],
        9: ['-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8']
    }

    all_ops = combine_all_operations()

    print()
    print("=" * 60)
    print("VERIFICARE: COMPARAȚIE CU LISTA UTILIZATORULUI")
    print("=" * 60)
    print()

    all_match = True

    for value in range(1, 10):
        code_ops = set(get_operations_for_value(value, all_ops))
        user_ops = set(user_operations[value])

        if code_ops == user_ops:
            print(f"✅ +{value}: CORECT - {len(code_ops)} operații")
        else:
            all_match = False
            print(f"❌ +{value}: DIFERENȚĂ DETECTATĂ!")

            missing_in_code = user_ops - code_ops
            if missing_in_code:
                print(f"   În lista user, dar NU în cod: {sorted(missing_in_code)}")

            extra_in_code = code_ops - user_ops
            if extra_in_code:
                print(f"   În cod, dar NU în lista user: {sorted(extra_in_code)}")

            print(f"   COD: {sorted(code_ops)}")
            print(f"   USER: {sorted(user_ops)}")

    print()
    if all_match:
        print("🎉 TOATE OPERAȚIILE SUNT CORECTE!")
    else:
        print("⚠️  AU FOST DETECTATE DIFERENȚE!")
    print("=" * 60)

if __name__ == '__main__':
    print_operations_table()
    verify_user_list()
