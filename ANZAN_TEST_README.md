# 🧮 Anzan Formula Automated Testing Tool

## Descriere

Acest tool generează automat exerciții pentru toate formulele Anzan (Small Friends, Big Friends) și produce un raport detaliat HTML și JSON care poate fi analizat manual pentru a verifica corectitudinea calculelor.

## Caracteristici

✅ **Testare completă** - Testează toate cele 26 de formule Anzan:
- Small Friends PLUS: +1, +2, +3, +4
- Small Friends MINUS: -1, -2, -3, -4
- Big Friends PLUS: +1 până la +9
- Big Friends MINUS: -1 până la -9

✅ **Raport HTML interactiv** - Raport vizual frumos formatat cu:
- Sumar general cu statistici
- Exerciții grupate pe tipuri de formule
- Pași detaliați pentru fiecare exercițiu
- Formule folosite evidențiate cu culori
- Design responsive și print-friendly

✅ **Raport JSON** - Pentru analiză programatică
- Structură completă a datelor
- Informații detaliate despre fiecare pas
- Formule identificate automat

✅ **Validare automată** - Verifică că:
- Formula corectă este folosită în fiecare exercițiu
- Calculele sunt corecte
- Exercițiile sunt generate corect pentru fiecare tip de formulă

## Instalare

Nu necesită dependențe speciale - folosește doar Python standard library.

```bash
# Tool-ul este gata de folosit
python test_anzan_formulas.py
```

## Utilizare

### Comanda de bază (10 exerciții per formulă)

```bash
python test_anzan_formulas.py
```

### Generează mai multe exerciții (ex: 20 per formulă)

```bash
python test_anzan_formulas.py --exercises 20
```

### Specifică fișiere custom pentru rapoarte

```bash
python test_anzan_formulas.py --html my_report.html --json my_report.json
```

### Opțiuni disponibile

```
--exercises, -e    Numărul de exerciții per formulă (default: 10)
--html            Fișierul HTML de output (default: anzan_test_report.html)
--json            Fișierul JSON de output (default: anzan_test_report.json)
```

## Interpretarea raportului

### Raportul HTML

Deschide `anzan_test_report.html` într-un browser pentru a vizualiza:

1. **Sumar general**
   - Numărul total de formule testate
   - Numărul de exerciții generate vs target
   - Rata medie de succes

2. **Secțiuni pe tipuri de formule**
   - Fiecare formulă are propria secțiune
   - Success rate (% de exerciții generate cu succes)
   - Lista de exerciții

3. **Detalii exercițiu**
   - Expresia completă (ex: `89 + 1 - 4 - 3 + 9 = 92`)
   - Pași detaliați cu formula folosită
   - Valoarea curentă după fiecare pas
   - Formule evidențiate cu culori diferite

### Coduri de culori pentru formule

- 🟢 **Verde** - Small Friends PLUS
- 🔵 **Albastru** - Small Friends MINUS
- 🟡 **Galben** - Big Friends PLUS
- 🔴 **Roșu** - Big Friends MINUS
- ⚪ **Gri** - Calcul direct (fără formulă)

### Ce să verifici în raport

✅ **Success Rate** - Ar trebui să fie >80% pentru fiecare formulă
- Dacă este mai mic, poate indica probleme în generarea exercițiilor

✅ **Formula corectă** - Verifică că fiecare exercițiu folosește formula țintă
- De exemplu, pentru "+2 = +5 - 3", verifică că într-adevăr apare această formulă

✅ **Pași de calcul** - Verifică că pașii sunt logici și corect calculați
- Fiecare pas ar trebui să arate formula folosită
- Rezultatul după fiecare pas ar trebui să fie corect

✅ **Varietate de exerciții** - Exercițiile ar trebui să fie variate
- Nu toate ar trebui să înceapă cu același număr
- Operațiile ar trebui să fie mixate

## Exemple de output

### Exemplu de exercițiu în raport:

```
Expresie: 89 + 1 - 4 - 3 + 9 = 92

Pași:
#0  START     89    -                Start with 89
#1  +1        90    +1 = +10 - 9    +1 → 90 (using +1 = +10 - 9)
#2  -4        86    -4 = -10 + 6    -4 → 86 (using -4 = -10 + 6)
#3  -3        83    Direct -3       -3 → 83 (using Direct -3)
#4  +9        92    +9 = +10 - 1    +9 → 92 (using +9 = +10 - 1)

Formule folosite: +1 = +10 - 9, -4 = -10 + 6, +9 = +10 - 1
```

## Structura raportului JSON

```json
{
  "timestamp": "2026-01-21T11:35:00",
  "summary": {
    "formulas_tested": 26,
    "total_exercises_generated": 90,
    "total_target_exercises": 130,
    "average_success_rate": 69.2
  },
  "results": [
    {
      "formula": "+1 = +5 - 4",
      "formula_type": "small_friends_plus",
      "operation": "+",
      "exercises_generated": 5,
      "target_count": 5,
      "success_rate": 100.0,
      "exercises": [
        {
          "expression": "23 + 1 + 4 - 2",
          "terms": [23, 1, 4, 2],
          "operations": ["+", "+", "-"],
          "correct_answer": 26,
          "steps": [...],
          "formulas_used": ["+1 = +5 - 4", ...]
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Success rate scăzut (<50%)

**Cauze posibile:**
- Generarea de poziții de start nu este optimă pentru acea formulă
- Restricțiile pentru formula respectivă sunt prea stricte
- Numărul de încercări maxime (50) nu este suficient

**Soluții:**
- Rulează cu mai puține exerciții: `--exercises 5`
- Verifică logica din `generate_starting_position()` pentru acea formulă
- Ajustează funcția `generate_number_for_*` pentru formula respectivă

### Nu se generează deloc exerciții pentru o formulă

**Cauze posibile:**
- Logica de validare este prea restrictivă
- Condițiile pentru formula respectivă nu sunt îndeplinite

**Soluții:**
- Verifică în raportul JSON ce formule au `exercises_generated: 0`
- Analizează funcțiile `_requires_small_friends()` și `_requires_big_friends()`
- Ajustează logica de generare pentru acele formule specifice

## Dezvoltare și îmbunătățiri

### Cum să adaugi teste pentru formule noi

1. Definește formula în lista corespunzătoare (`SMALL_FRIENDS_*`, `BIG_FRIENDS_*`)
2. Ajustează `generate_starting_position()` pentru noua formulă
3. Actualizează logica de validare în `_identify_formula()`

### Cum să îmbunătățești generarea de exerciții

- Modifică `generate_exercise_for_formula()` pentru logică mai complexă
- Ajustează numărul de încercări (`max_attempts`)
- Adaugă condiții suplimentare de validare

## Licență

Parte din MindAcademy - Anzan Training System

## Contact

Pentru bug-uri sau sugestii, contactează echipa de dezvoltare.
