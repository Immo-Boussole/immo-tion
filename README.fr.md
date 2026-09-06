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

### Utilisation de Docker Compose (Recommandé)

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
