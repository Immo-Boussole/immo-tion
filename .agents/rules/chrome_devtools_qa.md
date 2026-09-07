---
description: Project rule to enforce automated QA, regression checks, security audits, and responsive validation using Chrome DevTools MCP
---

# Chrome DevTools MCP Quality Assurance, Security & Responsive Testing

This rule defines the mandatory validation protocol using the Chrome DevTools MCP for any modification to the user interface (UI), templates, CSS styles, JavaScript files, or frontend routes of **Immo-Tion**.

---

## 1. Triggers and Prerequisites

- **Triggers**: Any modification impacting visual rendering, frontend interactivity, accessibility, or client-side security.
- **Local Server**:
  - Check that the local development server is running (default: `http://localhost:8085` or configured port).
  - If the server is not running, start it in the background:
    ```powershell
    & ".\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8085
    ```
    Use `run_command` with `IsDaemon: true`.

---

## 2. Multi-Device Validation Protocol (Responsive Design)

In compliance with [responsive_design.md](.agents/rules/responsive_design.md):

1. **Test across a minimum of 3 viewports** using `resize_page` or `emulate`:
   - **Mobile**: $375 \times 667$ px or $390 \times 844$ px (verify collapsible sidebar overlay, property switcher dropdown, no horizontal overflow, touch targets $\ge 44$ px).
   - **Tablet**: $768 \times 1024$ px (verify grid/flexbox layouts and portrait/landscape adaptation).
   - **Desktop**: $1280 \times 800$ px and/or $1920 \times 1080$ px (verify 270px fixed sidebar, wide data tables, and timeline legibility).
2. **Visual Screenshots**:
   - Use `take_screenshot` across critical views to validate visual rendering:
     - Dashboard (`/`)
     - Inventory / Appliances (`/inventory`)
     - Renovations / CIL timeline (`/renovations`)
     - Maintenance log (`/maintenance`)
     - Profile (`/profile`) & Admin Settings (`/admin/settings`)
     - Setup Wizard (`/setup`) on clean instances

---

## 3. Regression Detection (Zero Error Policy)

1. **JavaScript Console**:
   - Call `list_console_messages` after navigating and interacting with modified components.
   - **Requirement**: Zero unhandled JavaScript errors (`console.error`, uncaught exceptions).
2. **Network & API Requests**:
   - Call `list_network_requests`.
   - **Requirement**: Zero unexpected HTTP error codes ($4\text{xx} / 5\text{xx}$), no missing static assets (CSS, JS, images, local FontAwesome & Inter fonts).

---

## 4. Security & Integrity Checks

1. **Auth & Setup Protection**:
   - Verify unauthenticated requests redirect cleanly to `/login` (or `/setup` if unconfigured).
   - Ensure authenticated session cookies are `HttpOnly; SameSite=Lax`.
   - Ensure the Bridge API Bearer token (`POST /api/v1/bridge/import-listing`) requires valid authorization (`401 Unauthorized` without token).
2. **Data & Secret Leaks**:
   - Ensure no sensitive information (raw passwords, password hashes, SMTP secrets, Bridge API tokens) is exposed in the console, DOM attributes, or JavaScript source.
3. **XSS & Injection Prevention**:
   - Verify that user inputs, property names, appliance notes, and renovation descriptions are consistently sanitized and escaped (Jinja2 autoescaping must be active).

---

## 5. Quality & Accessibility Audits (Lighthouse)

- Run `lighthouse_audit` on major modified pages.
- Verify Accessibility indicators (color contrast for dark theme `#0b0f1a` / `#131929` with accent `#4f46e5`, `aria` tags, semantic HTML) and Best Practices.

---

## 6. Corrective Actions & Reporting

- **Strict Blocking on Anomalies**: Any detected issue (console error, responsive glitch, network failure, auth bypass, or security risk) must be resolved immediately before completing the task.
- **Test Summary**: Summarize all verification steps and findings in the walkthrough or final task response.
