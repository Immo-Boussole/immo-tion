# General Guidelines for AI Agents (Immo-Tion)

This document centralizes all mandatory rules and best practices for any AI agent working on this repository (`immo-tion`).

---

## 1. Responsive Design & Multi-Device Compatibility

For every code or user interface (UI/UX) modification:

- **Mandatory Multi-Device Support**: Always ensure interfaces render and function optimally across:
  - **PC / Desktop** (standard and widescreen displays)
  - **Tablets** (portrait and landscape orientations)
  - **Smartphones / Mobile Devices** (narrow vertical viewports, touch targets $\ge 44\text{px}$, no undesirable horizontal overflow). Users inspect appliances, crawl into basements, and photograph invoices directly with their smartphones!
- **CSS & Layout Checks**:
  - Use fluid flexbox/grid layouts and appropriate media queries.
  - Maintain component legibility, accessibility, and responsiveness (modals, banners, forms, maintenance tables, asset cards).
- **Detailed Reference**: See [.agents/rules/responsive_design.md](.agents/rules/responsive_design.md).

---

## 2. Git Commit Message Format

For every code change:

- Always provide a concise, clear Git commit message in **English** at the end of the response / task summary, adhering to the **Conventional Commits** standard (e.g. `feat(...)`, `fix(...)`, `refactor(...)`, `test(...)`, `docs(...)`).
- **Detailed Reference**: See [.agents/rules/commit_message_guideline.md](.agents/rules/commit_message_guideline.md).

---

## 3. Code Quality, Performance & Testing

- **Mandatory Local Pre-Push Validation**: Before pushing any commit or PR, always run local validation suites:
  ```bash
  python tests/run_tests.py --ci
  ```
  Ensure all tests (API, database, models, maintenance schedules, Jinja syntax, i18n parity) pass with **100% OK**.
- **Python 3.12+**: Prefer idiomatic, type-annotated Python. Use FastAPI with async route handlers.
- **SQLite WAL Mode**: Always ensure SQLite connections enable WAL mode (`PRAGMA journal_mode=WAL;`) and foreign keys (`PRAGMA foreign_keys=ON;`).
- **Security**: Never log, expose in API responses, or render in the UI any sensitive credentials (SMTP passwords, webhook secrets).

---

## 4. Documentation, Internationalization (i18n) & Cross-Repository Parity

- **English First & French Parity**: Write user-facing documentation in English first (`README.md`), and maintain exact parity in French (`README.fr.md`) in the same task/commit.
- **Acronym Integrity (T.I.O.N.)**:
  - 🇬🇧 **English (Default)**: **T**racking, **I**nventory, **O**perations & **N**otifications
  - 🇫🇷 **Français (Parité)**: **T**ravaux, **I**nventaire, **O**pérations & **N**otifications
- **Cross-Repo Ecosystem**: Keep references, navigation banners, and GitHub links aligned across all repositories (`immo-boussole`, `immo-boussole-extension`, `immo-boussole-orchestrator`, `immo-boussole.wiki`, `immo-tion`).
- **Organization Namespace**: Always use `https://github.com/Immo-Boussole/<repo>`.
- **Detailed Reference**: See [.agents/rules/documentation_and_i18n.md](.agents/rules/documentation_and_i18n.md).

---

## 5. GitHub Workflow Verification on Pushes & Pull Requests

- **Mandatory Workflow Monitoring**: After pushing code or creating/updating pull requests, always check the status of all triggered GitHub Actions workflows using `gh run list` / `gh run view` / `gh pr checks`.
- **Zero Failure Tolerance**: Never mark a task complete if any workflow job fails.
- **Detailed Reference**: See [.agents/rules/github_workflow_verification.md](.agents/rules/github_workflow_verification.md).

---

## 6. Response Formatting & Step Progress Tracking

- **Standardized Step Headers**: Every multi-step response or status update must begin with a Level 3 heading adhering to `### [X/Y] [EMOJI] [Descriptive Step Title]`.
- **Technology & Action Emojis**: Always prefix step titles with the corresponding Unicode emoji (e.g. 🐍 Python, 🧪 Tests, 🐳 Docker, 🐙 GitHub, ⚙️ CI/CD, 🌐 Frontend/Web, 📝 Docs/i18n, 🏠 Immo-Tion Domain).
- **Detailed Reference**: See [.agents/rules/step_progress_and_formatting.md](.agents/rules/step_progress_and_formatting.md).

---

## 7. Automatic Local Workspace Cleanup

- **Post-Action Cleanup**: After running test suites, ensure the root is clean of temporary test DB files (`test_*.db`), conflict files (`*[conflicted]*`), orphan journal files (`*.db-shm`, `*.db-wal`), and root `__pycache__` directories.
- Always use `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)` during automated test runs.
