# Forma-țintă: legătura Lecție ↔ Prezență prin Înscriere

> Document de lucru pentru chat-ul Airtable. Scop: mutarea legăturii dintre
> **Lectii** și **Prezente** de pe câmpul `Students Scheduled` (Lecție → Elevi)
> pe **Inscriere** (Lecție → Înscriere → Elev). Bază: `appNojgKwbj01pq8a`.

---

## De ce

Un copil poate avea mai multe **Înscrieri** în timp (module/grupe diferite). Dacă
prezența e legată direct de **Elev**, se pierde *pentru care înscriere/modul* a
fost prezența — ceea ce afectează:

- **progresul per modul** (Progres Lectii),
- **facturarea** (Rate v2 / Contracts v2 sunt deja legate de Înscriere),
- **transferurile** între grupe (aceeași persoană, înscrieri diferite).

Legând prezența de **Înscriere**, fiecare prezență aparține exact unui modul/grupă.

---

## Ce există deja (nu pornim de la zero)

| Tabel | Câmp existent | Rol |
|-------|---------------|-----|
| Prezente | **Inscriere** (link) | „Înscrierea exactă pentru care s-a generat prezența." — cheia țintă |
| Prezente | Elev, Lectie, Grupa (link) | rămân (Elev poate deveni lookup din Inscriere) |
| Inscrieri | **Prezente** (link, revers) | prezențele înscrierii |
| Inscrieri | **Lectii** (link) | lecțiile la care participă înscrierea |
| Lectii | **Inscrieri Selectate** (link) | înscrierile programate la lecție |
| Lectii | `Students Scheduled` (link → Elevi) | **mecanismul actual — de deprecat** |

Practic, infrastructura de legături prin Înscriere **există deja**; rămâne să
mutăm *sursa adevărului* + automatizările de pe `Students Scheduled` pe `Inscriere`.

---

## Forma-țintă (model)

1. **Lecția** aparține unei **Grupe** (`Nume Grupa`).
2. „Cine e programat la lecție" = **Înscrierile ACTIVE ale grupei** la data lecției
   (via `Lectii.Inscrieri Selectate`), NU o listă manuală de Elevi.
3. **Prezența** = una per **(Înscriere × Lecție)**:
   - `Prezente.Inscriere` = cheia canonică;
   - `Prezente.Lectie`, `Prezente.Grupa` = păstrate;
   - `Prezente.Elev` = de preferat **lookup din Inscriere → Elev** (o singură sursă),
     sau link direct ținut în sincron.
4. **Progres Lectii** se calculează din Prezențe (Attended=true). Rămâne corect;
   dacă îl leagă de `Elev + Lectie Template`, se poate rafina pe `Inscriere` pentru
   atribuire fără ambiguitate pe modul.

---

## Pași de migrare în Airtable (ordinea contează)

1. **Backfill `Prezente.Inscriere`** pentru rândurile existente: pentru fiecare
   prezență, găsește Înscrierea activă a Elevului în Grupa respectivă la data
   lecției. (Formulă ajutătoare / script pe o vizualizare; verifici pe un eșantion.)
2. **Actualizează Automatizarea A** (creare Lectie → creare Prezențe): sursa devine
   `Grupa → Înscrieri active` (populând `Lectii.Inscrieri Selectate`), și creează
   câte o Prezenta cu `Inscriere + Lectie + Grupa (+ Elev din lookup)`.
   Păstrează excepțiile existente: `Lectie Individuala` / `Lectie Recuperare` NU
   generează prezențe pentru toată grupa.
3. **Mută formulele/rollup-urile** care folosesc `Students Scheduled` pe legăturile
   prin Înscriere (ex. „Attended Rollup", „Completed Lessons", numărători).
4. **Actualizează interfețele/vizualizările** care afișează „studenți programați".
5. **Deprecare** `Students Scheduled` abia după ce 1–4 sunt validate (îl marchezi
   „de șters", nu îl ștergi imediat).

---

## Impact

- **Facturare** (Contracts v2 / Rate v2): deja pe Înscriere → lanțul se întărește.
- **Progres Lectii**: neschimbat dacă rămâne pe Elev+Template; se poate rafina pe Înscriere.
- **Transfer elev**: prezențele se atribuie corect înscrierii potrivite (modul corect).
- **Recuperări**: neschimbat (Attended=false + Genereaza Recuperare pe Prezenta).

---

## Ce oferă DEJA sincronizarea Mind.academy (nimic de schimbat în Django)

La **push**, Mind.academy scrie pe fiecare Prezenta: `Elev + Lectie + Grupa + **Inscriere**`
(când înscrierea e mapată). Deci după ce faci Înscrierea cheia canonică în Airtable,
push-ul nostru **o alimentează deja**. Reconcilierea se face după (Elev, Lecție),
fără duplicate.

> Opțional: dacă transformi `Prezente.Elev` în **lookup din Inscriere**, spune-mi
> și scot `Elev` din payload-ul de push (îl lăsăm doar `Inscriere` + `Lectie`).
> Momentan îl trimitem, e redundant dar inofensiv.

---

## Ordine sigură / riscuri

- Fă întâi **backfill** (1) și abia apoi comută **automatizarea** (2) — altfel prezențele
  noi n-ar avea Înscriere.
- Testează pe o **grupă pilot** (ex. R0133) înainte de toată baza.
- Ideal, lucrează pe o **copie a bazei** (duplicate) pentru pașii de automatizare,
  apoi replici pe producție.
- Nu șterge `Students Scheduled` până nu confirmi că formulele/interfețele nu-l mai folosesc.
