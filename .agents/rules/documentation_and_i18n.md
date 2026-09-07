# Documentation, Internationalization (i18n) & Cross-Repository Guidelines

This rule defines mandatory standards for all AI agents and contributors maintaining documentation across the **Immo-Boussole** organization (`https://github.com/Immo-Boussole`).

---

## 1. Organization & Repository Ecosystem

The Immo-Boussole project consists of five interconnected repositories:

| Repository | Role | Technology |
|---|---|---|
| **[immo-boussole](https://github.com/Immo-Boussole/immo-boussole)** | Core web application, multi-platform scrapers, SQLite database, Ollama AI, MCP server | Python 3.12, FastAPI, Playwright/Browserless, Jinja2, Tailwind/Vanilla CSS |
| **[immo-boussole-extension](https://github.com/Immo-Boussole/immo-boussole-extension)** | Browser extension for instant property extraction on real estate portals (LeBonCoin, Figaro, etc.) | TypeScript, Vite, WebExtension Manifest V3 (Firefox, Chrome, Edge) |
| **[immo-boussole-orchestrator](https://github.com/Immo-Boussole/immo-boussole-orchestrator)** | Multi-instance fleet management, Docker host manager (local/remote SSH/TCP), CLI & Web UI | Python 3.12, Typer, FastAPI, python-on-whales, Jinja2 |
| **[immo-tion](https://github.com/Immo-Boussole/immo-tion)** | Property operations manager: equipment inventory, Carnet d''Information du Logement (CIL), maintenance & energy | Python 3.12, FastAPI, SQLite WAL, Jinja2 |
| **[immo-boussole.wiki](https://github.com/Immo-Boussole/immo-boussole/wiki)** | Central organization knowledge base, setup guides, and technical references | GitHub Wiki (Markdown) |

---

## 2. Language & Translation Standards (English First, Bilingual Parity)

- **Primary Source of Truth**: All user documentation must be written in **English** first (`README.md`, `Topic-EN.md`).
- **Synchronous French Parity**: Every user-facing documentation file in English **must** have an up-to-date French equivalent (`README.fr.md`, `Topic-FR.md`). When modifying English user documentation, update the French counterpart in the same task/commit.
- **Acronym Integrity (T.I.O.N.)**:
  - 🇬🇧 **English (Default)**: **T**racking, **I**nventory, **O**perations & **N**otifications
  - 🇫🇷 **Français (Parité)**: **T**ravaux, **I**nventaire, **O**pérations & **N**otifications
- **Language Coverage Matrix**:
  - **User-Facing Documentation** (Repository READMEs, Wiki pages, Terms, Privacy): **English + French** (paired files).
  - **Developer & AI Technical Specifications** (`.ai/`, `.agents/rules/`, `AGENTS.md`, code comments, docstrings): **English only**.
  - **UI Strings / Localization**: Handled via `locales/en.json` + `locales/fr.json`.
- **Text-First Principle**: When creating or updating documentation, focus on clear, comprehensive, and well-structured text and tables. Do not spend time creating or embedding new screenshots unless explicitly requested by the user.

---

## 3. Cross-Repository Navigation & Organization Namespace

- **Unified Header Banner**: Every repository `README.md` and `README.fr.md` must include a navigation block linking to the other organization components and the central wiki:
  ```markdown
  > 🧭 **Immo-Boussole Organization**: [Core Web App](https://github.com/Immo-Boussole/immo-boussole) • [WebExtension](https://github.com/Immo-Boussole/immo-boussole-extension) • [Orchestrator](https://github.com/Immo-Boussole/immo-boussole-orchestrator) • [Immo-Tion](https://github.com/Immo-Boussole/immo-tion) • [Central Wiki](https://github.com/Immo-Boussole/immo-boussole/wiki)
  ```
- **Consistent Organization Namespace**: Always use `https://github.com/Immo-Boussole/<repo>` for all badges, links, clone instructions, and CI workflow badges. Never use personal user handles in organization-wide links.

---

## 4. Multi-Repo Synchronization Trigger Rules

Whenever a code change in one repository alters:
1. **API Endpoints or Data Contracts** (e.g. Bridge API import format `POST /api/v1/bridge/import-listing`):
   - Update the client repository (`immo-boussole` / `immo-boussole-extension`).
   - Update the corresponding guide in `immo-boussole.wiki` (both EN and FR).
2. **Configuration or Environment Variables** (`.env.example`, `docker-compose.yml`):
   - Update `README.md` and `README.fr.md` configuration tables.
   - Update relevant Wiki deployment guides.
3. **Architecture or Tech Stack**:
   - Update `.ai/` documentation if present.
   - Update `Architecture-Overview-EN.md` and `Architecture-Overview-FR.md` in the central wiki.

---

## 5. Tone, Structure & Formatting Conventions

- **Headings**: Use emojis consistently in top-level headings (`# 🏠`, `## 🚀 Features`, `## ⚡ Quick Start`, `## ⚙️ Configuration`, `## 📚 Documentation`).
- **Tables**: Use markdown tables for comparisons, environment variables, feature matrices, and technical stacks.
- **Code Blocks**: Specify exact syntax identifiers (e.g. `bash`, `python`, `powershell`, `yaml`, `json`, `dockerfile`).
- **Alerts**: Use GitHub alerts (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`).
- **Commit Messages**: Always write Git commit messages in **English** using Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
