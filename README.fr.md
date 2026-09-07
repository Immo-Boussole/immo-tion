# 🏠 Immo-Tion

[![Build and Push Docker Image](https://github.com/Immo-Boussole/immo-tion/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/Immo-Boussole/immo-tion/actions/workflows/docker-publish.yml)
[![Docker Hub](https://img.shields.io/badge/docker-hub-blue.svg?logo=docker&logoColor=white)](https://hub.docker.com/r/wikijm/immo-tion)
[![Documentation Wiki](https://img.shields.io/badge/docs-GitHub%20Wiki-blue?logo=github)](https://github.com/Immo-Boussole/immo-boussole/wiki)
[![Licence : GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 🧭 **Organisation Immo-Boussole** : [Application Principale](https://github.com/Immo-Boussole/immo-boussole) • [Extension Web](https://github.com/Immo-Boussole/immo-boussole-extension) • [Orchestrateur](https://github.com/Immo-Boussole/immo-boussole-orchestrator) • [Wiki Central](https://github.com/Immo-Boussole/immo-boussole/wiki) • [Immo-Tion](https://github.com/Immo-Boussole/immo-tion)

---

## 🌐 Langues

- 🇬🇧 [English (Par défaut)](README.md)
- 🇫🇷 [Français](README.fr.md)

---

## 💡 Concept & Identité

Alors qu'**Immo-Boussole** accompagne les acquéreurs dans la recherche, la veille et l'évaluation des biens jusqu'à l'achat, **Immo-Tion** prend le relais dès l'acquisition pour piloter l'intégralité du cycle de vie du logement.

### Que signifie "Immo-Tion" ?
- **Emotion (Émotion)** : L'attachement affectif, la fierté et le soin consacrés à son lieu de vie.
- **E-motion** (*Electronic Motion*) : Un habitat vivant, connecté et en perpétuel mouvement où entretien, rénovations et améliorations s'enchaînent harmonieusement.
- **-tion** : L'immobilier en **action**, en exploitation continue et en valorisation patrimoniale.

### L'Acronyme Officiel : **T.I.O.N.**
- 🇬🇧 **English (Prioritaire)** : **T**racking, **I**nventory, **O**perations & **N**otifications
- 🇫🇷 **Français (Parité)** : **T**ravaux, **I**nventaire, **O**pérations & **N**otifications

---

## 🚀 Les 5 Piliers Fonctionnels

1. **🛠️ Suivi de Travaux & Rénovations (Travaux / Tracking)**
   - Gestion des chantiers et des corps de métier (plomberie, électricité, isolation, décoration).
   - Devis, acomptes, factures acquittées, répertoire des artisans et suivi des garanties décennales.
   - Journal visuel avant / pendant / après avec photos horodatées.
   - Capitalisation en direct des travaux pour le calcul de la plus-value et du coût réel du bien.

2. **📦 Inventaire des Équipements & Garanties (Inventaire / Inventory)**
   - Catalogue exhaustif de l'électroménager, du système de chauffage/PAC et de la domotique.
   - Dates d'achat, fin de garantie constructeur, numéros de modèle et de série.
   - Archivage numérique des notices PDF et tickets de caisse.
   - Références des consommables et pièces d'usure (filtres VMC, cartouches adoucisseur, ampoules).

3. **🔄 Carnet d'Entretien Récurrent (Opérations / Operations)**
   - Planification des révisions obligatoires et périodiques : chaudière, ramonage, démoussage toiture, détecteurs de fumée.
   - Historique infalsifiable des interventions : date, intervenant, coût et certificat/rapport téléversé.
   - Indicateurs visuels : 🟢 À jour, 🟡 À planifier sous 30 jours, 🔴 En retard / Urgent.

4. **📑 Coffre-fort Documentaire & Conformité**
   - Classement numérique sécurisé par thématique : Acte notarié, Assurances, Urbanisme & cadastre, Contrats d'énergie.
   - Export 1-clic du **CIL** (*Carnet d'Information du Logement*) sous forme de dossier PDF/ZIP certifié pour le notaire, les assureurs ou les futurs acquéreurs.

5. **⚡ Suivi des Consommations & Énergie**
   - Relevés de consommations d'électricité, d'eau, de gaz, de bois et de granulés.
   - Corrélation des économies réalisées avant et après rénovation énergétique.
   - Suivi de l'étiquette DPE théorique et réelle post-travaux.

---

## 🔔 Hub de Notifications Proactif

Immo-Tion ne laisse aucune place aux oublis :
- **Alertes In-App** : Badges et bandeaux d'échéances prioritaires directement sur le tableau de bord.
- **Synchronisation Agenda** : Flux `.ics` dynamique synchronisable avec Google Calendar, Apple Calendar ou Outlook.
- **Rappels Email (SMTP)** : Relances automatiques programmées à J-30 et J-7 avant chaque échéance critique.
- **Webhooks Domotiques** : Émission de notifications JSON vers Home Assistant, Discord ou Telegram.

---

## 🔗 Passerelle Immo-Boussole

Immo-Tion s'interconnecte naturellement avec **Immo-Boussole** :
- **Export 1-Clic** : Sur la fiche de tout bien marqué comme *Acheté* dans Immo-Boussole, transférez instantanément le dossier vers Immo-Tion.
- **Initialisation Automatique** : Parcelle cadastrale, surfaces, étiquette DPE, galerie photos, coordonnées du notaire/agence et inventaire mobilier issu de `/v/{token}` sont automatiquement importés.

---

## 🐳 Démarrage Rapide avec Docker

### 1. Déploiement Local Standard

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

Lancer :
```bash
docker compose up -d
```
L'application est accessible sur `http://localhost:8085`.

---

## 🛡️ Exposition via Cloudflare Tunnel (`cloudflared`) & Sécurité Zero Trust

Tout comme **Immo-Boussole**, **Immo-Tion** est nativement conçu pour être exposé sur Internet en toute sécurité, sans ouvrir le moindre port entrant sur votre box, routeur ou pare-feu (pas de redirection NAT/PAT).

### 🌐 Principes d'Architecture

- **Zéro Port Ouvert** : Le connecteur `cloudflared` établit un tunnel sortant chiffré vers les centres de données Cloudflare. Aucune ouverture de port public n'est requise.
- **SSL/TLS Automatique** : Cloudflare assure la terminaison HTTPS, le chiffrement TLS 1.3 et le renouvellement automatique des certificats.
- **Réseau Docker Isolé** : Le conteneur applicatif (`immo-tion`) n'expose aucun port sur la machine hôte (bloc `ports:` omis). L'application n'est accessible que via le réseau Docker interne ou le Tunnel Cloudflare.

### 📋 Déploiement avec Cloudflared

Deux fichiers Compose prêts à l'emploi sont fournis :
1. **`docker-compose.hub.cloudflared.yml` (Recommandé)** : Télécharge l'image multi-architecture pré-construite depuis Docker Hub (`wikijm/immo-tion:latest`).
2. **`docker-compose.cloudflared.yml`** : Compile l'application localement depuis le Dockerfile.

#### Exemple de Stack (`docker-compose.hub.cloudflared.yml`)

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
      - REQUIRED_HEADERS="X-Origin-Verify:VOTRE_SECRET_PRIVE,CF-Ray"
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

### 🚀 Configuration Étape par Étape (Cloudflare Zero Trust)

#### 1. Créer le Tunnel Cloudflare
1. Connectez-vous sur le [Tableau de bord Cloudflare Zero Trust](https://one.dash.cloudflare.com/).
2. Rendez-vous dans **Networks** > **Tunnels** et cliquez sur **Create a tunnel**.
3. Choisissez **Cloudflared** comme connecteur et donnez un nom à votre tunnel (ex: `immo-tion-tunnel`).
4. Copiez la valeur du jeton d'installation (`TUNNEL_TOKEN`) pour votre déploiement.

#### 2. Configurer le Nom d'Hôte Public (Public Hostname)
1. Dans la configuration du tunnel, allez dans l'onglet **Public Hostname** et cliquez sur **Add a public hostname**.
2. Renseignez votre sous-domaine et nom de domaine :
   - **Sous-domaine** : `tion` (ou le préfixe de votre choix)
   - **Domaine** : `votre-domaine.com`
3. Configurez la cible de service :
   - **Type** : `HTTP`
   - **URL** : `immo-tion:8085` (correspond au nom de service Docker et au port interne)
4. Cliquez sur **Save hostname**.

#### 3. Activer la Protection d'Origine (Vérification Anti-Contournement)
Pour vous assurer que le trafic ne contourne jamais le pare-feu Cloudflare :
1. Dans Cloudflare Zero Trust > Tunnels > Éditer votre nom d'hôte > **Additional application settings** > **HTTP Headers** :
   - Ajoutez l'en-tête `X-Origin-Verify` avec un secret privé (ex: `X-Origin-Verify: mon_secret_personnalise`).
2. Dans le fichier `.env` d'Immo-Tion ou dans les variables d'environnement de votre stack Docker :
   ```ini
   REQUIRED_HEADERS="X-Origin-Verify:mon_secret_personnalise,CF-Ray"
   REQUIRED_HEADERS_EXEMPT_LOCALHOST=true
   ```
3. Toute requête directe ne disposant pas de ces en-têtes valides sera rejetée avec un code HTTP `403 Forbidden`. Les sondes de santé internes Docker (`/health`) et les appels locaux restent autorisés.

#### 4. Contrôle d'Accès Zero Trust (Fortement Conseillé)
Placez Immo-Tion derrière un portail captif Cloudflare Access afin que seules les personnes autorisées puissent voir l'application :
1. Dans Cloudflare Zero Trust, allez dans **Access** > **Applications** > **Add an application**.
2. Choisissez **Self-hosted**, nommez l'application `Portail Immo-Tion`, et entrez `tion.votre-domaine.com`.
3. Créez une règle **Allow** restreinte par adresses e-mail (code PIN OTP reçu par e-mail) ou fournisseur d'identité (Google, GitHub, Microsoft).

---

## ⚙️ Configuration & Variables d'Environnement

| Variable | Défaut | Description |
|---|---|---|
| `APP_PORT` | `8085` | Port HTTP d'écoute interne pour Uvicorn. |
| `APP_ENV` | `production` | Environnement d'exécution (`production` ou `development`). |
| `DATA_DIR` | `/data` (ou `./data`) | Chemin persistant de stockage pour SQLite et les fichiers téléversés. |
| `SECRET_KEY` | *(défaut)* | Clé secrète de signature des sessions de navigation. |
| `REQUIRED_HEADERS` | *(vide)* | Liste d'en-têtes requis (`Nom-Header` ou `Nom-Header:Valeur`) pour la vérification d'origine Cloudflare. |
| `REQUIRED_HEADERS_EXEMPT_LOCALHOST` | `true` | Si `true`, exempte les requêtes en boucle locale (`127.0.0.1`, `::1`) de la vérification des en-têtes. |
| `TUNNEL_TOKEN` | *(vide)* | Jeton d'authentification du tunnel Cloudflare Zero Trust pour `cloudflared`. |
| `SMTP_HOST` | *(optionnel)* | Adresse du serveur SMTP pour les notifications par e-mail. |
| `SMTP_PORT` | `587` | Port SMTP (ex: 587 pour STARTTLS, 465 pour SSL). |
| `SMTP_USER` | *(optionnel)* | Identifiant ou adresse expéditrice SMTP. |
| `SMTP_PASSWORD` | *(optionnel)* | Mot de passe SMTP ou mot de passe d'application. |
| `SMTP_FROM` | `notifications@immo-tion.local` | Adresse expéditrice affichée pour les alertes automatiques. |
| `SMTP_USE_TLS` | `true` | Active la négociation STARTTLS pour les échanges SMTP. |
| `WEBHOOK_URLS` | *(vide)* | Liste d'URLs séparées par des virgules pour Home Assistant, Discord ou Telegram. |

---

## 🛠️ Installation en Développement Local

```bash
# Cloner le dépôt
git clone https://github.com/Immo-Boussole/immo-tion.git
cd immo-tion

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Sous Windows : venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Démarrer le serveur local
uvicorn app.main:app --reload --port 8085
```

### Exécution des Tests de Validation
```bash
python tests/run_tests.py --ci
```

---

## 📄 Licence

Ce projet est sous licence **GNU General Public License v3.0** - voir le fichier [LICENSE](LICENSE) pour plus de détails.
