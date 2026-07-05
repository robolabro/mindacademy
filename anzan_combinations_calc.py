#!/usr/bin/env python3
"""
Calculator pentru combinații de exerciții Anzan
Calculează numărul de combinații posibile pentru diferite setări
"""

def calculate_combinations(complexity, terms_count):
    """
    Calculează numărul estimat de combinații pentru o anumită complexitate și număr de termeni
    """

    # Definim numerele disponibile pentru fiecare complexitate (pentru 1 cifră)
    available_numbers = {
        'direct-to-4': [1, 2, 3, 4],  # 4 cifre
        'direct-to-5': [1, 2, 3, 4, 5],  # 5 cifre
        'direct-to-9': [1, 2, 3, 4, 5, 6, 7, 8, 9],  # 9 cifre
        'direct-counting': [1, 2, 3, 4, 5, 6, 7, 8, 9],  # 9 cifre
        'small-plus-1': [1, 2, 3, 4, 5, 6, 7, 8, 9],  # 9 cifre (cu constrângeri specifice)
        'small-plus-2': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'small-plus-3': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'small-plus-4': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'small-minus-1': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'small-minus-2': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'small-minus-3': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'small-minus-4': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'small-friends-all': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-1': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-2': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-3': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-4': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-5': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-6': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-7': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-8': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-plus-9': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-1': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-2': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-3': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-4': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-5': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-6': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-7': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-8': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-minus-9': [1, 2, 3, 4, 5, 6, 7, 8, 9],
        'big-friends-all': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    }

    # Operații disponibile: + și - (pentru operație mixed)
    operations = ['+', '-']

    nums = available_numbers[complexity]
    num_count = len(nums)
    op_count = len(operations)

    # Formula de bază pentru combinații (fără constrângeri):
    # Primul termen: num_count opțiuni
    # Pentru fiecare termen suplimentar: num_count opțiuni × op_count operații
    # Total = num_count × (num_count × op_count)^(terms_count - 1)

    base_combinations = num_count * ((num_count * op_count) ** (terms_count - 1))

    # Factor de reducere pentru constrângeri (estimat)
    # Constrângeri includ:
    # - Evitarea duplicatelor
    # - Evitarea pattern-urilor similare
    # - Validări pentru rezultate negative
    # - Pentru prieteni mici/mari: cerințe specifice de utilizare a formulelor

    if 'small' in complexity or 'big' in complexity:
        # Pentru prieteni mici/mari, există mai multe constrângeri
        reduction_factor = 0.6  # ~60% din combinații sunt valide
    else:
        # Pentru calcul direct, mai puține constrângeri
        reduction_factor = 0.8  # ~80% din combinații sunt valide

    estimated_valid = int(base_combinations * reduction_factor)

    return {
        'theoretical': base_combinations,
        'estimated_valid': estimated_valid,
        'reduction_factor': reduction_factor
    }

def main():
    print("=" * 80)
    print("CALCULATOR COMBINAȚII EXERCIȚII ANZAN")
    print("=" * 80)
    print()

    complexities = [
        'direct-to-4',
        'direct-to-5',
        'direct-to-9',
        'direct-counting',
        'small-plus-1',
        'small-plus-2',
        'small-plus-3',
        'small-plus-4',
        'small-friends-all',
        'big-plus-1',
        'big-friends-all',
    ]

    terms_counts = [3, 4, 5]

    for complexity in complexities:
        print(f"\n{'='*80}")
        print(f"Complexitate: {complexity.upper()}")
        print(f"{'='*80}")

        for terms in terms_counts:
            result = calculate_combinations(complexity, terms)
            print(f"\n{terms} termeni:")
            print(f"  - Combinații teoretice: {result['theoretical']:,}")
            print(f"  - Combinații valide estimate: {result['estimated_valid']:,}")
            print(f"  - Factor de reducere: {result['reduction_factor']:.0%}")

    print("\n" + "=" * 80)
    print("NOTE:")
    print("  - Combinațiile teoretice = toate combinațiile posibile fără constrângeri")
    print("  - Combinațiile valide = estimate după aplicarea constrângerilor din cod")
    print("  - Pentru operație 'Amestecat', se folosesc atât + cât și -")
    print("  - Pentru operație 'Adunare', doar +, deci combinațiile sunt ~50% mai puține")
    print("=" * 80)

if __name__ == "__main__":
    main()
