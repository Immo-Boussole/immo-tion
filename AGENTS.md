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
  - Maintain component legibility, accessibility, and responsiveness (modals, banners, forms, maintenance tables, asset cards, setup wizard).
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
  Ensure all tests (API, database, models, maintenance schedules, session auth, Jinja syntax, i18n parity) pass with **100% OK**.
- **Python 3.12+**: Prefer idiomatic, type-annotated Python. Use FastAPI with async route handlers.
- **SQLite WAL Mode**: Always ensure SQLite connections enable WAL mode (`PRAGMA journal_mode=WAL;`), foreign keys (`PRAGMA foreign_keys=ON;`), and avoid nested write transactions to prevent `database is locked` errors.
- **Security**: Never log, expose in API responses, or render in the UI any sensitive credentials (passwords, password hashes, session secrets, SMTP credentials, Bridge API tokens).

---

## 4. Frontend QA, Security & Responsive Validation via Chrome DevTools MCP

For any change affecting the UI, CSS, JavaScript, templates, or frontend routes:

- **Responsive Multi-Viewport Verification**: Test and capture screenshots across Mobile (e.g. $375\times 667$ px), Tablet (e.g. $768\times 1024$ px), and Desktop (e.g. $1280\times 800$ px) viewports using `resize_page` / `emulate` / `take_screenshot`. Ensure touch targets $\ge 44\text{px}$ and no horizontal overflow.
- **Regression Detection (Zero Error Policy)**: Verify with `list_console_messages` that there are 0 unhandled JS errors, and with `list_network_requests` that there are no unexpected HTTP $4\text{xx}/5\text{xx}$ errors or missing static assets (CSS, JS, fonts).
- **Security & Integrity**: Inspect console and DOM for CSP violations, security warnings, and sensitive data leakage. Ensure proper XSS sanitization via Jinja2 autoescaping.
- **Quality & Accessibility Audits**: Run `lighthouse_audit` on modified pages to check accessibility, performance, and best practices.
- **Detailed Reference**: See [.agents/rules/chrome_devtools_qa.md](.agents/rules/chrome_devtools_qa.md).

---

## 5. Agent Autonomy & Deployment Policy

- **Full Automation on Dev & Local**: The agent is authorized to execute all tasks autonomously without prompting for user confirmation (running tests, modifying files, creating commits, pushing to remote, and updating the **Dev** environment).
- **Environment Update Commands**:
  - **Dev update**:
    ```bash
    ssh immo-dev "sudo bash /opt/immo-tion/dev/scripts/auto_update.sh /opt/immo-tion/dev/ docker-compose.cloudflared.yml" --force
    ```
  - **Production update**:
    ```bash
    ssh immo-dev "sudo bash /opt/immo-tion/prod/scripts/auto_update.sh /opt/immo-tion/prod/ docker-compose.cloudflared.yml" --force
    ```
- **Post-Change Workflow**:
  - Once a code change is made, committed, and pushed:
    1. Propose / execute the **Dev** update command.
    2. Once local tests, GitHub Actions CI, and the Dev deployment are verified **OK**, propose and prompt the user to execute the **Production** update command (never auto-deploy to Production without user confirmation).
- **Detailed Reference**: See [.agents/rules/autonomy.md](.agents/rules/autonomy.md).

---

## 6. Documentation, Internationalization (i18n) & Cross-Repository Parity

- **English First & French Parity**: Write user-facing documentation in English first (`README.md`), and maintain exact parity in French (`README.fr.md`) in the same task/commit.
- **Acronym Integrity (T.I.O.N.)**:
  - 🇬🇧 **English (Default)**: **T**racking, **I**nventory, **O**perations & **N**otifications
  - 🇫🇷 **Français (Parité)**: **T**ravaux, **I**nventaire, **O**pérations & **N**otifications
- **Cross-Repo Ecosystem**: Keep references, navigation banners, and GitHub links aligned across all repositories (`immo-boussole`, `immo-boussole-extension`, `immo-boussole-orchestrator`, `immo-tion`, `immo-boussole.wiki`).
- **Organization Namespace**: Always use `https://github.com/Immo-Boussole/<repo>`.
- **Text & Structure**: Focus on text, tables, and diagrams; do not spend time generating new screenshots unless requested.
- **Detailed Reference**: See [.agents/rules/documentation_and_i18n.md](.agents/rules/documentation_and_i18n.md).

---

## 7. GitHub Workflow Verification on Pushes & Pull Requests

- **Mandatory Workflow Monitoring**: After pushing code or creating/updating pull requests, always check the status of all triggered GitHub Actions workflows using `gh run list` / `gh run view` / `gh pr checks`.
- **Zero Failure Tolerance**: Never mark a task complete if any workflow job fails (CI, Docker build, lint, quality checks, test suite, security scans).
- **Immediate Failure Resolution**: Inspect failure logs (`gh run view <run-id> --log-failed`), diagnose the root cause, apply fixes, commit and push, and monitor until all workflows are 100% green.
- **Detailed Reference**: See [.agents/rules/github_workflow_verification.md](.agents/rules/github_workflow_verification.md).

---

## 8. Response Formatting & Step Progress Tracking

- **Standardized Step Headers**: Every multi-step response or status update must begin with a Level 3 heading adhering to `### [X/Y] [EMOJI] [Descriptive Step Title]` (single square bracket pair around the fraction, e.g. `### [1/5] ...`, never double brackets like `[[1]/[5]]`).
- **Technology & Action Emojis**: Always prefix step titles with the corresponding Unicode emoji (e.g. 🐍 Python, 🧪 Tests, 🐳 Docker, 🐙 GitHub, ⚙️ CI/CD, 🌐 Frontend/Web, 🔍 Research, 📝 Docs/i18n, 🚀 Deploy/Release, 🛡️ Security, 🏠 Immo-Tion Domain).
- **Detailed Reference**: See [.agents/rules/step_progress_and_formatting.md](.agents/rules/step_progress_and_formatting.md).

---

## 9. Automatic Local Workspace Cleanup

- **Post-Action Cleanup**: After completing actions or running test suites, ensure the local project root is clean of temporary test DB files (`test_*.db`), cloud synchronization conflict files (`*[conflicted]*`), orphan SQLite journal files (`*.db-shm`, `*.db-wal`), and root `__pycache__` directories.
- **Isolated Test DB Locations**: Always configure tests to use `tempfile.TemporaryDirectory(ignore_cleanup_errors=True)` to prevent creating database files in the project root directory.
- **Detailed Reference**: See [.agents/rules/local_cleanup.md](.agents/rules/local_cleanup.md).
