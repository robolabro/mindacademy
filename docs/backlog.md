# Mind.academy — Backlog

> Sursa de adevăr pentru progres. Versionat în repo (branch `claude/fix-flashcard-results-IN1uV`).
> Legendă: `Todo` / `In Progress` / `Done` / `Blocked` · Ultima actualizare: sesiunea Epic 7.

---

## Epice livrate (rezumat)

| Epic | Descriere | Status |
|------|-----------|--------|
| 1 | Tip lecție (fizic/online) + link videoconferință pe grupă | **Done** |
| 2 | Lecții online live: sesiune, sarcini, monitorizare timp real | **Done** |
| 3 | Curriculum în platformă (Course→Module→LessonTemplate + milestones) | **Done** (sync vechi retras în Epic 7) |
| 4 | Performanță per grupă (teme + live + antrenament, agregat) | **Done** |
| 5 | „Mod Antrenament" — restricție simulatoare la elevi | **Done** |
| 7 | Sincronizare bidirecțională Airtable ↔ Mind.academy | **Done** (vezi mai jos) |

---

## Epic 7 — Sincronizare Airtable ↔ Mind.academy

**Principiu:** Airtable = sursă pentru STRUCTURĂ (pull); Mind.academy = sursă pentru EXECUȚIE (push). Un singur owner per entitate.

### Faza 1 — Modele + mapare · **Done**
- App `crm_sync`: `AirtableSyncMixin`, `SyncLog`, `AirtablePushJob`.
- Rename `GroupStudent` → `Enrollment` (RenameModel, non-distructiv).
- Câmpuri de mapare + execuție (airtable_record_id, status înscriere, absență/recuperare, takeaways).

### Faza 2 — Pull Airtable → Django · **Done (live, toată baza)**
- `sync_from_airtable` (+ `--grupa`, `--dry-run`, `--create-missing-teachers`, `--show-schema`).
- Entități: Grupe (doar Active), Module, Lectii Template, Elevi, Inscrieri (doar Activ), Lectii, Profesori.
- Idempotent; upsert după `airtable_record_id`; arhivare (nu ștergere); orar din „Start date" (UTC→Europe/Bucharest).
- Profesori: potrivire după email/nume (prefix), fără duplicate; `--create-missing-teachers` creează cei lipsă (+ TeacherProfile).
- Module atașate la un curs-container; Lectii Template cu ordine unică per modul.
- Lecțiile importate ca oglindă a orarului, cu nume sugestiv din șablon.

### Faza 4 — Push Django → Airtable · **Done (pilotat pe R0133)**
- `push_to_airtable` (+ `--grupa`, `--dry-run`, `--cleanup-duplicates`, `--only-pending`, `--push-new-lessons`).
- **Prezențe** → tabelul „Prezente" (create/update cu reconciliere după Elev+Lecție, fără duplicate; leagă Elev/Lecție/Grupa/Inscriere).
- **Takeaways** → update „Lesson Takeaways" (doar acest câmp; Mind.academy e owner).
- **§4/A** — lecții create în platformă → create în „Lectii" (opt-in `--push-new-lessons`).
- **Push automat** — semnal marchează execuția modificată `pending`; `--only-pending` trimite doar ce s-a schimbat.
- Niciodată scriere în „Progres Lectii" (gardă la nivel de client).

### Automatizare (cron Railway)
- **Pull nocturn** (`nightly_sync`) — `Todo` (de configurat în Railway; opțional).
- **Push la ~10 min** (`push_to_airtable --only-pending`) — `Todo` (de configurat în Railway).

---

## De făcut / decizii deschise

### Coordonare cu Airtable (chat separat)
- [ ] **§4/A — flag de suprimare auto-prezențe.** Stabilește ce flag oprește automatizarea să genereze prezențe pentru toată grupa pe lecțiile create de noi (ex. `Lectie Individuala`) și pune-l în `AIRTABLE_NEW_LESSON_FIELDS`. Abia apoi `--push-new-lessons` live.
- [ ] **Mutarea legăturii Lectie↔Prezente pe `Inscriere`** (acum se folosește `Students Scheduled`). Sync-ul nostru scrie deja legătura `Inscriere` pe Prezente — partea de platformă e gata; rămâne restructurarea + automatizările în Airtable.

### Configurare (Railway)
- [ ] Serviciu cron **push** `*/10 * * * *` → `push_to_airtable --only-pending` (token cu `data.records:write`).
- [ ] (Opțional) Serviciu cron **pull nocturn** `0 2 * * *` → `nightly_sync`.
- [ ] `AIRTABLE_TOKEN` cu scope write pe serviciul de cron; `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`.

### Testare
- [ ] Parcurgerea planului de testare (stories) — vezi `docs/test-plan` / artifact.
- [ ] Date demo: `python manage.py seed_test_data` (profesor + copii + grupă online). `--wipe` la final.

### Îmbunătățiri UX (propuneri)
- [ ] UI prietenos pentru profesor: marcare prezență + „ce s-a lucrat" într-un singur ecran de lecție.
- [ ] UI creare lecție ad-hoc (recuperare/suplimentară) din platformă (backend gata prin §4/A).
- [ ] Buton „push acum" în admin pe grupă (alternativă la cron pentru cazuri urgente).

### Idei de business de evaluat (neîncepute)
- [ ] Rol **părinte**: vizualizare progres/prezență copil în platformă.
- [ ] Vizibilitate **contract/plată** (din Airtable) pe pagina elevului, read-only.
- [ ] **Transfer elev** între grupe la mijloc de modul (înscriere veche Finalizat + nouă Activ) — verificat că progresul per grupă rămâne corect.
- [ ] **Demo/trial** (Funnel Stage din Airtable) — elevi neînscriși încă, eventual un tablou de urmărire.
- [ ] Notificări (email/WhatsApp) la absență / recuperare generată.
