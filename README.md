# 🏥 SCRIBE — Main courante de crise hospitalière

**Outil open-source de gestion de crise pour les établissements de santé français.**
Couvre les crises cyber (NIS2, ANSSI, CERT Santé) et sanitaires (Plan Blanc, ORSAN).

---

## 🚀 Déploiement en 5 minutes

### Prérequis

- Python 3.9 ou supérieur
- Pas de base de données externe (SQLite embarqué)
- Pas de connexion Internet requise après installation (fonctionne en réseau isolé)

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configurer votre établissement

Ouvrez **`config.xml`** dans un éditeur de texte et remplissez :

| Section | Contenu |
|---|---|
| `<etablissement>` | Nom, sigle, FINESS |
| `<admin>` | Login et mot de passe initial |
| `<sites>` | Sites géographiques avec coordonnées GPS |
| `<directeurs>` | Noms et fonctions des directeurs de crise |
| `<unites_fonctionnelles>` | UF par site et par pôle |
| `<annuaire_normal>` | Téléphonie VoIP / IP-PBX nominale |
| `<annuaire_secours>` | GSM et fixes cuivre en cas de panne |

> **Astuce coordonnées GPS** : sur maps.google.fr, faites un clic droit sur votre établissement → "Coordonnées du lieu".

> **Vous avez un export FICOM ?** Ignorez la section `<unites_fonctionnelles>` et utilisez :
> ```bash
> python import_uf2.py
> ```

### 3. Initialiser

```bash
python setup.py
```

Ce script crée la base de données, charge vos données et génère la configuration pour l'interface web.

### 4. Démarrer

```bash
python main.py
```

Ouvrez votre navigateur sur **http://localhost:8000**

> Pour un accès depuis d'autres postes du réseau :
> ```bash
> python main.py --host 0.0.0.0 --port 8000
> ```

### 5. Première connexion

- **Login** : celui défini dans `<admin><login>` (défaut : `dircrise`)
- **Mot de passe** : celui défini dans `<admin><password>`
- **⚠️ Changez le mot de passe immédiatement** via le panneau admin (icône utilisateur, haut à droite)

---

## 📋 Fonctionnalités

| Onglet | Fonctionnalité |
|---|---|
| **VEILLE** | Déclaration d'incidents, carte des sites, filtres, pièces jointes |
| **SOINS** | Cartographie d'impact par pôle, timeline de projection |
| **CELLULE** | Registre des présences, chronologie décisionnelle |
| **KANBAN** | Suivi des tâches opérationnelles par colonne drag & drop |
| **REX** | Retours d'expérience, métriques MTTD/MTTR, export DOCX |
| **RELÈVE** | Consignes de passation avec accusé de réception |
| **ANNUAIRE** | Téléphonie nominale et de secours |

### Fonctionnalités transversales

- 🔐 Authentification locale (JWT, pas de LDAP requis)
- 🔔 Inbox notifications pour les directeurs de crise
- 📄 Rapport de clôture DOCX automatique
- 🧠 Intégration Albert AI (service numérique de l'État français)
- 🌙 / ☀️ Mode sombre / clair
- 📱 Fonctionne sur réseau parallèle isolé (sans Internet)

---

## 🔧 Configuration avancée

### Changer le port

```bash
python main.py --port 8080
```

### Utiliser un fichier XML différent

```bash
python setup.py /chemin/vers/mon_etablissement.xml
```

### Réinitialiser complètement

```bash
del scribe.db          # Windows
rm scribe.db           # Linux / Mac
python setup.py
```

### Mettre à jour la configuration sans perdre les données

Modifiez `config.xml` puis relancez `setup.py`. Les incidents, décisions et REX existants sont préservés. Seuls les sites, UF, directeurs et annuaires sont mis à jour.

---

## 🗂️ Structure des fichiers

```
scribe/
├── config.xml          ← VOTRE FICHIER DE CONFIGURATION
├── setup.py            ← Script d'initialisation (à lancer une fois)
├── main.py             ← Serveur web (à lancer à chaque démarrage)
├── import_uf2.py       ← Import UF depuis Excel FICOM (optionnel)
├── requirements.txt    ← Dépendances Python
├── scribe.db           ← Base de données (créée automatiquement)
├── uploads/            ← Pièces jointes des incidents
└── app/
    ├── api/            ← API REST (FastAPI)
    ├── models.py       ← Modèles de données
    └── static/
        ├── index.html  ← Interface web (single page)
        └── config.js   ← Généré par setup.py (ne pas modifier)
```

---

## 📡 Réglementaire

SCRIBE est conçu pour accompagner la mise en conformité avec :

- **NIS2** — Traçabilité des incidents et décisions
- **CERT Santé** — Main courante horodatée exportable
- **HDS** — Hébergement local, pas de données dans le cloud
- **RGPD** — Aucune donnée transmise à des tiers

---

## 🆓 Licence & Contribution

SCRIBE est distribué gratuitement pour les établissements de santé.

Pour signaler un problème ou proposer une amélioration, contactez votre correspondant RSSI ou l'équipe DSI qui vous a fourni cet outil.

---

## ❓ Dépannage

| Problème | Solution |
|---|---|
| `ModuleNotFoundError` | Relancer `pip install -r requirements.txt` |
| Carte vide | Vérifiez les coordonnées GPS dans `config.xml` (format décimal, ex: `45.9336`) |
| Login 401 | Relancer `python setup.py` pour réinitialiser le compte admin |
| UF absentes | Utiliser `python import_uf2.py` avec votre fichier FICOM |
| Port déjà utilisé | `python main.py --port 8001` |

---

*Développé pour les établissements de santé publics français — Réseau parallèle compatible.*
