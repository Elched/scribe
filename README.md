# 🏥 SCRIBE — Main courante de crise hospitalière

> **Outil open-source de gestion opérationnelle des crises cyber et sanitaires pour les établissements de santé français.**

[![Licence: MIT](https://img.shields.io/badge/licence-MIT-brightgreen)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com)
[![Réseau isolé](https://img.shields.io/badge/réseau-isolé%20compatible-orange)](#déploiement-en-5-minutes)
[![NIS2](https://img.shields.io/badge/conformité-NIS2%20%7C%20CERT%20Santé-red)](#conformité-réglementaire)

---

## Pourquoi SCRIBE ?

Lors d'une crise cyber ou sanitaire à l'hôpital, les équipes font face à un problème constant : **la perte de traçabilité**. Les décisions sont prises oralement, les chronologies se reconstituent de mémoire, les consignes de relève s'échangent par SMS, et le rapport post-incident mobilise des jours de travail.

SCRIBE résout ce problème en fournissant une **main courante numérique centralisée**, accessible depuis n'importe quel poste du réseau interne, qui fonctionne même en cas de panne des systèmes d'information principaux.

**Conçu par des professionnels de la sécurité des SI hospitaliers**, SCRIBE est calibré pour les contraintes réelles du terrain : réseau parallèle isolé, absence d'Active Directory, personnel non-technique en salle de crise, obligations réglementaires NIS2 et CERT Santé.

---

## Table des matières

- [Aperçu](#aperçu)
- [Fonctionnalités détaillées](#fonctionnalités-détaillées)
- [Déploiement en 5 minutes](#déploiement-en-5-minutes)
- [Configuration établissement](#configuration-établissement)
- [Intelligence artificielle](#intelligence-artificielle-configurable)
- [Architecture technique](#architecture-technique)
- [Conformité réglementaire](#conformité-réglementaire)
- [Feuille de route](#feuille-de-route)

---

## Aperçu

### 🌐 Main courante — Déclaration et suivi des incidents

![Onglet Veille — main courante principale](screenshots/acc.png)

Formulaire de déclaration structuré (type, urgence, site, UF, fait, analyse, jalons, PJ) avec timeline horodatée en temps réel, carte géographique multi-sites et KPIs dynamiques. L'analyse IA est disponible en un clic à tout moment.

---

### 🏥 Cartographie des soins — Impact sur les pôles cliniques

![Onglet Soins — état des pôles](screenshots/soin.png)

Vue transversale de l'impact sur chaque pôle clinique. Chaque unité peut être passée en Opérationnel, Mode dégradé ou Impact critique, avec horodatage automatique. Indispensable pour le Plan Blanc et les crises affectant les soins.

---

### ⚖️ Cellule de crise — Registre décisionnel

![Onglet Cellule — registre des décisions et présences](screenshots/celulle.png)

Registre horodaté des présences en cellule et de chaque décision prise, avec responsable, base réglementaire (Plan Blanc, ORSAN, NIS2…) et statut de validation. Constitue la preuve documentaire exigée par NIS2 et le Plan Blanc.

---

### 📋 Kanban — Gestion des tâches opérationnelles

![Onglet Kanban — tableau des tâches](screenshots/kaban.png)

Tableau en 4 colonnes (Backlog → En cours → En attente → Terminé) avec liaison directe aux incidents ouverts, assignation, priorité et échéance. Mise à jour en temps réel pour tous les utilisateurs connectés.

---

### 📊 REX — Retour d'expérience

![Onglet REX — retour d'expérience](screenshots/rex.png)

Formulaire guidé en langage naturel (3 étapes), pré-rempli automatiquement depuis les données de la main courante. Dashboard de métriques agrégées (MTTR, MTTD, jalons). Export rapport de clôture DOCX en un clic.

---

### 🔄 Relève — Passation entre équipes

![Onglet Relève — consignes avec accusé de réception](screenshots/releve.png)

Consignes horodatées avec accusé de réception numérique. Garantit la traçabilité complète des passations entre équipes, moment critique où l'information se perd habituellement.

---

### 📞 Annuaire — Téléphonie nominale et de secours

![Onglet Annuaire — double annuaire nominal et secours](screenshots/annuaire.png)

Double annuaire bascule en un clic : téléphonie IP/VoIP nominale et numéros de secours (GSM, fixes cuivre) utilisables si le système téléphonique IP est hors service. Entièrement configuré depuis `config.xml`, aucune donnée hardcodée.

---

## Fonctionnalités détaillées

### 🌐 Onglet VEILLE — Main courante principale

**Déclaration d'incident**
- Saisie guidée : type de crise (Cyber / Sanitaire / Mixte), niveau d'urgence (1 Veille → 4 Critique), site, unité fonctionnelle
- Champ *Fait* (description factuelle) séparé du champ *Analyse* (impact et systèmes affectés) — distinction essentielle pour les rapports ANSSI/CERT Santé
- Moyens engagés et coordonnées de l'intervenant
- **Jalons de résolution** : boutons prédéfinis (Passé d'ordi, DSI contacté, RSSI alerté, Cellule activée, CERT Santé, Isolation réseau, Sauvegarde OK, Retour normal) + jalons personnalisés — chaque jalon est horodaté au clic
- Projection de résolution estimée avec compte à rebours en temps réel
- Pièces jointes : captures d'écran, logs, documents (PDF, images, tout format)
- Demande d'avis IA au moment de la déclaration

**Timeline des incidents**
- Affichage en temps réel, rafraîchissement automatique toutes les 12 secondes
- Code couleur par niveau d'urgence : bleu (veille) → orange (alerte) → rouge (crise) → noir (critique)
- Progression des jalons par barre de pourcentage sur chaque fiche
- Pièces jointes visibles directement sur la fiche (chips cliquables)
- Numéro d'incident `#ID` affiché pour référencement croisé
- Filtres combinables : site, directeur, urgence, statut, type
- Changement de statut en un clic (Signalé → En cours → Résolu)
- Actions rapides depuis chaque fiche : 🤖 Avis IA, 📎 PJ, 📋 Tâche Kanban, 📄 REX, 🗑 Supprimer

**KPIs en temps réel**
- Total incidents, Critiques, Ouverts, Cyber, Sanitaires
- Indicateur de niveau global calculé automatiquement : VEILLE NORMALE → ALERTE → CRISE → CRITIQUE

**Carte géographique**
- Carte OpenStreetMap avec marqueurs colorés par niveau d'alerte de chaque site
- Auto-zoom vers le site le plus critique
- Intégration *La Suite Numérique* : boutons VISIO et PAD

**Export**
- Export CSV horodaté de toute la main courante (compatible tableur)

---

### 🏥 Onglet SOINS — Impact sur les unités de soins

- Toutes les unités fonctionnelles regroupées par pôle clinique
- État par UF : Nominal / Dégradé / Critique / Fermé, avec compteur de patients et commentaire libre
- Horodatage automatique de chaque mise à jour
- Dashboard de synthèse : pôles impactés, patients concernés, % activité nominale vs dégradée
- Résumé transmis automatiquement à l'analyse IA globale

---

### ⚖️ Onglet CELLULE — Registre de la cellule de crise

- **Registre des présences** : entrées/sorties horodatées, nom, fonction, action
- **Chronologie décisionnelle** : chaque décision horodatée, avec responsable, référence réglementaire et statut de validation
- **Analyse IA globale** : synthèse proportionnée de tous les incidents + décisions + état des pôles, avec actions prioritaires et points de vigilance

---

### 📋 Onglet KANBAN — Gestion des tâches opérationnelles

- Tableau BACKLOG → EN COURS → EN ATTENTE → TERMINÉ, drag & drop natif
- Lien vers l'incident source via sélecteur dynamique (incidents ouverts en tête, triés par urgence)
- Priorité : Critique (violet), Haute (rouge), Normale (jaune), Basse (vert)
- Date d'échéance avec alerte visuelle si dépassée
- Création rapide depuis une fiche incident en un clic (bouton 📋)

---

### 📊 Onglet REX — Retour d'expérience

**Formulaire en langage naturel — 3 étapes**
- *Étape 1* : Quel incident ? Quel type ? Qui rédige ?
- *Étape 2* : Délai de détection en h/min, durée de résolution en h/min, services impactés, jalons réalisés
- *Étape 3* : Ce qui a bien fonctionné / axes d'amélioration / actions concrètes / leçon principale

Sélecteur d'incident dynamique — pré-remplissage automatique depuis la main courante (durée, jalons, type).

**Dashboard REX**
- KPIs agrégés : MTTR moyen, MTTD moyen, % jalons complétés
- Graphique de répartition par type de crise
- Export rapport de clôture DOCX complet (page de garde, chronologie, décisions, présences, consignes, avis IA)

---

### 🔄 Onglet RELÈVE — Passation entre équipes

- Consignes horodatées destinées à une personne ou un poste
- **Accusé de réception** numérique horodaté — non modifiable après accusé
- Historique complet de toutes les consignes de la crise

---

### 📞 Onglet ANNUAIRE — Téléphonie de crise

- **Annuaire nominal** : numéros IP/VoIP/DECT du réseau téléphonique habituel
- **Annuaire de secours** : GSM personnels, fixes cuivre — utilisables si le système téléphonique IP est hors service
- Bascule en un clic entre les deux modes
- Entièrement configuré depuis `config.xml`, aucune donnée hardcodée

---

### 🔐 Authentification et gestion des utilisateurs

- Aucune dépendance LDAP / Active Directory — fonctionne sur réseau isolé
- JWT HS256, hash SHA-256 des mots de passe
- Rôles : **Admin** (complet + gestion utilisateurs), **Directeur** (opérationnel), **Observateur** (lecture seule)
- Périmètres : un directeur peut être limité à un site ou un service spécifique
- Notifications de périmètre : inbox personnalisée par utilisateur

---

### 🔔 Notifications

- Badge non-lu dans le header, mis à jour toutes les 15 secondes
- Panneau Inbox glissant : INCIDENT, TÂCHE, SYSTÈME
- Clic → navigation directe vers l'incident concerné

---

### 🧠 Intelligence artificielle (7 fournisseurs)

| Fournisseur | Description | Données sortantes |
|---|---|---|
| 🇫🇷 **Albert** (défaut) | IA souveraine DINUM/Etalab | Serveurs gouvernementaux FR |
| 🤖 **OpenAI** | ChatGPT (GPT-4o, GPT-4o-mini…) | Serveurs OpenAI US |
| 🟤 **Anthropic** | Claude (Haiku, Sonnet, Opus…) | Serveurs Anthropic US |
| 🔷 **Google Gemini** | Gemini 2.0 Flash, 1.5 Pro… | Serveurs Google |
| 🌪️ **Mistral AI** | mistral-small, mistral-large… | Serveurs Mistral FR |
| 🏠 **Ollama** | Modèle local (llama3, phi3…) | **Aucune — 100% local** |
| ⚙️ **OpenAI-compat** | LM Studio, vLLM, Jan… | **Aucune — 100% local** |

Changement de fournisseur : une seule ligne dans `config.xml`, puis `python setup.py`. Aucune modification de code.

> Pour les établissements sur réseau totalement isolé, le mode **Ollama** permet une IA entièrement locale sans aucune donnée qui sort du SI.

---

### 🎨 Interface

- **Mode sombre / clair** : bascule via le bouton 🌙/☀️, mémorisé entre les sessions
- Single Page Application : aucun rechargement de page, temps de réponse < 100ms
- Badge du fournisseur IA actif affiché dans le header

---

## Déploiement en 5 minutes

### Prérequis

- Python 3.9 ou supérieur (`python --version`)
- Aucune base de données externe (SQLite embarqué)
- Aucune connexion Internet requise en fonctionnement

### Installation

```bash
# 1. Décompresser l'archive
unzip scribe_open.zip && cd scribe_open

# 2. Installer les dépendances Python
pip install -r requirements.txt

# 3. Éditer config.xml avec les données de votre établissement

# 4. Initialiser
python setup.py

# 5. Démarrer
python main.py
```

Ouvrez **http://localhost:8000** — Login : `dircrise` / `Scribe2026!` (**à changer immédiatement** via le panneau admin).

### Accès réseau (salle de crise)

```bash
python main.py --host 0.0.0.0 --port 8000
# → http://[IP-du-serveur]:8000 depuis tous les postes du réseau
```

### Import des unités fonctionnelles

```bash
# Option A — remplir le modèle fourni
python import_uf2.py uf_modele.xlsx

# Option B — export FICOM de votre établissement
python import_uf2.py votre_export.xlsx
```

### Service systemd (production)

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
systemctl enable scribe && systemctl start scribe
```

---

## Configuration établissement

Tout se configure dans **`config.xml`** — c'est le seul fichier à modifier.

```xml
<scribe>
  <etablissement>
    <nom>Centre Hospitalier de Votre Ville</nom>
    <sigle>CHVV</sigle>
    <finess>000000000</finess>
  </etablissement>

  <admin>
    <login>dircrise</login>
    <password>VotreMotDePasse!</password>   <!-- Changer après la 1ère connexion -->
  </admin>

  <sites>
    <site>
      <nom>Site Principal</nom>
      <adresse>1 avenue de l'Hôpital, 00000 Ville</adresse>
      <latitude>48.8566</latitude>
      <longitude>2.3522</longitude>
      <telephone_garde>01 00 00 00 00</telephone_garde>
    </site>
  </sites>

  <directeurs>
    <directeur>
      <nom>M. Prénom NOM</nom>
      <fonction>Directeur Général</fonction>
      <abreviation>DG</abreviation>
    </directeur>
  </directeurs>

  <unites_fonctionnelles site="Site Principal">
    <uf code="1001" pole="URGENCES">Urgences adultes</uf>
    <uf code="2001" pole="SOINS CRITIQUES">Réanimation</uf>
  </unites_fonctionnelles>

  <annuaire_normal>
    <contact service="URGENCES" local="IOA" tel="5100"/>
    <contact service="DSI INFORMATIQUE" local="Support" tel="6060"/>
  </annuaire_normal>

  <annuaire_secours>
    <contact service="CADRE DE NUIT" local="GSM" tel="06 00 00 00 00"/>
  </annuaire_secours>

  <ia>
    <fournisseur>albert</fournisseur>   <!-- albert | openai | anthropic | gemini | mistral | ollama -->
    <cle_api></cle_api>
    <modele></modele>                    <!-- Laisser vide = modèle par défaut -->
  </ia>
</scribe>
```

Puis : `python setup.py`

---

## Intelligence artificielle configurable

### Changer de fournisseur

```xml
<ia>
  <fournisseur>openai</fournisseur>
  <cle_api>sk-proj-xxxxx</cle_api>
  <modele>gpt-4o-mini</modele>
</ia>
```

### Mode 100% local avec Ollama

```bash
ollama pull llama3   # https://ollama.ai
```

```xml
<ia>
  <fournisseur>ollama</fournisseur>
  <modele>llama3</modele>
</ia>
```

Aucune donnée ne quitte le SI. Idéal pour les réseaux totalement isolés.

---

## Architecture technique

| Composant | Technologie |
|---|---|
| Backend | Python 3.9+ / FastAPI / SQLAlchemy |
| Base de données | SQLite (embarqué — fichier `scribe.db`) |
| Frontend | HTML5 / CSS3 / JavaScript vanilla (SPA) |
| Carte | Leaflet.js + OpenStreetMap |
| Authentification | JWT HS256 / SHA-256 |
| Rapports | python-docx |
| IA | Adaptateur universel httpx (7 fournisseurs) |

### Structure des fichiers

```
scribe/
├── config.xml              ← À remplir
├── setup.py                ← Initialisation
├── main.py                 ← Serveur
├── import_uf2.py           ← Import UF (FICOM ou modèle générique)
├── uf_modele.xlsx          ← Modèle Excel à adapter
├── seed.py                 ← Création des sites
├── requirements.txt
├── scribe.db               ← Base SQLite (générée)
├── uploads/                ← Pièces jointes
└── app/
    ├── models.py
    ├── database.py
    └── api/
        ├── ai_router.py    ← Routeur IA universel
        ├── albert.py       ← Endpoints IA + prompts métier
        ├── auth.py
        ├── sitrep.py       ← Main courante
        ├── cellule.py      ← Décisions + présences
        ├── releve.py
        ├── cartographie.py
        ├── tasks.py        ← Kanban
        ├── rapport.py      ← Export DOCX + REX
        └── attachments.py
    └── static/
        ├── index.html      ← Interface SPA
        └── config.js       ← Généré par setup.py
```

---

## Conformité réglementaire

### NIS2

- Traçabilité horodatée de chaque incident avec déclarant identifié
- MTTD/MTTR calculés automatiquement et exportables
- L'IA rappelle l'obligation de notification dans les 24h pour les incidents significatifs
- Le registre cellule constitue la preuve des actions correctives

### CERT Santé

- Main courante horodatée conforme aux exigences de traçabilité
- Export CSV pour envoi des éléments de chronologie
- Rapport de clôture DOCX aligné avec les attendus du CERT Santé
- Contact CERT Santé pré-intégré dans l'annuaire de secours

### HDS

- Données hébergées localement (SQLite sur le serveur de l'établissement)
- Aucune transmission à un tiers (sauf choix d'un fournisseur IA cloud)
- Mode Ollama : IA entièrement locale, zéro donnée sortante

### RGPD

- Aucune donnée patient dans la main courante (données organisationnelles uniquement)
- Pas de SaaS, pas de compte en ligne, pas de télémétrie

### Plan Blanc / ORSAN

- Structure de main courante conforme aux exigences du Plan Blanc
- Registre des présences en cellule conforme
- Base réglementaire associée à chaque décision

---

## Cas d'usage

### Ransomware à 3h du matin

L'administrateur déclare un incident CYBER urgence 3 → SCRIBE notifie les directeurs → la cellule s'active, les présences sont enregistrées → les jalons s'enchaînent (Isolation réseau ✓, CERT Santé ✓) → les tâches sont distribuées via le Kanban → la relève de 6h est formalisée avec accusé de réception → le rapport de clôture DOCX est généré en un clic le lendemain.

### Déclenchement Plan Blanc

Afflux massif → incident SANITAIRE urgence 4 → l'onglet SOINS affiche l'état de chaque pôle → la cellule enregistre les décisions de réquisition → l'IA synthétise l'état des pôles → l'export CSV est transmis à l'ARS.

---

## Feuille de route

- [ ] Export PDF natif
- [ ] Interface de configuration graphique (sans éditer config.xml manuellement)
- [ ] Mode multi-établissements (GHT)
- [ ] Synchronisation entre deux instances SCRIBE (réseau principal + réseau de crise)
- [ ] Application mobile PWA pour les astreintes
- [ ] Intégration messagerie sécurisée MSSanté
- [ ] Modèles de jalons paramétrables par type de crise

---

## Contribution

SCRIBE est distribué librement aux établissements de santé publics et privés.

Ouvrez une *issue* pour signaler un bug ou proposer une fonctionnalité. Les *pull requests* sont bienvenues.

---

## Licence

MIT — voir [LICENSE](LICENSE)

*Développé par et pour les équipes de sécurité des SI hospitaliers français.*  

