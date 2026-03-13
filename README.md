# 🏥 SCRIBE — Main courante de crise hospitalière

> **Outil open-source de gestion opérationnelle des crises cyber et sanitaires pour les établissements de santé français.**

[![Licence: Libre](https://img.shields.io/badge/licence-libre-brightgreen)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com)
[![Réseau isolé](https://img.shields.io/badge/réseau-isolé%20compatible-orange)](#déploiement)
[![NIS2](https://img.shields.io/badge/conformité-NIS2%20%7C%20CERT%20Santé-red)](#conformité-réglementaire)

---

## Pourquoi SCRIBE ?

Lors d'une crise cyber ou sanitaire à l'hôpital, les équipes font face à un problème constant : **la perte de traçabilité**. Les décisions sont prises oralement, les chronologies se reconstituent de mémoire, les consignes de relève s'échangent par SMS, et le rapport post-incident mobilise des jours de travail.

SCRIBE résout ce problème en fournissant une **main courante numérique centralisée**, accessible depuis n'importe quel poste du réseau interne, qui fonctionne même en cas de panne des systèmes d'information principaux.

**Conçu par des professionnels de la sécurité des SI hospitaliers**, SCRIBE est calibré pour les contraintes réelles du terrain : réseau parallèle isolé, absence d'Active Directory, personnel non-technique en salle de crise, obligations réglementaires NIS2 et CERT Santé.

---

## Table des matières

- [Capture d'écran](#aperçu)
- [Fonctionnalités](#fonctionnalités-détaillées)
- [Déploiement en 5 minutes](#déploiement-en-5-minutes)
- [Configuration établissement](#configuration-établissement)
- [Intelligence artificielle](#intelligence-artificielle-configurable)
- [Architecture technique](#architecture-technique)
- [Conformité réglementaire](#conformité-réglementaire)
- [Feuille de route](#feuille-de-route)

---

## Aperçu

```
┌─────────────────────────────────────────────────────────────────┐
│  🏥 SCRIBE v6  [CHU]     14:56  📥 Inbox(3)  🌙  ⏻             │
├──────┬────────┬─────────┬────────┬─────┬─────────┬─────────────┤
│VEILLE│ SOINS  │ CELLULE │ KANBAN │ REX │ RELÈVE  │  ANNUAIRE   │
├──────┴────────┴─────────┴────────┴─────┴─────────┴─────────────┤
│  DÉCLARATION D'INCIDENT          │  Carte des sites             │
│  Type : [CYBER] [SANITAIRE]      │  ○ Site principal            │
│  Directeur de crise : …          │  ● Site secondaire (alerte)  │
│  Site / UF : …                   │                              │
│  Fait – Quoi ? : …               ├──────────────────────────────│
│  Analyse – Impact ? : …          │  1 TOTAL  │ 0 CRITIQUE       │
│  Jalons de résolution : ✓ …      │  1 OUVERT │ 1 CYBER          │
│  [🔴 DIFFUSER]  [🤖 ALBERT]      │  [ANALYSE GLOBALE][CSV]      │
└──────────────────────────────────┴──────────────────────────────┘
```

---

## Fonctionnalités détaillées

### 🌐 Onglet VEILLE — Main courante principale

La colonne vertébrale de SCRIBE. C'est ici que se construit la chronologie horodatée de la crise.

**Déclaration d'incident**
- Saisie guidée : type de crise (Cyber / Sanitaire / Mixte), niveau d'urgence (1 Veille → 4 Critique), site, unité fonctionnelle
- Champ *Fait* (description factuelle) séparé du champ *Analyse* (impact et systèmes affectés) — distinction essentielle pour les rapports ANSSI/CERT Santé
- Moyens engagés et coordonnées de l'intervenant
- **Jalons de résolution** : boutons prédéfinis (Passé d'ordi, DSI contacté, RSSI alerté, Cellule activée, CERT Santé, Isolation réseau, Sauvegarde OK, Retour normal) + jalons personnalisés ; chaque jalon est horodaté au clic
- Projection de résolution estimée avec compte à rebours en temps réel
- Pièces jointes : captures d'écran, logs, documents (PDF, images, tout format)
- Demande d'avis IA au moment de la déclaration

**Timeline des incidents**
- Affichage en temps réel, rafraîchissement automatique toutes les 12 secondes
- Code couleur par niveau d'urgence : bleu (veille) → orange (alerte) → rouge (crise) → noir (critique)
- Progression des jalons par barre de pourcentage sur chaque fiche
- Pièces jointes visibles directement sur la fiche (chips cliquables)
- Numéro d'incident `#ID` affiché pour référencement croisé
- Barre de filtres : par site, par directeur, par urgence, par statut, par type
- Changement de statut en un clic (Signalé → En cours → Résolu)
- Horodatage automatique de la résolution
- Actions rapides depuis chaque fiche : 🤖 Demander l'avis IA, 📎 Ajouter PJ, 📋 Créer tâche Kanban, 📄 Générer REX, 🗑 Supprimer

**KPIs en temps réel**
- Total incidents, Critiques, Ouverts, Cyber, Sanitaires
- Indicateur de niveau global : VEILLE NORMALE → ALERTE → CRISE → CRITIQUE (calculé automatiquement)

**Carte géographique**
- Carte OpenStreetMap avec marqueurs sur les sites de l'établissement
- Code couleur dynamique selon le niveau d'alerte de chaque site
- Auto-zoom vers le site le plus critique
- Panneau redimensionnable à la souris
- Intégration *La Suite Numérique* : boutons VISIO (visio.numerique.gouv.fr) et PAD

**Filtres et recherche**
- Filtrage multicritères combinable : site, directeur de crise, urgence, statut, type
- Export CSV de toute la main courante (horodaté, compatible tableur)

---

### 🏥 Onglet SOINS — Impact sur les unités de soins

Vision transversale de l'impact sur les pôles cliniques, indispensable en crise sanitaire ou lors d'une panne SI affectant les soins.

**Vue par pôle**
- Toutes les unités fonctionnelles regroupées par pôle (Urgences, Chirurgie, Réanimation, Maternité, Imagerie…)
- Saisie de l'état de chaque unité : Nominal / Dégradé / Critique / Fermé
- Compteur de patients présents par UF
- Commentaire libre par UF
- Horodatage automatique de chaque mise à jour

**Timeline de projection**
- Visualisation Gantt des estimations de retour à la normale par service
- Horizon temporel glissant (6h, 24h, 72h)
- Indicateur visuel des UF dont la résolution estimée est dépassée

**Dashboard de synthèse**
- Nombre total de pôles impactés, patients concernés
- Pourcentage de l'activité en mode nominal vs dégradé
- Résumé transmis automatiquement à l'analyse IA globale

---

### ⚖️ Onglet CELLULE — Registre de la cellule de crise

La cellule de crise doit pouvoir justifier a posteriori chaque décision prise. Cet onglet constitue le **registre officiel** de la cellule.

**Registre des présences**
- Entrées et sorties horodatées automatiquement
- Nom, fonction, action (entrée/sortie/remplacement)
- Historique complet consultable et exportable

**Chronologie décisionnelle**
- Saisie horodatée de chaque décision prise en cellule
- Champ *Responsable* de l'exécution
- Référence réglementaire associée (Plan Blanc, ORSAN, PCA, NIS2…)
- Statut de validation (Validé / En attente / Annulé)
- Numérotation séquentielle automatique

**Analyse IA globale** (bouton ANALYSE GLOBALE)
- Synthèse de la situation basée sur tous les incidents ouverts + décisions prises + état des pôles
- Évaluation proportionnée au niveau réel (pas de catastrophisme sur un incident mineur)
- Actions prioritaires recommandées
- Points de vigilance et risques d'escalade

---

### 📋 Onglet KANBAN — Gestion des tâches opérationnelles

En crise, les actions à mener se multiplient. Le tableau Kanban permet de les distribuer, les suivre et les prioriser sans perte d'information.

**Tableau en 4 colonnes**
- BACKLOG → EN COURS → EN ATTENTE → TERMINÉ
- Drag & drop natif entre les colonnes
- Mise à jour en temps réel pour tous les utilisateurs connectés

**Cartes de tâche**
- Titre, description détaillée
- **Lien vers l'incident source** (sélecteur avec liste des incidents ouverts, triés par urgence)
- Assignation à un nom/fonction
- Priorité : Critique (violet), Haute (rouge), Normale (jaune), Basse (vert)
- Date d'échéance avec alerte visuelle si dépassée
- Création rapide depuis une fiche incident en un clic (bouton 📋)

**Depuis chaque incident**
- Bouton de création rapide 📋 qui ouvre le Kanban avec le titre et le lien incident pré-remplis

---

### 📊 Onglet REX — Retour d'expérience

Le REX (Retour d'Expérience) est une obligation réglementaire et un outil de capitalisation. SCRIBE le rend accessible à tous, même sans formation spécifique.

**Formulaire en langage naturel (3 étapes)**
- *Étape 1 – Informations générales* : Quel incident ? Quel type ? Qui rédige ?
- *Étape 2 – Chronologie* : Quand avez-vous su qu'il y avait un problème ? (délai de détection en h/min) — Combien de temps pour résoudre ? (en h/min) — Combien de services impactés ? — Étapes réalisées sur prévues
- *Étape 3 – Bilan* : Ce qui a bien fonctionné / Ce qui peut être amélioré / Actions concrètes / Message principal à retenir

> Le jargon MTTD/MTTR est converti automatiquement depuis la saisie en heures/minutes. L'utilisateur ne voit jamais d'acronyme technique.

**Pré-remplissage automatique depuis un incident**
- Bouton 📄 sur chaque fiche → ouvre le REX avec durée, jalons, type pré-remplis depuis les données de la main courante

**Dashboard REX**
- KPIs agrégés : nombre total de REX, MTTR moyen, MTTD moyen, % jalons complétés
- Graphique de répartition par type de crise (barres)
- Fiches REX avec tags visuels (points positifs, axes d'amélioration, actions)
- Filtrage par type, par date, par rédacteur

**Export rapport DOCX**
- Rapport de clôture complet en Word (.docx) généré automatiquement pour chaque incident
- Contient : page de garde (référence, dates, site, urgence, directeur, statut), description complète, chronologie des jalons, registre des décisions, liste des présences, consignes de relève, avis IA, métriques (durée, jalons %, décisions)
- Pied de page horodaté et marqué CONFIDENTIEL
- Compatible avec les modèles de rapport CERT Santé et ANSSI

---

### 🔄 Onglet RELÈVE — Passation entre équipes

La relève est un moment critique où l'information se perd. SCRIBE la formalise.

**Consignes de relève**
- Rédaction libre d'une consigne destinée à une personne / un poste
- Horodatage automatique à la création
- **Accusé de réception** : la personne qui prend la relève clique "Accusé" — horodaté et enregistré
- Historique complet de toutes les consignes de la crise
- Impossibilité de modifier une consigne après accusé de réception (intégrité)

---

### 📞 Onglet ANNUAIRE — Téléphonie de crise

En crise cyber, le système téléphonique IP peut être hors service. L'annuaire de secours est critique.

**Double annuaire**
- **Annuaire nominal** : numéros IP/VoIP/DECT du réseau téléphonique habituel
- **Annuaire de secours** : GSM personnels, fixes cuivre, numéros d'astreinte — utilisables en cas de panne totale du système de téléphonie
- Bascule en un clic entre les deux modes
- Chargé depuis `config.xml` — aucune donnée hardcodée
- Contacts : service, localisation, numéro, note
- Inclut par défaut SAMU 15, Pompiers 18, CERT Santé, ANSSI

---

### 🔐 Authentification et gestion des utilisateurs

**Système d'authentification local**
- Aucune dépendance LDAP / Active Directory — fonctionne sur réseau isolé
- JWT (JSON Web Token) HS256, durée de session configurable (12h par défaut)
- Hash SHA-256 des mots de passe

**Rôles utilisateurs**
- **Admin** : accès complet, gestion des utilisateurs, panneau d'administration
- **Directeur** : accès complet à toutes les fonctionnalités opérationnelles
- **Observateur** : lecture seule (pour les invités, autorités de tutelle, etc.)

**Gestion des périmètres**
- Un directeur peut être limité à un site ou un périmètre spécifique
- Les notifications lui sont envoyées uniquement pour les incidents de son périmètre

**Panneau d'administration** (role admin)
- CRUD complet des utilisateurs (création, modification, désactivation)
- Attribution des rôles et périmètres
- Accessible via l'icône utilisateur en haut à droite

---

### 🔔 Système de notifications

- Badge rouge non-lu dans le header, mis à jour toutes les 15 secondes
- Panneau Inbox glissant : liste chronologique des notifications
- Types : INCIDENT (nouvel incident déclaré), TÂCHE (assignation Kanban), SYSTÈME
- Marquage individuel ou global "tout lire"
- Clic sur une notification → navigation directe vers l'incident concerné
- Notifications de périmètre : les directeurs ne reçoivent que les incidents de leur site

---

### 🧠 Intelligence artificielle (7 fournisseurs)

L'IA assiste les décideurs sans se substituer à eux. Toutes les analyses sont indicatives et proportionnées au niveau réel de la situation.

**Analyse d'incident individuel**
- Niveau d'alerte recommandé (VEILLE / ALERTE / CRISE / CRITIQUE)
- Actions prioritaires numérotées
- Organismes à notifier (CERT Santé, ANSSI, ARS, etc.)
- Niveau de risque avec justification

**Analyse de situation globale**
- Synthèse de tous les incidents ouverts + décisions prises + état des pôles
- Niveau global calculé proportionnellement (pas de sur-alerte sur incidents mineurs)
- Actions prioritaires adaptées au contexte réel
- Points de vigilance et risques d'escalade

**Fournisseurs configurables** (choix dans `config.xml`) :

| Fournisseur | Description | Données sortantes |
|---|---|---|
| 🇫🇷 **Albert** (défaut) | IA souveraine DINUM/Etalab | Serveurs gouvernementaux FR |
| 🤖 **OpenAI** | ChatGPT (GPT-4o, GPT-4o-mini…) | Serveurs OpenAI US |
| 🟤 **Anthropic** | Claude (Haiku, Sonnet, Opus…) | Serveurs Anthropic US |
| 🔷 **Google Gemini** | Gemini 2.0 Flash, 1.5 Pro… | Serveurs Google |
| 🌪️ **Mistral AI** | mistral-small, mistral-large… | Serveurs Mistral FR |
| 🏠 **Ollama** | Modèle local (llama3, phi3…) | **Aucune — 100% local** |
| ⚙️ **OpenAI-compat** | LM Studio, vLLM, Jan… | **Aucune — 100% local** |

> Pour les établissements sur réseau totalement isolé, le mode **Ollama** permet une IA entièrement locale, sans aucune donnée qui sort du SI.

Le badge du fournisseur actif est affiché dans le header de l'interface.

---

### 🗺️ Cartographie multi-sites

- Carte OpenStreetMap (fonctionne hors Internet via tiles mis en cache ou serveur de tuiles interne)
- Marqueurs colorés par niveau d'alerte : vert (nominal), orange (alerte), rouge (crise)
- Auto-zoom dynamique vers le site le plus critique
- Panneau redimensionnable par drag vertical (80px → 500px)
- Données GPS configurées dans `config.xml`

---

### 🎨 Interface et ergonomie

- **Mode sombre / clair** : bascule via le bouton 🌙/☀️ dans le header, mémorisé entre les sessions
- Single Page Application : aucune navigation, aucun rechargement, temps de réponse < 100ms
- Polices monospace pour les données critiques (timestamps, IDs, statuts)
- Code couleur cohérent sur toute l'interface : urgences, types, priorités
- Responsive : fonctionne sur grand écran (salle de crise) comme sur portable

---

## Déploiement en 5 minutes

### Prérequis

- Python 3.9 ou supérieur (`python --version`)
- Aucune base de données externe (SQLite embarqué)
- Aucune connexion Internet requise en fonctionnement (la carte utilise OpenStreetMap, désactivable)

### Installation

```bash
# 1. Décompresser l'archive
unzip scribe_open.zip
cd scribe_open

# 2. Installer les dépendances Python
pip install -r requirements.txt

# 3. Configurer votre établissement (ouvrir config.xml dans un éditeur)
# → Voir section "Configuration établissement" ci-dessous

# 4. Initialiser
python setup.py

# 5. Démarrer
python main.py
```

Ouvrez **http://localhost:8000** dans votre navigateur.

### Accès réseau

Pour rendre SCRIBE accessible à tous les postes de la salle de crise :

```bash
python main.py --host 0.0.0.0 --port 8000
```

Les autres postes accèdent via `http://[IP-du-serveur]:8000`.

### Démarrage en production (service systemd)

```ini
# /etc/systemd/system/scribe.service
[Unit]
Description=SCRIBE Main courante hospitalière
After=network.target

[Service]
WorkingDirectory=/opt/scribe
ExecStart=/usr/bin/python3 main.py --host 0.0.0.0 --port 8000
Restart=always
User=scribe

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable scribe
systemctl start scribe
```

---

## Configuration établissement

Tout se configure dans **`config.xml`** — c'est le seul fichier à modifier.

### Structure du fichier

```xml
<scribe>
  <etablissement>
    <nom>Centre Hospitalier de Votre Ville</nom>
    <sigle>CHVV</sigle>
    <finess>000000000</finess>
  </etablissement>

  <admin>
    <login>dircrise</login>
    <password>VotreMotDePasse!</password>   <!-- À changer après la 1ère connexion -->
  </admin>

  <sites>
    <site>
      <nom>Site Principal</nom>
      <adresse>1 avenue de l'Hôpital, 00000 Ville</adresse>
      <latitude>48.8566</latitude>    <!-- maps.google.fr → clic droit → coordonnées -->
      <longitude>2.3522</longitude>
      <telephone_garde>01 00 00 00 00</telephone_garde>
    </site>
    <!-- autant de sites que nécessaire -->
  </sites>

  <directeurs>
    <directeur>
      <nom>M. Prénom NOM</nom>
      <fonction>Directeur Général</fonction>
      <abreviation>DG</abreviation>
    </directeur>
    <!-- ... -->
  </directeurs>

  <unites_fonctionnelles site="Site Principal">
    <uf code="1001" pole="URGENCES">Urgences adultes</uf>
    <uf code="4001" pole="SOINS CRITIQUES">Réanimation</uf>
    <!-- ... -->
  </unites_fonctionnelles>

  <annuaire_normal>
    <contact service="URGENCES — IOA" local="Accueil urgences" tel="5100"/>
    <!-- ... -->
  </annuaire_normal>

  <annuaire_secours>
    <contact service="CADRE DE NUIT — SECOURS" local="GSM cadre" tel="06 00 00 00 04" note=""/>
    <!-- ... -->
  </annuaire_secours>

  <ia>
    <fournisseur>albert</fournisseur>   <!-- albert | openai | anthropic | gemini | mistral | ollama -->
    <cle_api></cle_api>                 <!-- Clé API du fournisseur -->
    <modele></modele>                    <!-- Laisser vide = modèle par défaut -->
  </ia>
</scribe>
```

### Import des UF depuis FICOM

Si votre établissement dispose d'un export Excel FICOM :

```bash
# Placer le fichier uf.xlsx à la racine du projet
python import_uf2.py
```

Cela remplace la saisie manuelle des UF dans `config.xml`.

### Relancer après modification

```bash
python setup.py    # recharge sites, UF, directeurs, annuaires, config IA
# Les données (incidents, décisions, REX) sont préservées
```

---

## Intelligence artificielle configurable

### Changer de fournisseur

Modifiez `config.xml` :

```xml
<ia>
  <fournisseur>openai</fournisseur>
  <cle_api>sk-proj-votre-clé</cle_api>
  <modele>gpt-4o-mini</modele>
</ia>
```

Puis `python setup.py`. Aucune modification de code nécessaire.

### Fonctionnement sans Internet (Ollama)

```bash
# Installer Ollama : https://ollama.ai
ollama pull llama3
```

```xml
<ia>
  <fournisseur>ollama</fournisseur>
  <modele>llama3</modele>
</ia>
```

Aucune donnée ne quitte le SI. Idéal pour les établissements sur réseau totalement isolé.

### Variables d'environnement (surpassent config.xml)

```bash
export SCRIBE_IA_PROVIDER=anthropic
export SCRIBE_IA_KEY=sk-ant-...
export SCRIBE_IA_MODEL=claude-haiku-4-5-20251001
python main.py
```

---

## Architecture technique

### Stack

| Composant | Technologie |
|---|---|
| Backend | Python 3.9+ / FastAPI / SQLAlchemy |
| Base de données | SQLite (embarqué, fichier `scribe.db`) |
| Frontend | HTML5 / CSS3 / JavaScript vanilla (SPA) |
| Carte | Leaflet.js + OpenStreetMap |
| Authentification | JWT HS256 / SHA-256 |
| Rapports | python-docx |
| IA | Adaptateur universel httpx (OpenAI / Anthropic / Gemini / Ollama) |

### Structure des fichiers

```
scribe/
├── config.xml              ← Configuration établissement (à remplir)
├── setup.py                ← Initialisation (à lancer une fois)
├── main.py                 ← Serveur (à lancer à chaque démarrage)
├── import_uf2.py           ← Import UF depuis Excel FICOM
├── requirements.txt        ← Dépendances Python
├── scribe.db               ← Base de données SQLite (générée)
├── uploads/                ← Pièces jointes
└── app/
    ├── models.py           ← Modèles de données (SQLAlchemy)
    ├── database.py         ← Connexion SQLite
    ├── api/
    │   ├── ai_router.py    ← Routeur IA universel (7 fournisseurs)
    │   ├── albert.py       ← Endpoints IA + prompts métier
    │   ├── auth.py         ← Authentification JWT
    │   ├── sitrep.py       ← Main courante / incidents
    │   ├── cellule.py      ← Décisions + présences
    │   ├── releve.py       ← Consignes de relève
    │   ├── cartographie.py ← Sites + UF
    │   ├── tasks.py        ← Kanban
    │   ├── rapport.py      ← Export DOCX + REX
    │   └── attachments.py  ← Pièces jointes
    └── static/
        ├── index.html      ← Interface complète (SPA)
        └── config.js       ← Généré par setup.py
```

### Modèle de données

```
Hospital (Sites)
└── UniteFonctionnelle (UF par pôle)

SitrepEntry (Incidents)
├── Jalons (JSON — chronologie horodatée)
├── Attachment (Pièces jointes)
├── Task (Tâches Kanban liées)
└── albert_avis (Analyse IA stockée)

Decision (Cellule de crise)
Presence (Registre des présences)
Consigne (Relève)
RexEntry (REX — liés optionnellement à un incident)

User
└── Notification (Inbox)
```

### API REST

```
GET/POST   /api/v1/sitrep/        Incidents (main courante)
PUT        /api/v1/sitrep/{id}/status
PUT        /api/v1/sitrep/{id}/jalons
GET        /api/v1/sitrep/stats   KPIs temps réel
GET        /api/v1/sitrep/export-csv

GET/POST   /api/v1/cellule/decisions
GET/POST   /api/v1/cellule/presences

GET/POST   /api/v1/tasks/         Kanban
PUT        /api/v1/tasks/{id}/move

GET/POST   /api/v1/rapport/rex    REX
GET        /api/v1/rapport/rapport/{id}  Export DOCX

POST       /api/v1/albert/analyser        Analyse incident
POST       /api/v1/albert/situation-globale
GET        /api/v1/albert/config  Fournisseur IA actif

POST       /api/v1/auth/login
GET/POST   /api/v1/auth/users
GET        /api/v1/auth/notifications
```

---

## Conformité réglementaire

SCRIBE est conçu pour accompagner la mise en conformité avec les textes applicables aux établissements de santé.

### NIS2 (Directive européenne)

- **Traçabilité des incidents** : chaque incident est horodaté, numéroté, associé à un déclarant identifié
- **Chronologie de détection et de résolution** : les champs MTTD/MTTR sont calculés automatiquement et exportables
- **Notification dans les délais** (24h pour incidents significatifs) : l'analyse IA rappelle l'obligation de notification aux organismes compétents lorsque c'est applicable
- **Documentation des décisions** : le registre de cellule constitue la preuve des actions correctives menées

### CERT Santé

- **Main courante horodatée** : conforme aux exigences de traçabilité du CERT Santé
- **Export CSV** : format adapté pour l'envoi des éléments de chronologie
- **Rapport de clôture DOCX** : structure alignée avec les attendus du CERT Santé pour les comptes-rendus d'incident
- **Contact CERT Santé** pré-intégré dans l'annuaire de secours

### HDS (Hébergement de Données de Santé)

- **Données hébergées localement** : SQLite sur le serveur de l'établissement, aucune donnée transmise à un tiers (hors choix d'un fournisseur IA cloud)
- **Mode Ollama** : IA entièrement locale, zéro donnée sortante
- **Pas de cloud** : pas de SaaS, pas de compte en ligne, pas de télémétrie

### RGPD

- Aucune donnée patient dans la main courante (données organisationnelles uniquement)
- Aucune transmission à des tiers
- Suppression des incidents possible par les administrateurs

### Plan Blanc / ORSAN

- Base réglementaire associée à chaque décision (Plan Blanc, ORSAN, PCA, NIS2…)
- Structuration de la main courante conforme aux exigences de traçabilité du Plan Blanc
- Registre des présences en cellule conforme

---

## Cas d'usage concrets

### Scénario 1 — Attaque ransomware (3h du matin)

1. L'administrateur système détecte une activité suspecte et déclare un incident CYBER, urgence 3 (CRISE), sur le site principal
2. SCRIBE notifie immédiatement tous les directeurs de crise configurés via l'Inbox
3. Le RSSI arrive en salle, bascule sur l'annuaire de secours (réseau IP potentiellement compromis)
4. Le directeur de garde active la cellule de crise — les présences sont enregistrées
5. Les jalons s'enchaînent : DSI contacté ✓ → RSSI alerté ✓ → Isolation réseau ✓
6. L'IA analyse la situation : niveau CRISE, recommande de notifier le CERT Santé dans les 24h
7. Les décisions sont enregistrées en temps réel dans le registre cellule
8. Les tâches opérationnelles (isoler le VLAN, contacter le prestataire, basculer sur le PABX de secours) sont distribuées via le Kanban
9. À 6h, la relève est formalisée avec accusé de réception
10. À J+1, le rapport de clôture DOCX est généré en un clic, avec chronologie complète

### Scénario 2 — Déclenchement Plan Blanc (afflux massif de blessés)

1. Le SAMU contacte l'établissement — Plan Blanc déclenché — incident SANITAIRE, urgence 4 (CRITIQUE)
2. L'onglet SOINS est activé : état de chaque service mis à jour (Urgences CRITIQUE, Bloc DÉGRADÉ, Réa NOMINAL)
3. La cellule de crise enregistre les décisions de réquisition et de déprogrammation
4. L'IA synthétise l'état des pôles et formule des recommandations ARS
5. Les consignes de relève entre les équipes de jour et de nuit sont traçées avec accusé de réception
6. L'export CSV est transmis à l'ARS pour le reporting réglementaire

---

## Feuille de route

Les évolutions suivantes sont envisagées selon les retours des établissements :

- [ ] Export PDF natif (en plus du DOCX)
- [ ] Interface de configuration graphique (sans éditer config.xml manuellement)
- [ ] Mode multi-établissements (groupement hospitalier de territoire)
- [ ] Synchronisation entre deux instances SCRIBE (réseau principal + réseau de crise)
- [ ] Intégration SIGO / messagerie sécurisée MSSanté
- [ ] Application mobile PWA pour les astreintes
- [ ] Modèles de jalons paramétrables par type de crise
- [ ] Tableau de bord de suivi des plans d'action post-REX

---

## Contribution

SCRIBE est distribué librement aux établissements de santé.

**Vous avez identifié un bug ou souhaitez proposer une fonctionnalité ?** Ouvrez une *issue* sur ce dépôt ou contactez directement l'équipe DSI/RSSI qui vous a fourni cet outil.

**Vous souhaitez contribuer au code ?** Les *pull requests* sont bienvenues. Respectez la philosophie du projet : simplicité de déploiement, zéro dépendance externe obligatoire, fonctionnement sur réseau isolé.

---

## Licence

SCRIBE est mis à disposition librement pour les établissements de santé publics et privés français. Aucune contrepartie n'est demandée.

Attribution appréciée mais non obligatoire.

---

*Développé par et pour les équipes de sécurité des SI hospitaliers français.*
*Conforme aux exigences NIS2, CERT Santé, HDS et Plan Blanc.*
