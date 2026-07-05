# Restricții Calcul Direct - Versiune Actualizată (2026-02-20)

## Overview

Acest document descrie restricțiile pentru generarea exercițiilor de Calcul Direct (direct-to-4, direct-to-5, direct-to-9). Restricțiile au fost relaxate pentru a permite mai multă varietate și exerciții mai realiste.

---

## 1. Operații Permise (Tabele de Directă)

### Direct-to-4 (Numerele 1-4)

**Adunări permise:**
```
1+1, 1+2, 1+3
2+1, 2+2
3+1
```
**Total: 6 combinații de adunare**

**Scăderi permise:**
```
1-1
2-1, 2-2
3-1, 3-2, 3-3
4-1, 4-2, 4-3, 4-4
```
**Total: 10 combinații de scădere**

---

### Direct-to-5 (Introducere cifra 5)

Include toate operațiile din Direct-to-4, plus:

**Adunări NOI:**
```
1+5, 2+5, 3+5, 4+5
```
**Total adunări: 6 + 4 = 10 combinații**

**Scăderi NOI:**
```
6-1, 6-5
7-1, 7-2, 7-5
8-1, 8-2, 8-3, 8-5
9-1, 9-2, 9-3, 9-4, 9-5
```
**Total scăderi: 10 + 14 = 24 combinații**

---

### Direct-to-9 (Numerele mari 6-9)

Include toate operațiile din Direct-to-4 și Direct-to-5, plus:

**Adunări NOI:**
```
1+6, 1+7, 1+8
2+6, 2+7
3+6
```
**Total adunări: 10 + 6 = 16 combinații**

**Scăderi NOI:**
```
6-6
7-6, 7-7
8-6, 8-7, 8-8
9-6, 9-7, 9-8, 9-9
```
**Total scăderi: 24 + 10 = 34 combinații**

#### ❌ Scăderi BLOCATE (Corect!)

Următoarele operații sunt **corect blocate** pentru că produc rezultate negative:
```
5-6 = -1
5-7 = -2
5-8 = -3
5-9 = -4
```

Acestea NU pot fi folosite în Calcul Direct pentru că rezultatul este negativ.

---

## 2. Restricții pentru Rezultate

### 2.1 Rezultat Final
✅ **Obligatoriu:** `1 ≤ rezultat final ≤ 9`

Rezultatul final trebuie să fie între 1 și 9 (inclusiv) pentru toate nivelurile de Calcul Direct.

### 2.2 Rezultate Intermediare (RELAXAT!)

**Versiune anterioară (❌ Prea restrictivă):**
- Toate rezultatele intermediare trebuiau să fie între 1 și 9

**Versiune nouă (✅ Actualizată 2026-02-21):**
- ✅ Rezultate intermediare `>= 0` (permite treceri prin 0)
- ✅ Rezultate intermediare **pot fi > 9** (permite mai multă varietate)

**Exemple:**
```
Exercițiu 1: 8 + 6 - 7 - 5 + 6 = 8
Pași intermediari:
8 + 6 = 14  ← Permis (> 9)
14 - 7 = 7  ✓
7 - 5 = 2   ✓
2 + 6 = 8   ✓ (rezultat final valid)

Exercițiu 2: 5 - 5 + 3 = 3
Pași intermediari:
5 - 5 = 0   ← Acum permis (trecere prin 0)
0 + 3 = 3   ✓ (rezultat final valid)
```

**Impact:** Mai multe exerciții cu scăderi, mai multă varietate, permite treceri prin 0!

---

## 3. Restricții pentru Repetarea Numerelor

### 3.1 Repetări Consecutive (PĂSTRAT)

✅ **Regula:** NU permite același număr de 2 ori consecutiv

**Exemple:**
```
✅ VALID:   7 - 6 + 3 - 1 = 3
❌ INVALID: 7 - 6 - 6 + 2 = -3 (6 repetat consecutiv)
```

**Cod:**
```javascript
const MAX_CONSECUTIVE_REPETITIONS = 1;
```

### 3.2 Total Occurrences (ELIMINAT!)

**Versiune anterioară (❌ Eliminată):**
- Maximum 2-3 apariții totale pentru fiecare număr

**Versiune nouă (✅ Fără limită):**
- ✅ Nu mai există restricție pentru numărul total de apariții
- ✅ Doar restricția consecutivă rămâne activă

**Impact:** Permite exerciții mai naturale și variate

---

## 4. Restricții pentru Numere Mari (6-9) - DIRECT-TO-9

### 4.1 Versiune Anterioară (❌ Prea restrictivă)

**Înainte:**
- Trebuia 40-70% din termenii **NON-FIRST** să fie 6-9
- Primul termen era exclus din calcul
- Formula: `largeCount / (totalTerms - 1) >= percentage`

**Probleme:**
- Limita prea strictă, prea greu de generat
- Primul termen nu conta, ceea ce era artificial

### 4.2 Versiune Nouă (✅ Actualizată 2026-02-20)

**Acum:**
- ✅ Trebuie 30-50% din **TOȚI termenii** să fie 6-9 (inclusiv primul!)
- ✅ Formula: `largeCount / totalTerms >= percentage`

**Procente target în funcție de numărul de termeni:**
```
3 termeni:  50% (minim 2 numere mari din 3)
4 termeni:  40% (minim 2 numere mari din 4)
5+ termeni: 30% (minim 2 numere mari din 5)
```

