# Felipe's Fable Week — a decided plan (July 8–14, 2026)

Five real deliverables, sized to stay inside plan limits. One thing per day-ish;
each session starts by pointing Claude at its memory (CLAUDE.md / Context Pack).

## The rhythm

- **1 stretch project on Fable 5** (the expensive brain, used once, hard).
- **2 Cowork tasks** (files & documents — your natural terrain).
- **2 Claude Code tasks** (software — this repo and one new build).
- Everything else this week: Sonnet 5. Bulk file grunt-work: Haiku.

## ✅ Task 0 — done today (Claude Code)

Memory + guide + plan created in this repo, committed to branch
`claude/platform-exploration-learning-kuqpxa`.

## 🗂️ Cowork Task 1 — "Biblioteca Felipe Genovese" organizer (the centerpiece)

Your "app to tidy up everything I've produced." Cowork is the right environment:
it works on folders directly, no code needed.

1. Open Cowork (desktop app, or claude.ai on web — Cowork tab).
2. Point it at a local folder where you've synced/downloaded the Biblioteca
   (Google Drive for desktop makes Drive appear as a normal folder).
3. Paste your Context Pack, then say:
   *"Inventory every file here: build `catalog.csv` with filename, folder, type,
   date, a one-line description, project tag (World Cup / FICC / thesis / legal /
   pessoal / engenharia), and a duplicate flag. Propose a new folder tree. Don't
   move anything yet — show me the plan first."*
4. Review the plan, then tell it to execute the reorganization.

Output: a clean tree + `catalog.csv` — which becomes the data for Code Task 2.

## ⚖️ Cowork Task 2 — Legal-case binder

Point Cowork at the process-1025609 folder from Drive and ask for: a chronological
timeline of the case, an index of every document (what it is, date, why it matters),
and a list of gaps/missing documents — as one organized `binder.md` + spreadsheet.
(Claude organizes and summarizes; your BPP lawyers decide strategy.)

## ⚽ Claude Code Task 1 — Level up this repo

In a new Claude Code session on this repo: publish the "300 Analysts" page with
GitHub Pages so it has a real URL you can share, add a small "How this was built"
section for portfolio use, and wire in a CALL THE CUP teaser (bring the Monte Carlo
simulator into the page as a second tab, fed by `build_data.py`).

## 📚 Claude Code Task 2 — Biblioteca Catalog web app

New repo `biblioteca-felipe`. One prompt: *"Build a single-file `index.html` that
loads `catalog.csv` (from Cowork Task 1) and gives me search, filters by project
tag and type, and a duplicates view. Same no-build-step style as my World Cup page."*
Result: your personal library, searchable in a browser, hosted free on GitHub Pages.

## 🚀 Fable 5 stretch — the Career Package

One deep session on claude.ai with Fable 5 selected, Context Pack pasted:
*"Build my complete positioning package for work at the intersection of engineering
and applied AI: narrative (EN + PT-BR), CV rewrite, LinkedIn profile text, a
one-page portfolio outline linking the World Cup page, FICC, and Genovese
Inteligente, and a target list of 10 role types with why-me arguments. Skeptical
senior-reviewer pass at the end. Complete package, decide details yourself."*

This is the highest-leverage single use of the big model this week.

## Guardrails

- One big session per day; let agents finish instead of restarting them.
- Start sessions with memory (CLAUDE.md is automatic here; paste Context Pack elsewhere).
- If a session drifts, stop and restart with a tighter goal — cheaper than steering.
