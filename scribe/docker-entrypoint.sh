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

# Config XML : priorité 1→ /data/config.xml (volume), 2→ /app/config.xml, 3→ demo
if [ -f /data/config.xml ]; then
    CONFIG_PATH=/data/config.xml
    echo "  [config] Utilisation de /data/config.xml (volume monté)"
elif [ -f /app/config.xml ]; then
    CONFIG_PATH=/app/config.xml
    echo "  [config] Utilisation de /app/config.xml"
elif [ -f /app/config_demo1.xml ]; then
    CONFIG_PATH=/app/config_demo1.xml
    echo "  [config] AVERTISSEMENT: aucun config.xml trouvé, démarrage en mode DEMO (config_demo1.xml)"
    echo "  [config] Pour une config personnalisée, montez votre fichier:"
    echo "  [config]   -v /chemin/vers/config.xml:/data/config.xml:ro"
else
    echo "  [config] ERREUR FATALE: aucun fichier de configuration trouvé !"
    echo "  [config] Montez votre config.xml avec: -v ./config.xml:/data/config.xml:ro"
    exit 1
fi

# Base SQLite : stocker dans /data/db/
export DATABASE_URL="sqlite:////data/db/scribe.db"

# Initialisation au premier démarrage
if [ ! -f /data/db/scribe.db ]; then
    echo "  [init] Premier démarrage — initialisation..."
    python setup.py "$CONFIG_PATH"
    # Référentiel capacitaire (selon le mode)
    if echo "$CONFIG_PATH" | grep -q "demo1\|demo"; then
        python setup_capacite_demo.py 2>/dev/null || true
        python seed_demo_crise.py 2>/dev/null || true
        echo "  [init] Mode démo : référentiel capacitaire + scénario crise chargés."
    else
        python setup_capacite_demo.py 2>/dev/null || true
        echo "  [init] Référentiel capacitaire générique chargé."
        echo "  [init] Pour votre référentiel : python setup_capacite_chag.py (CHAG)"
        echo "  [init]                          python import_config_xlsx.py (Excel)"
    fi
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

# config.js : déplacer vers /data/ pour persistance et créer le lien symbolique
if [ -f /app/app/static/config.js ] && [ ! -L /app/app/static/config.js ]; then
    mv /app/app/static/config.js /data/config.js
fi
if [ -f /data/config.js ]; then
    ln -sf /data/config.js /app/app/static/config.js
fi

echo ""
echo "  ✓ SCRIBE démarré sur http://0.0.0.0:8000"
echo "  ✓ Données persistantes dans /data/"
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
