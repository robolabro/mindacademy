# Logica Progresivă Anzan - Documentație Completă

## Ordinea de Învățare și Formule Permise

### 1. Direct (4, 5, 9)
- **Calcule directe** cu numerele 4, 5, și 9
- **Nu necesită formule speciale**

---

### 2. Small Friends (Prieteni Mici)

#### Small Friends Plus
- **+1 = +5 - 4**: Poate include **Direct (4, 5, 9)**
- **+2 = +5 - 3**: Poate include **Direct + Small Friends (+1)**
- **+3 = +5 - 2**: Poate include **Direct + Small Friends (+1, +2)**
- **+4 = +5 - 1**: Poate include **Direct + Small Friends (+1, +2, +3)**

#### Small Friends Minus
- **-1 = -5 + 4**: Poate include **Direct + Small Friends Plus (toate)**
- **-2 = -5 + 3**: Poate include **Direct + Small Friends (+1, +2, +3, +4, -1)**
- **-3 = -5 + 2**: Poate include **Direct + Small Friends (+1, +2, +3, +4, -1, -2)**
- **-4 = -5 + 1**: Poate include **Direct + Small Friends (+1, +2, +3, +4, -1, -2, -3)**

**Distribuție probabilități:**
- Prima formulă (+1): 50% Direct + 50% din formulele anterioare
- Restul: 40% Direct + 30% formule anterioare + 30% Small Friends anterioare

---

### 3. Big Friends (Prieteni Mari)

**Ordinea de învățare:**
```
+1, +2, +3, +4, +5 → -1, -2, -3, -4, -5 → +6, +7, +8, +9 → -6, -7, -8, -9
```

#### Formule și Conținut Permis:

**+1 = -9 + 10**
- Direct (4, 5, 9)
- Small Friends (toate: +1, +2, +3, +4, -1, -2, -3, -4)

**+2 = -8 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1)

**+3 = -7 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2)

**+4 = -6 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3)

**+5 = -5 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4)

**-1 = -10 + 9**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5)

**-2 = -10 + 8**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1)

**-3 = -10 + 7**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1, -2)

**-4 = -10 + 6**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1, -2, -3)

**-5 = -10 + 5**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1, -2, -3, -4)

**+6 = -4 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1, -2, -3, -4, -5)

**+7 = -3 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1, -2, -3, -4, -5, +6)

**+8 = -2 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1, -2, -3, -4, -5, +6, +7)

**+9 = -1 + 10**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1, +2, +3, +4, +5, -1, -2, -3, -4, -5, +6, +7, +8)

**-6 = -10 + 4**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1 până +9, -1 până -5)

**-7 = -10 + 3**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1 până +9, -1 până -6)

**-8 = -10 + 2**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1 până +9, -1 până -7)

**-9 = -10 + 1**
- Direct (4, 5, 9)
- Small Friends (toate)
- Big Friends (+1 până +9, -1 până -8)

**Distribuție probabilități:**
- Prima formulă (+1): 50% Direct + 50% Small Friends
- Restul: 30% Direct + 30% Small Friends + 40% Big Friends anterioare

---

### 4. Familia (Family)

**Învățat după:** Toate formulele Big Friends (-9 fiind ultima)

**Conținut:**
- Direct (4, 5, 9)
- Small Friends (toate: +1, +2, +3, +4, -1, -2, -3, -4)
- Big Friends (toate: +1 până +9, -1 până -9)

**Distribuție probabilități:**
- 25% Direct
- 25% Small Friends
- 25% Big Friends (orice)
- 25% Combined (exerciții complexe care combină multiple tehnici)

---

### 5. Mixate (Mix)

**Învățat după:** Familia

**Conținut:**
- Toate formulele învățate anterior:
  - Direct (4, 5, 9)
  - Small Friends (toate)
  - Big Friends (toate)
  - Family (exerciții tip Familie)

**Distribuție probabilități:**
- 20% Direct
- 20% Small Friends
- 20% Big Friends (orice)
- 20% Family
- 20% Complex (exerciții foarte complexe, multiple tehnici)

