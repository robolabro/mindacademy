#!/usr/bin/env python3
"""
Anzan Formula Automated Testing Tool

This script generates exercises for all Anzan formulas and produces a detailed report
that can be manually reviewed to verify correctness of calculations.
"""

import random
import json
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from enum import Enum


class FormulaType(Enum):
    """Types of Anzan formulas"""
    SMALL_FRIENDS_PLUS = "small_friends_plus"
    SMALL_FRIENDS_MINUS = "small_friends_minus"
    BIG_FRIENDS_PLUS = "big_friends_plus"
    BIG_FRIENDS_MINUS = "big_friends_minus"
    DIRECT = "direct"


class Formula:
    """Represents an Anzan formula"""

    def __init__(self, formula_type: FormulaType, number: int, description: str):
        self.type = formula_type
        self.number = number
        self.description = description

    def __str__(self):
        return self.description

    def __repr__(self):
        return f"Formula({self.type.value}, {self.number}, '{self.description}')"


# Define all formulas
SMALL_FRIENDS_PLUS = [
    Formula(FormulaType.SMALL_FRIENDS_PLUS, 1, "+1 = +5 - 4"),
    Formula(FormulaType.SMALL_FRIENDS_PLUS, 2, "+2 = +5 - 3"),
    Formula(FormulaType.SMALL_FRIENDS_PLUS, 3, "+3 = +5 - 2"),
    Formula(FormulaType.SMALL_FRIENDS_PLUS, 4, "+4 = +5 - 1"),
]

SMALL_FRIENDS_MINUS = [
    Formula(FormulaType.SMALL_FRIENDS_MINUS, 1, "-1 = -5 + 4"),
    Formula(FormulaType.SMALL_FRIENDS_MINUS, 2, "-2 = -5 + 3"),
    Formula(FormulaType.SMALL_FRIENDS_MINUS, 3, "-3 = -5 + 2"),
    Formula(FormulaType.SMALL_FRIENDS_MINUS, 4, "-4 = -5 + 1"),
]

BIG_FRIENDS_PLUS = [
    Formula(FormulaType.BIG_FRIENDS_PLUS, i, f"+{i} = +10 - {10-i}")
    for i in range(1, 10)
]

BIG_FRIENDS_MINUS = [
    Formula(FormulaType.BIG_FRIENDS_MINUS, i, f"-{i} = -10 + {10-i}")
    for i in range(1, 10)
]


