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
- **Takeaways + Temă (Homework)** → update în „Lectii" (doar aceste câmpuri; Mind.academy e owner; pull nu le suprascrie).
- **Push automat** — semnal marchează execuția modificată `pending`; `--only-pending` trimite doar ce s-a schimbat.
- **Mai multe grupe deodată** — `--grupa=COD1,COD2,...` la pull ȘI push.
- Niciodată scriere în „Progres Lectii" (gardă la nivel de client).

### UX profesor · **Done**
- **Ecran unificat „Gestionează lecția"** (`lesson_manage`): prezență (prezent/absent, absență anunțată, generează recuperare, evaluare 1–5, notiță) + „ce s-a lucrat" + temă + milestones + pornire lecție live — într-un singur loc. La salvare, execuția se marchează `pending` → push automat.
- **Pagina grupei**: fiecare lecție duce la ecranul de gestionare; lecțiile trecute arată sumarul de prezență.
- **Date demo**: `seed_test_data` (profesor + copii + grupă online).

### Automatizare (cron Railway)
- **Pull nocturn** (`nightly_sync`) — **Done** (serviciu `mindacademy-cron`, `0 2 * * *`, `AIRTABLE_TOKEN` read).
- **Push nocturn** (`nightly_push`) — trimite doar execuția `pending` (prezențe + takeaways + temă); NU creează lecții noi, NU șterge duplicate. `Todo` (de configurat un al doilea serviciu cron cu token write).

---

## De făcut / decizii deschise

### Coordonare cu Airtable (chat separat)
- [ ] **§4/A — flag de suprimare auto-prezențe.** Stabilește ce flag oprește automatizarea să genereze prezențe pentru toată grupa pe lecțiile create de noi (ex. `Lectie Individuala`) și pune-l în `AIRTABLE_NEW_LESSON_FIELDS`. Abia apoi `--push-new-lessons` live.
- [ ] **Mutarea legăturii Lectie↔Prezente pe `Inscriere`** (acum se folosește `Students Scheduled`). Sync-ul nostru scrie deja legătura `Inscriere` pe Prezente — partea de platformă e gata; rămâne restructurarea + automatizările în Airtable.

### Configurare (Railway)
- [x] Serviciu cron **pull nocturn** `0 2 * * *` → `nightly_sync` (`mindacademy-cron`, token read).
- [ ] Serviciu cron **push nocturn** `0 3 * * *` → `nightly_push` (token cu `data.records:write`).
- [ ] `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` + `MISE_PYTHON_GITHUB_ATTESTATIONS=false` pe serviciul de push.

### Testare
- [ ] Parcurgerea planului de testare (stories) — vezi `docs/test-plan` / artifact.
- [ ] Date demo: `python manage.py seed_test_data` (profesor + copii + grupă online). `--wipe` la final.

### Îmbunătățiri UX
- [x] Ecran unificat de lecție (prezență + „ce s-a lucrat" + temă + milestones + live) — **Done** (`lesson_manage`).
- [x] Pagina grupei duce la ecranul de gestionare per lecție + sumar prezență — **Done**.
- [ ] UI creare lecție ad-hoc (recuperare/suplimentară) din platformă (backend gata prin §4/A; lipsește ecranul dedicat).
- [ ] Buton „push acum" în admin pe grupă (alternativă la cron pentru cazuri urgente).
- [ ] Buton direct „Gestionează" în calendar (acum e din pagina grupei).

### În lucru (sesiunea curentă)
- [ ] **B — Progres înscriere (read-only din Airtable):** total prezențe + lecții viitoare rămase din modul, afișate în admin (Enrollment) și în platforma profesor (per copil). Blocat pe numele câmpurilor Airtable (Progres Lectii / Inscrieri).
- [ ] **A — Aliniere Curs:** un Curs local per „Categorie Curs" din Airtable (decizie în așteptare).
- [ ] **Front-end mindacademy.ro — refresh vizual** (pagina mamă mai „fresh"). Direcție + livrare (mockup vs. direct) de stabilit.
- [x] **§7 — Prezență rapidă:** pre-bifat prezent, debifare = absent, extras în „Editează" — **Done**.
- [x] **Recuperări în platformă:** marcare distinctă + text explicativ + editare dată → push în Airtable — **Done**.

### Idei de business de evaluat (neîncepute)
- [ ] Rol **părinte**: vizualizare progres/prezență copil în platformă.
- [ ] Vizibilitate **contract/plată** (din Airtable) pe pagina elevului, read-only.
- [ ] **Transfer elev** între grupe la mijloc de modul (înscriere veche Finalizat + nouă Activ) — verificat că progresul per grupă rămâne corect.
- [ ] **Demo/trial** (Funnel Stage din Airtable) — elevi neînscriși încă, eventual un tablou de urmărire.
- [ ] Notificări (email/WhatsApp) la absență / recuperare generată.