**Exemple:**
```
✅ VALID: 8 - 6 + 3 = 5
         (2 numere mari din 3 termeni = 67% ✓)

✅ VALID: 7 - 6 + 2 + 6 = 9
         (3 numere mari din 4 termeni = 75% ✓)

✅ VALID: 3 - 1 + 6 - 5 + 6 = 9
         (2 numere mari din 5 termeni = 40% ✓)
```

**Impact:** Mai multă flexibilitate, primul termen poate ajuta!

---

## 5. Restricții pentru Cifra 5 - SMALL FRIENDS (SIMILAR)

### 5.1 Versiune Nouă (✅ Actualizată)

**Acum:**
- ✅ Trebuie 30-60% din **TOȚI termenii** să conțină cifra 5
- ✅ Include primul termen în calcul

**Procente target:**
```
3 termeni:  60% (minim 2 cincișori)
4 termeni:  50% (minim 2 cincișori)
5 termeni:  40% (minim 2 cincișori)
6+ termeni: 30% (minim 2 cincișori)
```

---

## 6. Validări și Verificări

### 6.1 Verificări Active

✅ **Operații permise:** Verifică `isAllowedOperation()` pentru fiecare pas
✅ **Rezultat final:** `1 ≤ result ≤ 9`
✅ **Rezultate intermediare:** `result >= 0` (permite treceri prin 0)
✅ **Repetări consecutive:** MAX 1 consecutiv
✅ **Numere mari (6-9):** Minim 30-50% pentru direct-to-9
✅ **Cifra 5:** Minim 30-60% pentru Small Friends (NU se aplică la direct-to-9)

### 6.2 Verificări Eliminate

❌ **Rezultate intermediare <= 9:** ELIMINAT (acum permite > 9)
❌ **Max total occurrences:** ELIMINAT (acum fără limită totală)
❌ **Restricții non-first:** MODIFICAT (acum include primul termen)

---

## 7. Exemple Complete

### Direct-to-4
```
✅ 3 - 2 + 1 = 2
✅ 2 + 1 + 1 = 4
✅ 4 - 3 + 2 - 1 = 2
```

### Direct-to-5
```
✅ 4 + 5 - 2 = 7
✅ 2 + 5 - 5 = 2
✅ 4 - 1 + 5 - 2 = 6
```

### Direct-to-9 (cu rezultate intermediare > 9!)
```
✅ 7 - 6 + 6 = 7
   (7-6=1, 1+6=7)

✅ 8 + 6 - 7 - 3 = 4
   (8+6=14 > 9 ✓, 14-7=7, 7-3=4)

✅ 9 - 6 + 6 - 7 - 1 + 8 - 7 - 1 + 7 = 8
   (Multe scăderi, rezultate intermediare variate)
```

---

## 8. Beneficii ale Noilor Restricții

### 8.1 Mai Multe Scăderi
- Înainte: Puține scăderi din cauza restricției <= 9
- Acum: Multe scăderi posibile (vezi exemplele din test)

### 8.2 Mai Multă Varietate
- Înainte: Restricții artificiale limitau combinațiile
- Acum: Exerciții mai naturale și diverse

### 8.3 Mai Realist Pedagogic
- Înainte: Restricții prea stricte
- Acum: Permite rezultate intermediare > 9 (natural în calcul mental)

### 8.4 Generare Mai Rapidă
- Înainte: Multe încercări eșuate
- Acum: Mai puține restricții = generare mai eficientă

---

## 9. Testing

**Test executat:** `node test_calcul_direct.js`
**Rezultat:** ✅ 50/50 exerciții generate cu succes

**Observații:**
- Mai multe scăderi în exerciții
- Varietate mai mare de combinații
- Numere mari (6-9) bine distribuite
- Rezultate finale toate valide (1-9)

---

## 10. Implementare Tehnică

### Funcții Cheie

**`isAllowedOperation(currentValue, operation, operand, complexity)`**
- Verifică dacă o operație este în tabelele de directă
- Returnează `true` dacă operația este permisă

**`validateIntermediateResults(terms, operations)`**
- Verifică că toate rezultatele intermediare >= 0 (permite treceri prin 0)
- ✅ NU mai verifică <= 9 (RELAXAT!)

**`shouldAvoidTermRepetition(termsArray, candidateTerm, totalTermCount)`**
- Verifică doar repetări consecutive
- ✅ NU mai verifică total occurrences (ELIMINAT!)

### Constante

```javascript
// Repetări
const MAX_CONSECUTIVE_REPETITIONS = 1;

// Numere mari (6-9) pentru direct-to-9
const TARGET_PERCENTAGE = {
  3: 0.5,  // 50%
  4: 0.4,  // 40%
  5: 0.3   // 30%
};

// Cifra 5 pentru Small Friends
const FIVE_PERCENTAGE = {
  3: 0.6,  // 60%
  4: 0.5,  // 50%
  5: 0.4,  // 40%
  6: 0.3   // 30%
};
```

---

## Changelog

**2026-02-21 - Permite treceri prin 0**
- ✅ Modificat restricția rezultate intermediare: `>= 0` (în loc de `>= 1`)
- ✅ Permite exerciții cu treceri prin 0 (ex: 5-5+3=3)
- ✅ Clarificat că regula cifrelor 5 se aplică DOAR la Small Friends și direct-to-5, NU la direct-to-9

**2026-02-20 - Versiunea Actualizată**
- ✅ Eliminat restricția rezultate intermediare <= 9
- ✅ Eliminat restricția max total occurrences
- ✅ Modificat restricția numere mari: include primul termen
- ✅ Modificat restricția cifra 5: include primul termen
- ✅ Verificat că scăderile 5-6, 5-7, 5-8, 5-9 rămân corect blocate

**Autor:** Claude (MindAcademy - Anzan Training System)