class Exercise:
    """Represents a generated exercise"""

    def __init__(self, terms: List[int], operations: List[str], complexity: str):
        self.terms = terms
        self.operations = operations
        self.complexity = complexity
        self.steps = []
        self.formulas_used = []
        self.correct_answer = self._calculate_result()
        self._analyze_steps()

    def _calculate_result(self) -> int:
        """Calculate the correct answer"""
        result = self.terms[0]
        for i, op in enumerate(self.operations):
            if op == '+':
                result += self.terms[i + 1]
            else:
                result -= self.terms[i + 1]
        return result

    def _requires_small_friends(self, current: int, number: int, operation: str) -> bool:
        """Check if operation requires Small Friends formula"""
        if operation == '+':
            # Need Small Friends if adding from 1-4 to reach 5-9
            # Formula is needed when transitioning from lower beads (1-4) to heaven bead region (5-9)
            # Example: 4+1=5 requires +1 = +5-4 (move heaven up, remove all 4 lower beads)
            current_ones = current % 10
            if 1 <= number <= 4:
                result_ones = (current_ones + number) % 10
                return current_ones >= 1 and current_ones <= 4 and result_ones >= 5 and result_ones <= 9
        else:  # operation == '-'
            current_ones = current % 10
            if 1 <= number <= 4:
                # Small Friends Minus is used when:
                # - current has heaven bead (current_ones >= 5)
                # - result won't have heaven bead (current_ones - number < 5)
                # Example: 7-3=4 (current_ones=7 >= 5, result=4 < 5, so 3 > 7-5=2)
                return current_ones >= 5 and number > (current_ones - 5)
        return False

    def _requires_big_friends(self, current: int, number: int, operation: str) -> bool:
        """Check if operation requires Big Friends formula"""
        current_ones = current % 10
        if operation == '+':
            # Need Big Friends if adding would exceed 9
            return current_ones + number > 9
        else:  # operation == '-'
            # Need Big Friends if subtracting would go negative
            return number > current_ones

    def _can_perform_directly(self, current: int, number: int, operation: str) -> bool:
        """Check if operation can be performed directly"""
        current_ones = current % 10
        if operation == '+':
            return current_ones + number <= 9
        else:  # operation == '-'
            return current_ones >= number

    def _identify_formula(self, current: int, number: int, operation: str) -> Optional[Formula]:
        """Identify which formula should be used for this operation"""
        # Check Small Friends first (for 1-4)
        if 1 <= number <= 4:
            if self._requires_small_friends(current, number, operation):
                if operation == '+':
                    return next((f for f in SMALL_FRIENDS_PLUS if f.number == number), None)
                else:
                    return next((f for f in SMALL_FRIENDS_MINUS if f.number == number), None)

        # Check Big Friends (for 1-9)
        if 1 <= number <= 9:
            if self._requires_big_friends(current, number, operation):
                if operation == '+':
                    return next((f for f in BIG_FRIENDS_PLUS if f.number == number), None)
                else:
                    return next((f for f in BIG_FRIENDS_MINUS if f.number == number), None)

        # Direct calculation
        if self._can_perform_directly(current, number, operation):
            return Formula(FormulaType.DIRECT, number, f"Direct {operation}{number}")

        return None

    def _analyze_steps(self):
        """Analyze each step and identify formulas used"""
        current = self.terms[0]
        self.steps.append({
            'step': 0,
            'operation': 'START',
            'value': self.terms[0],
            'current': current,
            'formula': None,
            'description': f"Start with {self.terms[0]}"
        })

        for i, op in enumerate(self.operations):
            number = self.terms[i + 1]
            formula = self._identify_formula(current, number, operation=op)

            if op == '+':
                current += number
            else:
                current -= number

            self.steps.append({
                'step': i + 1,
                'operation': f"{op}{number}",
                'value': number,
                'current': current,
                'formula': formula,
                'description': f"{op}{number} → {current}" + (f" (using {formula})" if formula else "")
            })

            if formula:
                self.formulas_used.append(formula)

    def get_expression(self) -> str:
        """Get the full expression as string"""
        expr = str(self.terms[0])
        for i, op in enumerate(self.operations):
            expr += f" {op} {self.terms[i + 1]}"
        return expr

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'expression': self.get_expression(),
            'terms': self.terms,
            'operations': self.operations,
            'complexity': self.complexity,
            'correct_answer': self.correct_answer,
            'steps': [{
                'step': s['step'],
                'operation': s['operation'],
                'value': s['value'] if s['step'] > 0 else None,
                'current': s['current'],
                'formula': str(s['formula']) if s['formula'] else None,
                'formula_type': s['formula'].type.value if s['formula'] else None,
                'description': s['description']
            } for s in self.steps],
            'formulas_used': [str(f) for f in self.formulas_used],
            'formula_types': [f.type.value for f in self.formulas_used]
        }


