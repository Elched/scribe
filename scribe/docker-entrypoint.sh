#!/bin/bash
set -e

echo ""
echo "  ██████╗  ██████╗██████╗ ██╗██████╗ ███████╗"
echo "  ██╔════╝██╔════╝██╔══██╗██║██╔══██╗██╔════╝"
echo "  ╚█████╗ ██║     ██████╔╝██║██████╔╝█████╗  "
echo "   ╚═══██╗██║     ██╔══██╗██║██╔══██╗██╔══╝  "
echo "  ██████╔╝╚██████╗██║  ██║██║██████╔╝███████╗"
echo "  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝"
echo "  Main courante de crise hospitalière — open source"
echo ""

# Lien symbolique base de données (au cas où le volume n'était pas monté au build)
mkdir -p /data/uploads /data/db
if [ ! -L /app/uploads ]; then
    rm -rf /app/uploads
    ln -sf /data/uploads /app/uploads
fi

# Config XML : priorité à /data/config.xml (monté par volume), sinon /app/config.xml
if [ -f /data/config.xml ]; then
    CONFIG_PATH=/data/config.xml
    echo "  [config] Utilisation de /data/config.xml"
else
    CONFIG_PATH=/app/config.xml
    echo "  [config] Utilisation de /app/config.xml (valeurs par défaut)"
fi

# Base SQLite : stocker dans /data/db/
export DATABASE_URL="sqlite:////data/db/scribe.db"

# Initialisation au premier démarrage
if [ ! -f /data/db/scribe.db ]; then
    echo "  [init] Premier démarrage — initialisation..."
    python setup.py "$CONFIG_PATH"
    python seed.py
    echo "  [init] Base initialisée."
else
    echo "  [init] Base existante détectée — démarrage direct."
    # Migrations légères : s'assurer que les nouvelles tables existent
    python -c "
import sys; sys.path.insert(0,'.')
from app.database import engine, Base
import app.models
Base.metadata.create_all(bind=engine)
print('  [init] Tables vérifiées.')
"
fi

# Lien config.js généré vers /app/app/static/
if [ -f /data/config.js ]; then
    ln -sf /data/config.js /app/app/static/config.js
fi

echo ""
echo "  ✓ SCRIBE démarré sur http://0.0.0.0:8000"
echo "  ✓ Données persistantes dans /data/"
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
