---
description: Project rule to ensure all code and UI changes work seamlessly across desktop, tablet, and mobile screens
---

# Responsive Design & Multi-Device Compatibility

For every code or user interface (UI/UX) modification on **Immo-Tion**:

- **Multi-Resolution & Multi-Device Support**: Systematically ensure changes are fully responsive and function optimally across:
  - **PC / Desktop** (standard and widescreen displays)
  - **Tablets** (portrait and landscape orientations)
  - **Smartphones / Mobile Devices** (small screens, appropriate touch targets $\ge 44\text{px}$, smooth scrolling, no undesirable horizontal overflow). Users inspect appliances, crawl into basements, and photograph invoices directly with their smartphones!
- **Sidebar Architecture & Layout**:
  - Desktop ($> 768\text{px}$): Fixed 270px left sidebar with active navigation indicators and property context.
  - Mobile ($\le 768\text{px}$): Collapsible slide-over drawer with backdrop overlay, toggled via the hamburger button in the topbar.
- **Topbar & Active Property Context**:
  - Always keep the property switcher dropdown easily accessible in the topbar.
  - Quick action buttons (e.g. "+ Add Equipment", "+ Log Intervention", Profile/Logout) must wrap gracefully or collapse into touch-friendly icons on narrow viewports.
- **Data Tables & Timeline Cards**:
  - Appliance inventory, maintenance logs, and CIL renovation timelines must stack into readable card layouts or horizontally scrollable containers on mobile devices.
- **Modals & Dialogs**:
  - Modals (add equipment, edit warranty, log maintenance intervention) must adapt to full-screen or near-full-screen on mobile viewports with sticky header and footer action buttons.
  - Touch targets for form inputs, dropdowns, and buttons must be at least $44 \times 44\text{px}$.
- **Setup Wizard (`/setup`)**:
  - Multi-step setup wizard must remain perfectly centered, legible, and functional across both small smartphone screens and wide desktop displays.
