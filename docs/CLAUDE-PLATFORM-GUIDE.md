# The Claude Platform, Explained for Felipe (July 2026)

A plain-language map of every Claude "place" you can work in, which model to pick,
what "agent" actually means, and how to give Claude memory. Written assuming no
developer background.

---

## 1. The places (apps) — and when to use each

Think of it as one brain (the Claude models) wearing different uniforms:

| Place | What it is | Use it when... |
|---|---|---|
| **Claude (claude.ai / mobile / desktop)** | The regular chat. Conversations, file uploads, artifacts (interactive pages Claude builds), Projects, connectors to your apps. | Thinking, writing, analyzing a document, quick research, brainstorming. Your default. |
| **Cowork** | Claude working *in a folder of files* like a colleague at the desk next to you. It reads, renames, converts, reorganizes, and produces documents/spreadsheets/decks — no code knowledge needed. Now on desktop, web, and mobile; sessions run remotely and keep going even when you close the laptop. | Organizing the Biblioteca, building a legal-case binder, turning messy folders into clean deliverables. **This is your power tool as a non-developer.** |
| **Claude Code** | Claude working *in a code repository* (like this one). Terminal, web (claude.ai/code), desktop app, or straight from GitHub. It writes code, runs it, commits, and pushes. | Building or upgrading anything that is software: this World Cup page, a catalog app, CALL THE CUP. You describe; it builds. |
| **Projects (inside claude.ai)** | Folders for chats, with shared files and custom instructions that apply to every chat inside. | Ongoing themes: "Legal case", "Job search", "Thesis". Paste your Context Pack into the project instructions once — every chat there knows you. |
| **Claude in Chrome / Claude for Excel** | Claude operating inside your browser / spreadsheet. | Filling forms, navigating sites, working over spreadsheets like SEPI/Radar_Imoveis. |
| **Claude Agent SDK / API** | For developers building their own Claude-powered apps (what FICC-style systems use underneath). | Later, if you productize something. |
| **Claude for Life Sciences ("Claude Science")** | Claude with scientific connectors (PubMed, benchling-style tools) for research workflows. | Literature work for the thesis; you already have Consensus/Scholar/alphaXiv connected. |

**Rule of thumb:** documents & folders → Cowork. Software → Claude Code.
Everything else → regular Claude, organized into Projects.

## 2. The models — which one, when

(Names you asked about: "Sony" = **Sonnet**, "Raiku" = **Haiku**.)

| Model | Personality | Use for | Cost feel |
|---|---|---|---|
| **Fable 5** (new, Mythos-class tier, above Opus) | The deepest thinker Anthropic ships to everyone. | The hardest work: multi-step projects, big analyses, "push the limits" week. Spend it where the decision is expensive to get wrong. | Highest |
| **Opus 4.8** | Very strong daily driver; has "fast mode". | Serious writing, coding sessions, strategy. | High |
| **Sonnet 5** | The balanced workhorse. | 80% of everything: drafting, summarizing, normal coding. | Medium |
| **Sonnet 4.6** | Previous workhorse, still solid. | When Sonnet 5 is unavailable; routine tasks. | Medium-low |
| **Haiku 4.5** | Fast and cheap. | Bulk/simple work: renaming, extracting, classifying hundreds of files. | Lowest |

Budget strategy (matches your own Context Pack): **Haiku for volume, Sonnet for
routine, Fable/Opus for judgment.** In apps you pick the model in the model selector;
in Claude Code type `/model`.

## 3. "Agent" vs "not agent" — the only distinction that matters

- **Not an agent (chat):** you ask, Claude answers, you act. One turn at a time.
  Regular Claude conversations.
- **Agent:** you give a *goal*, and Claude takes many actions on its own — reading
  files, running programs, browsing, correcting its own mistakes — and comes back
  with the finished result. Claude Code, Cowork, deep research, and scheduled
  routines are all agents.

When to want an agent: the task has many steps, touches real files/systems, or
should keep running while you do something else. When chat is enough: you mainly
need thinking, writing, or explanation.

## 4. "System instructions" and prompts, demystified

- **Prompt:** what you type. Best pattern for you: *context → goal → constraints →
  "deliver the complete package, decide details yourself."*
- **Custom/system instructions:** standing orders Claude reads before every chat —
  set them in Settings (personal preferences) or per-Project. This is where your
  ground rules ("no menus, complete packages, show steps") belong.
- **CLAUDE.md:** the same idea for Claude Code — a file in the repo (like the one
  now at the root here) read at the start of every session.
- **Skills:** reusable instruction packs (yours or from the community) that Claude
  loads when relevant. You can ask Claude Code to create one from any repeated
  workflow, e.g. an "AuditFix" skill encoding your double-test rule.

## 5. Memory — how to make Claude know you everywhere

You already invented the right thing: the **AI Collaboration Context Pack** in Notion.
The platform now gives it four permanent homes:

1. **claude.ai memory + personal preferences** (Settings): Claude remembers across
   chats; preferences hold your ground rules.
2. **Projects**: Context Pack pasted into each project's instructions.
3. **Claude Code**: `CLAUDE.md` per repo (done here) — and a personal global one at
   `~/.claude/CLAUDE.md` applies to *all* your repos. Say "remember X" in a session
   to append.
4. **Cowork**: keep a `CONTEXT.md` in any folder you point it at; it reads it like
   Claude Code reads CLAUDE.md.

Keep Notion as the master copy; the others are mirrors.

## 6. What's new out in the world (July 2026)

- **Cowork went web + mobile**, sessions run in the cloud and survive your laptop
  closing; Chat and Cowork now share one home for projects and artifacts.
- **Fable 5 / Mythos 5** launched — a new tier above Opus.
- **Microsoft 365 connector can now write** (send email, manage calendar, edit files).
- **Claude Code + Cowork reached government (FedRAMP High)** — a sign these agent
  tools are the long-term center of the platform.

Sources: [Anthropic — Claude Cowork](https://www.anthropic.com/product/claude-cowork),
[TechCrunch](https://techcrunch.com/2026/07/07/the-coding-agent-wars-are-spilling-into-the-rest-of-the-office-claude-cowork/),
[9to5Mac](https://9to5mac.com/2026/07/07/anthropic-expanding-claude-cowork-to-mobile-and-web-details-here/),
[Claude release notes](https://support.claude.com/en/articles/12138966-release-notes).

## 7. Where to learn (official + community)

- **Docs:** code.claude.com/docs (Claude Code), support.claude.com (apps),
  docs.claude.com (API/Agent SDK).
- **Anthropic Academy:** anthropic.com/learn — free structured courses, from
  "Claude 101" to building agents.
- **Community:** the Anthropic Discord, r/ClaudeAI, and the claude-code GitHub
  repo (issues + discussions) are where new tricks appear first.
