# Mind.academy — Index materiale

> Punct unic de acces la tot ce s-a dezvoltat. Versionat în repo (branch `claude/fix-flashcard-results-IN1uV`).
> Ultima actualizare: sesiunea Epic 7 + refresh site.

## 🔗 Acces rapid

- **Artifacts (claude.ai):** în terminalul Claude Code scrie `/artifacts` (listează tot; `o` deschide, `c` copiază linkul); `ctrl+]` redeschide ultimul. Pe web: <https://claude.ai/code/artifacts>.
- **Docs în repo:** folderul `docs/` de pe branch (pe GitHub sau local).

---

## 📄 Artifacts publicate

| Material | Ce e | Link |
|---|---|---|
| **Ghid Admin · Mind.academy ↔ Airtable** | Ghidul de operare (§1–§8: grupă, elev, alocare, lecții, recuperări, conținut, prezență, curriculum) | <https://claude.ai/code/artifact/9714171d-e90d-4b08-9ee4-6ac6ba7eb78f> |
| **Plan de testare** | Stories de testat (inclusiv online + edge cases business) | <https://claude.ai/code/artifact/2c61a28c-3862-4269-be84-1246ccb6d032> |
| **MindAcademy Landing** (canvas editabil) | Refresh homepage — 2 direcții: „Modern japonez" + „Motion & minimal (Emil)". Editabil, cu Save | <https://claude.ai/code/artifact/71ae2360-5391-4373-8740-2ddfa4568359> |
| **MindAcademy** (mockup static) | Prima variantă de refresh homepage („modern japonez") | <https://claude.ai/code/artifact/90551235-84f4-476f-8cc4-0efa4866f677> |
| **Mockup · Pagina grupei (profesor)** | Machetă pagină grupă | <https://claude.ai/code/artifact/54a180a0-f5ad-4e6c-bf85-592c9fea5cf5> |
| **Mockup · Ecran lecție profesor** | Machetă „Gestionează lecția" | <https://claude.ai/code/artifact/464505b4-d693-43b3-b9ff-87c73185a03a> |
| **airtable-inscriere-link.md** | Document formă-țintă: mutarea legăturii Lectie↔Prezente pe Înscriere | <https://claude.ai/code/artifact/9e3a31d7-c8a7-4aeb-8a8b-77561846d8f5> |

---

## 📁 Fișiere în repo

- **Backlog:** [`docs/backlog.md`](./backlog.md) — sursa de adevăr pentru progres/to-do.
- **Formă-țintă Inscriere:** [`docs/airtable-inscriere-link.md`](./airtable-inscriere-link.md).
- **Homepage / refresh site (cod live):**
  - `templates/courses/home.html` — homepage (direcția Emil).
  - `static/css/home.css` — secțiunile homepage-ului.
  - `static/css/site.css` — refresh global pe tot site-ul public (chrome + componente).
- **Surse design canvas** (pentru re-editare în Claude Design):
  - `Main.dc.html` (direcția „Modern japonez"), `Motion.dc.html` (direcția „Emil"), `canvas.json`.

---

## 🗺️ Unde caut ce

- „Cum se face X în operare?" → **Ghidul de admin** (artifact §1–§8).
- „Ce mai avem de făcut / ce s-a livrat?" → **`docs/backlog.md`**.
- „Cum arată / edităm homepage-ul?" → **canvas-ul MindAcademy Landing** (vizual) sau `templates/courses/home.html` (cod).
- „Ce testăm?" → **Planul de testare** (artifact).
