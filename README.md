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

### 1. Standard Local Deployment

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

## 🛡️ Cloudflare Tunnel Exposure (`cloudflared`) & Zero Trust Security

Just like **Immo-Boussole**, **Immo-Tion** is natively designed to be exposed securely on the public Internet without opening any inbound ports on your router, firewall, or NAT.

### 🌐 Architectural Principles

- **Zero Open Ports**: The `cloudflared` daemon establishes an outbound encrypted tunnel directly to Cloudflare edge data centers. No external router port forwarding is needed.
- **Automatic SSL/TLS**: Cloudflare handles SSL termination, TLS 1.3 encryption, and valid certificates automatically.
- **Isolated Docker Bridge**: The application container (`immo-tion`) does not expose any host ports (`ports:` block omitted). External visitors can only reach Immo-Tion through the Cloudflare Tunnel.

### 📋 Deployment with Cloudflared

Two dedicated Compose manifests are provided:
1. **`docker-compose.hub.cloudflared.yml` (Recommended)**: Pulls the pre-built, multi-architecture image from Docker Hub (`wikijm/immo-tion:latest`).
2. **`docker-compose.cloudflared.yml`**: Compiles the application locally from the Dockerfile.

#### Stack Example (`docker-compose.hub.cloudflared.yml`)

```yaml
version: "3.8"

services:
  immo-tion:
    image: wikijm/immo-tion:latest
    container_name: immo-tion-app
    restart: always
    networks:
      - immo-tion-net
    environment:
      - APP_PORT=8085
      - DATA_DIR=/data
      - APP_ENV=production
      - REQUIRED_HEADERS="X-Origin-Verify:YOUR_SECRET_TOKEN,CF-Ray"
      - REQUIRED_HEADERS_EXEMPT_LOCALHOST=true
    volumes:
      - tion-data:/data

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: always
    command: tunnel run
    networks:
      - immo-tion-net
    environment:
      - TUNNEL_TOKEN=${TUNNEL_TOKEN}

networks:
  immo-tion-net:
    name: immo-tion-net
    driver: bridge

volumes:
  tion-data:
    name: immo-tion-data
```

---

### 🚀 Step-by-Step Cloudflare Zero Trust Setup

#### 1. Create a Cloudflare Tunnel
1. Log in to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
2. Navigate to **Networks** > **Tunnels** and click **Create a tunnel**.
3. Select **Cloudflared** as the connector and name it (e.g. `immo-tion-tunnel`).
4. Copy the installation token value (`TUNNEL_TOKEN`) for deployment.

#### 2. Configure Public Hostname Routing
1. In the tunnel configuration, go to the **Public Hostname** tab and click **Add a public hostname**.
2. Set your custom subdomain and domain:
   - **Subdomain**: `tion` (or your preferred prefix)
   - **Domain**: `your-domain.com`
3. Configure the service connection:
   - **Type**: `HTTP`
   - **URL**: `immo-tion:8085` (matches the Docker service name and internal port)
4. Click **Save hostname**.

#### 3. Enforce Origin Protection (Anti-Bypass Header Verification)
To ensure traffic cannot bypass Cloudflare's WAF and reach your origin directly:
1. In Cloudflare Tunnel settings > Public Hostname > **Additional application settings** > **HTTP Headers**:
   - Add header `X-Origin-Verify` with a private secret token (e.g. `X-Origin-Verify: your_custom_secret_key`).
2. In Immo-Tion's `.env` or Docker stack environment:
   ```ini
   REQUIRED_HEADERS="X-Origin-Verify:your_custom_secret_key,CF-Ray"
   REQUIRED_HEADERS_EXEMPT_LOCALHOST=true
   ```
3. Any direct HTTP request lacking this valid signature will be immediately rejected with HTTP `403 Forbidden`. Internal Docker health probes (`/health`) and localhost callers remain exempt.

#### 4. Zero Trust Access Control (Strongly Recommended)
Place Immo-Tion behind Cloudflare Access to restrict logins exclusively to authorized family members or collaborators:
1. In Cloudflare Zero Trust, navigate to **Access** > **Applications** > **Add an application**.
2. Select **Self-hosted**, name it `Immo-Tion Portal`, and specify `tion.your-domain.com`.
3. Create an **Allow Policy** restricted by email addresses (OTP PIN sent via email) or OAuth identity providers (Google, GitHub, Microsoft).

---

## ⚙️ Configuration & Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `8085` | Internal HTTP listening port for Uvicorn. |
| `APP_ENV` | `production` | Deployment mode (`production` or `development`). |
| `DATA_DIR` | `/data` (or `./data`) | Persistent storage path for the SQLite database and uploads. |
| `SECRET_KEY` | *(default)* | Secret key used for signing session cookies. |
| `REQUIRED_HEADERS` | *(empty)* | Comma-separated list of required headers (`Header-Name` or `Header-Name:Value`) to enforce Cloudflare origin verification. |
| `REQUIRED_HEADERS_EXEMPT_LOCALHOST` | `true` | When `true`, loopback callers (`127.0.0.1`, `::1`) are exempt from header enforcement. |
| `TUNNEL_TOKEN` | *(empty)* | Cloudflare Zero Trust tunnel authentication token for `cloudflared`. |
| `SMTP_HOST` | *(optional)* | SMTP server address for email notifications. |
| `SMTP_PORT` | `587` | SMTP port (e.g. 587 for STARTTLS, 465 for SSL). |
| `SMTP_USER` | *(optional)* | SMTP username/address. |
| `SMTP_PASSWORD` | *(optional)* | SMTP password or app-specific password. |
| `SMTP_FROM` | `notifications@immo-tion.local` | Sender address for automated notifications. |
| `SMTP_USE_TLS` | `true` | Enable STARTTLS for SMTP connections. |
| `WEBHOOK_URLS` | *(empty)* | Comma-separated list of webhook URLs for Home Assistant, Discord, or Telegram. |

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
