# 🏠 Immo-Tion

[![Build and Push Docker Image](https://github.com/Immo-Boussole/immo-tion/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/Immo-Boussole/immo-tion/actions/workflows/docker-publish.yml)
[![Docker Hub](https://img.shields.io/badge/docker-hub-blue.svg?logo=docker&logoColor=white)](https://hub.docker.com/r/wikijm/immo-tion)
[![Wiki Documentation](https://img.shields.io/badge/docs-GitHub%20Wiki-blue?logo=github)](https://github.com/Immo-Boussole/immo-boussole/wiki)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 🧭 **Immo-Boussole Organization**: [Core Web App](https://github.com/Immo-Boussole/immo-boussole) • [WebExtension](https://github.com/Immo-Boussole/immo-boussole-extension) • [Orchestrator](https://github.com/Immo-Boussole/immo-boussole-orchestrator) • [Central Wiki](https://github.com/Immo-Boussole/immo-boussole/wiki) • [Immo-Tion](https://github.com/Immo-Boussole/immo-tion)

---

## 🌐 Languages

- 🇬🇧 [English (Default)](README.md)
- 🇫🇷 [Français](README.fr.md)

---

## 💡 Concept & Identity

While **Immo-Boussole** guides buyers through hunting, scouting, and evaluating properties until acquisition, **Immo-Tion** takes over once the home is purchased to manage its entire lifecycle.

### What is "Immo-Tion"?
- **Emotion**: The deep emotional connection, pride, and care invested into your home.
- **E-motion** (*Electronic Motion*): A living, continuously moving and connected home where operations, renovations, and maintenance flow smoothly across years.
- **-tion**: Real estate in **action**, active maintenance, and ongoing asset valorization.

### The Official Acronym: **T.I.O.N.**
- 🇬🇧 **English (Default)**: **T**racking, **I**nventory, **O**perations & **N**otifications
- 🇫🇷 **Français (French Parity)**: **T**ravaux, **I**nventaire, **O**pérations & **N**otifications

---

## 🚀 The 5 Functional Pillars

1. **🛠️ Renovations & Works Tracking (Travaux / Tracking)**
   - Project and trade management (plumbing, electrical, insulation, decoration).
   - Quotes, down payments, final invoices, contractor directory, and ten-year warranty (*garantie décennale*) tracking.
   - Before / During / After visual photo logs.
   - Real-time capitalization of works for capital gain and actual cost basis calculations.

2. **📦 Equipment & Warranty Inventory (Inventaire / Inventory)**
   - Comprehensive catalog of appliances, HVAC systems, and home automation hardware.
   - Purchase dates, warranty expirations, model/serial numbers, and vendor links.
   - Attached PDF user manuals and digitized purchase receipts.
   - Spare parts and consumables tracking (VMC filters, water softener cartridges, lightbulbs).

3. **🔄 Periodic Maintenance Log (Opérations / Operations)**
   - Scheduled recurring operations: annual boiler/heat pump service, chimney sweeping, gutter cleaning, smoke detector testing.
   - Tamper-evident intervention history: date, technician, cost, and uploaded certificate/report.
   - Status indicators: 🟢 Up to date, 🟡 Due within 30 days, 🔴 Overdue / Critical.

4. **📑 Document Vault & Compliance**
   - Secure digital binder categorized by domain: Deeds & acquisition, Insurance contracts, Urban planning & cadastre, Utility contracts.
   - One-click export of the official **CIL** (*Carnet d'Information du Logement*) as a bundled PDF/ZIP dossier for notaries, insurers, and prospective future buyers.

5. **⚡ Utilities & Energy Monitoring**
   - Track electricity, water, gas, firewood, and wood pellet consumption over time.
   - Correlate energy savings before and after thermal insulation or heating upgrades.
   - Track theoretical and audited DPE energy efficiency ratings.

---

## 🔔 Proactive Notifications Hub

Immo-Tion never leaves maintenance to chance:
- **In-App Alerts**: Visual countdown badges and overdue task banners on the dashboard.
- **Calendar Sync**: Dynamic `.ics` feed seamlessly subscribed into Google Calendar, Apple Calendar, or Outlook.
- **Email Reminders (SMTP)**: Scheduled proactive alerts dispatched at Day -30 and Day -7 before critical deadlines.
- **Smart Home Webhooks**: JSON webhook dispatchers compatible with Home Assistant, Discord, or Telegram.

---

## 🔗 Immo-Boussole Bridge

Immo-Tion seamlessly connects with **Immo-Boussole**:
- **1-Click Export**: On any purchased listing in Immo-Boussole, trigger a direct transfer to Immo-Tion.
- **Automatic Import**: Land parcel reference, property dimensions, DPE energy ratings, initial photo gallery, agency/seller contacts, and inspected furniture/equipment inventories from `/v/{token}` are automatically initialized.

---

## 🐳 Quick Start with Docker

### Using Docker Compose (Recommended)

```yaml
version: "3.8"

services:
  immo-tion:
    image: wikijm/immo-tion:latest
    container_name: immo-tion
    restart: unless-stopped
    ports:
      - "8085:8085"
    environment:
      - APP_PORT=8085
      - DATA_DIR=/data
    volumes:
      - ./data:/data
```

Run:
```bash
docker compose up -d
```
Access the application at `http://localhost:8085`.

---

## 🛠️ Local Development Setup

```bash
# Clone the repository
git clone https://github.com/Immo-Boussole/immo-tion.git
cd immo-tion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the local server
uvicorn app.main:app --reload --port 8085
```

### Running Validation Tests
```bash
python tests/run_tests.py --ci
```

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.