---

## Principii Generale

### 1. Învățare Progresivă
Fiecare nouă formulă poate include în exerciții toate formulele învățate anterior, asigurându-se că elevii practică constant tehnicile deja învățate.

### 2. Creștere Graduală a Dificultății
- **Început:** Doar calcule directe
- **Small Friends:** Introducere la formule simple cu bila cerească (valoare 5)
- **Big Friends:** Formule avansate cu bila de pe tija de 10
- **Familia:** Combinare liberă a tuturor tehnicilor
- **Mixate:** Exerciții complexe care necesită multiple tehnici

### 3. Verificare Automată
Sistemul verifică automat dacă exercițiile generate respectă:
- Formula țintă este folosită efectiv în exercițiu
- Nu se folosesc formule care nu au fost încă învățate
- Distribuția probabilităților este respectată

### 4. Prevenirea Regenerării Infinite
Fiecare generator are:
- Maxim 50 de încercări pentru a genera un exercițiu valid
- Verificare strictă că formula țintă este folosită
- Fallback la exerciții mai simple dacă generarea eșuează

---

## Implementare Tehnică

### Funcții Cheie

1. **`getAllowedSmallFriendsFormulas(target)`**
   - Returnează lista de formule Small Friends permise pentru formula `target`

2. **`getAllowedBigFriendsFormulas(target)`**
   - Returnează lista de formule Big Friends permise pentru formula `target`
   - Respectă ordinea de învățare: +1→+5, -1→-5, +6→+9, -6→-9

3. **`generateSmallFriendsWithProgressive(target, addends, formula)`**
   - Generează exerciții pentru Small Friends cu logică progresivă
   - Distribuție: 40% Direct + 30% anterioare + 30% Small Friends anterioare

4. **`generateBigFriendsWithProgressive(target, addends, formula, section)`**
   - Generează exerciții pentru Big Friends cu logică progresivă
   - Distribuție: 30% Direct + 30% Small Friends + 40% Big Friends anterioare

5. **`generateFamily(addends, formula, section)`**
   - Generează exerciții tip Familie
   - Combină toate tehnicile învățate

6. **`generateMix(addends, formula, section)`**
   - Generează exerciții mixate
   - Nivel maxim de dificultate

---

## Exemple

### Exemplu Small Friends +2
Exercițiu generat pentru formula **+2 = +5 - 3**:

Poate conține:
- Calcul direct: `7 + 2 = 9` ✓
- Small Friends +1: `9 + 1 = 10` (folosește +1 = +5 - 4) ✓
- Formula țintă: `8 + 2 = 10` (folosește +2 = +5 - 3) ✓

### Exemplu Big Friends -1
Exercițiu generat pentru formula **-1 = -10 + 9**:

Poate conține:
- Calcul direct: `15 - 4 = 11` ✓
- Small Friends: `18 - 3 = 15` (folosește -3 = -5 + 2) ✓
- Big Friends +1 până +5: `7 + 3 = 10` (folosește +3 = -7 + 10) ✓
- Formula țintă: `20 - 1 = 19` (folosește -1 = -10 + 9) ✓

### Exemplu Familia
Exercițiu generat pentru **Familia**:

Poate conține orice combinație:
- Direct: `25 + 4 = 29` ✓
- Small Friends: `67 + 2 = 69` (folosește +2 = +5 - 3) ✓
- Big Friends: `48 + 7 = 55` (folosește +7 = -3 + 10) ✓
- Big Friends: `93 - 8 = 85` (folosește -8 = -10 + 2) ✓

---

## Testing

Pentru a testa logica progresivă, folosiți:

```bash
python test_anzan_formulas.py --exercises 10
```

Aceasta va genera:
- 10 exerciții pentru fiecare formulă
- Raport HTML detaliat cu toate calculele
- Raport JSON pentru analiză programatică

Rapoartele vor arăta:
- Ce formule au fost folosite în fiecare exercițiu
- Dacă formula țintă este folosită efectiv
- Pașii de calcul pentru fiecare exercițiu

---

Ultima actualizare: 2026-01-21