class AnzanFormulaTest:
    """Main test class for Anzan formulas"""

    def __init__(self, exercises_per_formula: int = 10):
        self.exercises_per_formula = exercises_per_formula
        self.results = []

    def generate_number_for_small_friends(self, formula: Formula,
                                         current: int, operation: str) -> Optional[int]:
        """Generate a number that requires the specific Small Friends formula"""
        current_ones = current % 10
        number = formula.number

        if operation == '+':
            # For Small Friends Plus, we need:
            # - current_ones in range 1-4 (heaven bead not used)
            # - current_ones + number in range 5-9 (transition to heaven bead)
            # Example: 4+1=5, 3+2=5, 2+3=5, 1+4=5
            result_ones = current_ones + number
            if current_ones < 1 or current_ones > 4 or result_ones < 5 or result_ones > 9:
                return None
            return number
        else:  # operation == '-'
            # For Small Friends Minus, we need:
            # - current_ones >= 5 (heaven bead is present)
            # - number > (current_ones - 5) (result < 5, no heaven bead)
            # Example: 5-1=4, 6-2=4, 7-3=4, 8-4=4
            if current_ones < 5 or number <= (current_ones - 5):
                return None
            return number

    def generate_number_for_big_friends(self, formula: Formula,
                                       current: int, operation: str) -> Optional[int]:
        """Generate a number that requires the specific Big Friends formula"""
        current_ones = current % 10
        number = formula.number

        if operation == '+':
            # For Big Friends Plus: current_ones + number > 9
            if current_ones + number <= 9:
                return None
            return number
        else:  # operation == '-'
            # For Big Friends Minus: number > current_ones
            if number <= current_ones:
                return None
            return number

    def generate_starting_position(self, formula: Formula, operation: str) -> int:
        """Generate appropriate starting position for formula"""
        if formula.type == FormulaType.SMALL_FRIENDS_PLUS:
            # Need ones place in 1-4 and + number gives result in 5-9
            # For +1: ones can be 4 (4+1=5)
            # For +2: ones can be 3 or 4 (3+2=5, 4+2=6)
            # For +3: ones can be 2, 3, or 4 (2+3=5, 3+3=6, 4+3=7)
            # For +4: ones can be 1, 2, 3, or 4 (1+4=5, 2+4=6, 3+4=7, 4+4=8)
            # So: min_ones = max(1, 5 - formula.number)
            #     max_ones = min(4, 9 - formula.number)
            min_ones = max(1, 5 - formula.number)
            max_ones = min(4, 9 - formula.number)
            ones = random.randint(min_ones, max_ones)
            tens = random.randint(0, 8)
            return tens * 10 + ones

        elif formula.type == FormulaType.SMALL_FRIENDS_MINUS:
            # Need ones place >= 5 and - number requires Small Friends
            # For -1: ones must be 5 (5-1=4, uses -5+4)
            # For -2: ones must be 5 or 6 (5-2=3, 6-2=4)
            # For -3: ones must be 5, 6, or 7 (5-3=2, 6-3=3, 7-3=4)
            # For -4: ones must be 5, 6, 7, or 8 (5-4=1, 6-4=2, 7-4=3, 8-4=4)
            min_ones = 5
            max_ones = min(9, 4 + formula.number)
            ones = random.randint(min_ones, max_ones)
            tens = random.randint(1, 9)  # At least 10 to allow subtraction
            return tens * 10 + ones

        elif formula.type == FormulaType.BIG_FRIENDS_PLUS:
            # Need ones + formula.number > 9
            min_ones = max(1, 10 - formula.number)
            max_ones = 9
            ones = random.randint(min_ones, max_ones)
            tens = random.randint(0, 8)  # Leave room for +10
            return tens * 10 + ones

        elif formula.type == FormulaType.BIG_FRIENDS_MINUS:
            # Need ones < formula.number (can't subtract directly)
            max_ones = min(8, formula.number - 1)
            min_ones = 0
            ones = random.randint(min_ones, max_ones)
            tens = random.randint(1, 9)  # At least 10 to allow -10
            return tens * 10 + ones

        # Default: random number 10-90
        return random.randint(1, 9) * 10 + random.randint(0, 9)

    def generate_exercise_for_formula(self, formula: Formula,
                                     operation: str, num_terms: int = 5) -> Optional[Exercise]:
        """Generate an exercise that uses the specified formula"""
        max_attempts = 50

        for attempt in range(max_attempts):
            try:
                # Generate starting position appropriate for this formula
                first_term = self.generate_starting_position(formula, operation)

                terms = [first_term]
                operations = []
                current = first_term
                formula_used = False

                for term_idx in range(1, num_terms):
                    # First operation should use the target formula
                    if term_idx == 1:
                        op = operation
                        if formula.type in [FormulaType.SMALL_FRIENDS_PLUS,
                                          FormulaType.SMALL_FRIENDS_MINUS]:
                            number = self.generate_number_for_small_friends(formula, current, op)
                        elif formula.type in [FormulaType.BIG_FRIENDS_PLUS,
                                            FormulaType.BIG_FRIENDS_MINUS]:
                            number = self.generate_number_for_big_friends(formula, current, op)
                        else:
                            number = formula.number

                        if number is None:
                            break

                        formula_used = True
                    else:
                        # Random operations for remaining terms
                        op = random.choice(['+', '-'])
                        number = random.randint(1, 9)

                    # Validate the operation keeps result in valid range
                    if op == '+':
                        new_current = current + number
                    else:
                        new_current = current - number

                    # Keep result positive and reasonable
                    if new_current < 0 or new_current > 999:
                        break

                    terms.append(number)
                    operations.append(op)
                    current = new_current

                # Check if we have a complete exercise with the formula
                if len(terms) == num_terms and formula_used:
                    complexity = f"{formula.type.value}_{formula.number}"
                    exercise = Exercise(terms, operations, complexity)

                    # Verify the formula was actually used
                    if any(f.type == formula.type and f.number == formula.number
                          for f in exercise.formulas_used):
                        return exercise

            except Exception as e:
                continue

        return None

    def test_formula(self, formula: Formula, operation: str):
        """Test a specific formula"""
        print(f"Testing {formula}...")
        exercises = []

        for i in range(self.exercises_per_formula):
            exercise = self.generate_exercise_for_formula(formula, operation)
            if exercise:
                exercises.append(exercise)

        result = {
            'formula': str(formula),
            'formula_type': formula.type.value,
            'operation': operation,
            'exercises_generated': len(exercises),
            'target_count': self.exercises_per_formula,
            'success_rate': len(exercises) / self.exercises_per_formula * 100,
            'exercises': [ex.to_dict() for ex in exercises]
        }

        self.results.append(result)
        return result

    def test_all_formulas(self):
        """Test all formulas"""
        print("=" * 80)
        print("ANZAN FORMULA AUTOMATED TEST")
        print("=" * 80)
        print(f"Generating {self.exercises_per_formula} exercises per formula...")
        print()

        # Test Small Friends
        print("Testing Small Friends PLUS formulas...")
        for formula in SMALL_FRIENDS_PLUS:
            self.test_formula(formula, '+')

        print("\nTesting Small Friends MINUS formulas...")
        for formula in SMALL_FRIENDS_MINUS:
            self.test_formula(formula, '-')

        # Test Big Friends
        print("\nTesting Big Friends PLUS formulas...")
        for formula in BIG_FRIENDS_PLUS:
            self.test_formula(formula, '+')

        print("\nTesting Big Friends MINUS formulas...")
        for formula in BIG_FRIENDS_MINUS:
            self.test_formula(formula, '-')

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

    def generate_html_report(self, output_file: str = "anzan_test_report.html"):
        """Generate a beautiful HTML report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anzan Formula Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .summary {{
            padding: 40px;
            background: #f8f9fa;
            border-bottom: 3px solid #e9ecef;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 5px solid #667eea;
        }}

        .summary-card h3 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .summary-card p {{
            color: #6c757d;
            font-size: 0.9em;
        }}

        .content {{
            padding: 40px;
        }}

        .formula-section {{
            margin-bottom: 40px;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}

        .formula-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}

        .formula-title {{
            font-size: 1.8em;
            color: #2d3748;
        }}

        .formula-badge {{
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
        }}

        .success-rate {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 15px;
        }}

        .success-high {{
            background: #d4edda;
            color: #155724;
        }}

        .success-medium {{
            background: #fff3cd;
            color: #856404;
        }}

        .success-low {{
            background: #f8d7da;
            color: #721c24;
        }}

        .exercise {{
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid #28a745;
        }}

        .exercise-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .exercise-expression {{
            font-size: 1.4em;
            font-weight: bold;
            color: #2d3748;
            font-family: 'Courier New', monospace;
        }}

        .exercise-answer {{
            font-size: 1.4em;
            color: #28a745;
            font-weight: bold;
        }}

        .steps {{
            margin-top: 20px;
        }}

        .step {{
            display: grid;
            grid-template-columns: 60px 120px 120px 150px 1fr;
            gap: 15px;
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 8px;
            align-items: center;
            transition: all 0.3s ease;
        }}

        .step:hover {{
            background: #e9ecef;
            transform: translateX(5px);
        }}

        .step-number {{
            font-weight: bold;
            color: #667eea;
            text-align: center;
            font-size: 1.1em;
        }}

        .step-operation {{
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #2d3748;
            text-align: center;
        }}

        .step-current {{
            font-weight: bold;
            color: #28a745;
            text-align: center;
            font-size: 1.1em;
        }}

        .step-formula {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
        }}

        .formula-small-plus {{
            background: #d4edda;
            color: #155724;
        }}

        .formula-small-minus {{
            background: #cce5ff;
            color: #004085;
        }}

        .formula-big-plus {{
            background: #fff3cd;
            color: #856404;
        }}

        .formula-big-minus {{
            background: #f8d7da;
            color: #721c24;
        }}

        .formula-direct {{
            background: #e2e3e5;
            color: #383d41;
        }}

        .step-description {{
            color: #6c757d;
            font-size: 0.95em;
        }}

        .formulas-used {{
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}

        .formulas-used-title {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .formula-tag {{
            display: inline-block;
            padding: 6px 14px;
            margin: 5px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: bold;
        }}

        .no-exercises {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-style: italic;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            background: #2d3748;
            color: white;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧮 Anzan Formula Test Report</h1>
            <p>Raport automat de testare pentru toate formulele Anzan</p>
            <p>Generated: {timestamp}</p>
        </div>

        <div class="summary">
            <h2>📊 Sumar General</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>{len(self.results)}</h3>
                    <p>Formule testate</p>
                </div>
                <div class="summary-card">
                    <h3>{sum(r['exercises_generated'] for r in self.results)}</h3>
                    <p>Exerciții generate</p>
                </div>
                <div class="summary-card">
                    <h3>{sum(r['target_count'] for r in self.results)}</h3>
                    <p>Exerciții target</p>
                </div>
                <div class="summary-card">
                    <h3>{sum(r['success_rate'] for r in self.results) / len(self.results):.1f}%</h3>
                    <p>Rata medie de succes</p>
                </div>
            </div>
        </div>

        <div class="content">
"""

        # Group results by formula type
        small_friends_plus_results = [r for r in self.results if 'small_friends_plus' in r['formula_type']]
        small_friends_minus_results = [r for r in self.results if 'small_friends_minus' in r['formula_type']]
        big_friends_plus_results = [r for r in self.results if 'big_friends_plus' in r['formula_type']]
        big_friends_minus_results = [r for r in self.results if 'big_friends_minus' in r['formula_type']]

        # Generate sections for each formula type
        formula_groups = [
            ("Small Friends PLUS", small_friends_plus_results, "small-plus"),
            ("Small Friends MINUS", small_friends_minus_results, "small-minus"),
            ("Big Friends PLUS", big_friends_plus_results, "big-plus"),
            ("Big Friends MINUS", big_friends_minus_results, "big-minus"),
        ]

        for group_name, results, group_id in formula_groups:
            if not results:
                continue

            html += f"""
            <h2 style="margin: 40px 0 20px 0; color: #2d3748;">📚 {group_name}</h2>
"""

            for result in results:
                success_rate = result['success_rate']
                success_class = 'success-high' if success_rate >= 80 else ('success-medium' if success_rate >= 50 else 'success-low')

                html += f"""
            <div class="formula-section">
                <div class="formula-header">
                    <div>
                        <span class="formula-title">{result['formula']}</span>
                        <span class="success-rate {success_class}">{success_rate:.0f}% Success</span>
                    </div>
                    <span class="formula-badge">{result['exercises_generated']}/{result['target_count']} exercises</span>
                </div>
"""

                if result['exercises']:
                    for idx, exercise in enumerate(result['exercises'], 1):
                        html += f"""
                <div class="exercise">
                    <div class="exercise-header">
                        <span class="exercise-expression">{exercise['expression']}</span>
                        <span class="exercise-answer">= {exercise['correct_answer']}</span>
                    </div>

                    <div class="steps">
"""
                        for step in exercise['steps']:
                            formula_class = ''
                            if step['formula_type']:
                                formula_type = step['formula_type']
                                if 'small' in formula_type and 'plus' in formula_type:
                                    formula_class = 'formula-small-plus'
                                elif 'small' in formula_type and 'minus' in formula_type:
                                    formula_class = 'formula-small-minus'
                                elif 'big' in formula_type and 'plus' in formula_type:
                                    formula_class = 'formula-big-plus'
                                elif 'big' in formula_type and 'minus' in formula_type:
                                    formula_class = 'formula-big-minus'
                                else:
                                    formula_class = 'formula-direct'

                            formula_html = f'<span class="step-formula {formula_class}">{step["formula"]}</span>' if step['formula'] else '<span style="color: #adb5bd;">-</span>'

                            html += f"""
                        <div class="step">
                            <div class="step-number">#{step['step']}</div>
                            <div class="step-operation">{step['operation']}</div>
                            <div class="step-current">{step['current']}</div>
                            <div>{formula_html}</div>
                            <div class="step-description">{step['description']}</div>
                        </div>
"""

                        html += """
                    </div>
"""

                        if exercise['formulas_used']:
                            html += """
                    <div class="formulas-used">
                        <div class="formulas-used-title">✓ Formule folosite în acest exercițiu:</div>
                        <div>
"""
                            for formula in exercise['formulas_used']:
                                html += f'                            <span class="formula-tag formula-small-plus">{formula}</span>\n'

                            html += """
                        </div>
                    </div>
"""

                        html += """
                </div>
"""
                else:
                    html += """
                <div class="no-exercises">
                    ⚠️ Nu s-au putut genera exerciții pentru această formulă
                </div>
"""

                html += """
            </div>
"""

        html += """
        </div>

        <div class="footer">
            <p>🧮 Anzan Formula Test - MindAcademy</p>
            <p>Generated automatically for formula validation</p>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✓ HTML report generated: {output_file}")
        return output_file

    def generate_json_report(self, output_file: str = "anzan_test_report.json"):
        """Generate JSON report for programmatic analysis"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'formulas_tested': len(self.results),
                'total_exercises_generated': sum(r['exercises_generated'] for r in self.results),
                'total_target_exercises': sum(r['target_count'] for r in self.results),
                'average_success_rate': sum(r['success_rate'] for r in self.results) / len(self.results) if self.results else 0
            },
            'results': self.results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✓ JSON report generated: {output_file}")
        return output_file


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Anzan Formula Automated Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run test with 10 exercises per formula (default)
  python test_anzan_formulas.py

  # Run test with 20 exercises per formula
  python test_anzan_formulas.py --exercises 20

  # Custom output files
  python test_anzan_formulas.py --html my_report.html --json my_report.json
"""
    )

    parser.add_argument(
        '--exercises', '-e',
        type=int,
        default=10,
        help='Number of exercises to generate per formula (default: 10)'
    )

    parser.add_argument(
        '--html',
        type=str,
        default='anzan_test_report.html',
        help='HTML report output file (default: anzan_test_report.html)'
    )

    parser.add_argument(
        '--json',
        type=str,
        default='anzan_test_report.json',
        help='JSON report output file (default: anzan_test_report.json)'
    )

    args = parser.parse_args()

    # Run tests
    tester = AnzanFormulaTest(exercises_per_formula=args.exercises)
    tester.test_all_formulas()

    # Generate reports
    print("\nGenerating reports...")
    html_file = tester.generate_html_report(args.html)
    json_file = tester.generate_json_report(args.json)

    print("\n" + "=" * 80)
    print("REPORTS GENERATED SUCCESSFULLY")
    print("=" * 80)
    print(f"HTML Report: {html_file}")
    print(f"JSON Report: {json_file}")
    print("\nDeschide fișierul HTML într-un browser pentru a vizualiza raportul detaliat.")
    print("=" * 80)


if __name__ == '__main__':
    main()
