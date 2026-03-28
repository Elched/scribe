SCRIBE — Main courante de gestion de crise hospitalière
=====================================

Résumé
------

[🇬🇧 English](README.md)

SCRIBE est une application open-source pour la gestion de crise et le suivi de la capacité en lits d’un établissement de santé. Elle a été développée pour des usages opérationnels (cellule de crise, main courante) et pour le pilotage capacitaire (lits/RH/matériel).

Fonctionnalités principales :
- Main courante (sitrep) : création d’incidents, jalons, pièces jointes
- Suivi capacitaire : déclarations quotidiennes par unité (lits H/F/N, tensions)
- Salle de crise : registre de présence horodaté, journal des décisions, Kanban opérationnel
- Collecteur territorial : agrège les remontées de plusieurs sites
- Analyse IA optionnelle via fournisseurs configurables (Albert, OpenAI, etc.)

Principes de conception
-----------------------
- Fonctionne en local / on-premise (pas d’obligation cloud)
- Interface simple pour des utilisateurs non techniques (cadres, directeurs)
- Empilement léger : Python + FastAPI + SQLite par défaut

Démarrage rapide (mode démo)
----------------------------

Avec Docker Compose (mode démo intégré) :

```powershell
git clone https://github.com/nocomp/scribe.git
cd scribe
docker compose up -d
# Ouvrir ensuite http://localhost:8000 (utilisateur démo : dircrise / Scribe2026!)
```

Sans Docker (exécution locale) :

```powershell
pip install -r scribe/requirements.txt
python scribe/setup_demo1.py
python scribe/seed_demo_crise.py
python scribe/main.py
```

Architecture
------------

Structure principale :

```
scribe/
├─ scribe/        # application principale (FastAPI)
│  ├─ app/static/  # frontend (SPA)
│  ├─ app/lang/    # traductions (JSON)
│  └─ app/api/     # endpoints backend
└─ collecteur/    # collecteur territorial (FastAPI)
```

Configuration
-------------

La configuration principale se trouve dans `scribe/config.xml`. Elle contient les informations établissement, le compte admin initial, la langue par défaut et les paramètres IA.

Pour les déploiements Docker :
- Montez votre `config.xml` dans `/data/config.xml` (volume) pour qu’il soit utilisé au démarrage.
- Le fichier `config.js` généré par `setup.py` est placé dans `/data` si vous utilisez le volume persistant.

Internationalisation (i18n)
---------------------------

Les traductions se trouvent dans `scribe/app/lang/` au format JSON (fichiers nommés par code de langue, ex. `fr.json`, `en.json`).

Pour modifier ou ajouter une langue :
- Éditez `scribe/app/lang/<code>.json` et mettez à jour le bloc `_meta` (`code`, `name`, `flag`, `direction`).
- Redémarrez le service pour vider le cache en mémoire (l’API met en cache les fichiers). L’API d’i18n est disponible sous `/api/v1/i18n/<code>` pour inspection.

Collecteur territorial
----------------------

Le service `collecteur` reçoit les pushs JSON depuis plusieurs instances SCRIBE et propose une interface de supervision en lecture seule (port par défaut `9000`).
Routes principales :
- `/api/push` — état de crise (incidents et KPI)
- `/api/push-capacite` — état capacitaire (lits et ressources)

Scénario de démonstration
-------------------------

Le script `seed_demo_crise.py` charge un scénario réaliste (ex. incident ransomware) pour tests et démonstrations : incidents, décisions, tâches, passations.

Conformité et observations opérationnelles
-----------------------------------------

- Conçu pour aider aux exigences NIS2, Plan Blanc et ORSAN.
- Déploiement local recommandé pour conformité HDS / RGPD (éviter le cloud si nécessaire).

Déploiement Docker (production)
--------------------------------

Utilisez des variables d’environnement pour ne pas stocker de secrets en clair. Créez un fichier `.env` à côté de `docker-compose.yml` contenant au minimum :

```
SCRIBE_SECRET=RemplacezParUnSecretFort_32caracteres_ou_plus
ADMIN_PASSWORD=ChangezCeMotDePasseAdmin!
CORS_ORIGINS=https://votre.domaine.exemple
LOG_LEVEL=info
```

Démarrage recommandé :

```powershell
cd 'C:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe'
docker compose pull
docker compose up -d --remove-orphans
docker compose logs -f
```

Remarques importantes :
- `SCRIBE_SECRET` sert à signer les JWT : conservez-le secret et renouvelez-le régulièrement.
- En production, préférez une base de données persistante (PostgreSQL via `DATABASE_URL`) plutôt que SQLite.
- N’enregistrez jamais le fichier `.env` dans le dépôt git.

Sauvegarde et reprise
---------------------

- Si vous utilisez SQLite, sauvegardez régulièrement `/data/db/scribe.db` (copie du fichier) et testez la restauration.
- Pour PostgreSQL, utilisez les outils de sauvegarde/restauration standard (pg_dump / pg_restore).

Sécurité et bonnes pratiques
---------------------------

- Placez le service derrière un reverse-proxy TLS (Traefik, Nginx) et n’exposez pas l’interface d’administration publiquement.
- Restreignez les origines CORS via la variable `CORS_ORIGINS`.
- Faites tourner l’application avec un utilisateur non-root en production.

Contribuer
----------

- Testez vos modifications et utilisez `python -m py_compile` pour vérifier les erreurs de syntaxe.
- Ouvrez des issues ou merge requests claires et ciblées.

Licence
-------

MIT

Contact mainteneur
------------------

Pour questions ou contribution, créez une issue sur le dépôt GitHub ou contactez l’équipe en charge (coordonnées internes selon votre organisation).
