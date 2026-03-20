@echo off
chcp 65001 > nul 2>&1
cd /d "%~dp0"

echo.
echo  =====================================================
echo   SCRIBE v1.3.0 - Configuration initiale
echo   github.com/nocomp/scribe
echo  =====================================================
echo.

:MENU
echo  Choisissez un mode :
echo.
echo   1  Mon etablissement (fichier Excel SCRIBE_config_etablissement.xlsx)
echo   2  Demo ransomware LockBit 48h (CHV Valmont)
echo   3  Demo clinique Montrelay
echo   4  Docker (necessite Docker Desktop installe)
echo   5  Quitter
echo.
set CHOIX=
set /p CHOIX=Votre choix (1-5) : 
echo.

if "%CHOIX%"=="1" goto EXCEL
if "%CHOIX%"=="2" goto DEMO1
if "%CHOIX%"=="3" goto DEMO2
if "%CHOIX%"=="4" goto DOCKER
if "%CHOIX%"=="5" goto FIN
echo  Choix invalide.
goto MENU

:EXCEL
echo  [MON ETABLISSEMENT] Import depuis fichier Excel
echo.
python --version > nul 2>&1
if errorlevel 1 ( echo [ERREUR] Python introuvable & pause & exit /b 1 )
if not exist SCRIBE_config_etablissement.xlsx (
    echo  [ERREUR] SCRIBE_config_etablissement.xlsx introuvable.
    echo  Placez le fichier Excel dans ce dossier et relancez.
    pause
    goto MENU
)
if exist scribe.db del /f scribe.db
if exist app\static\config.js del /f app\static\config.js
python import_config_xlsx.py SCRIBE_config_etablissement.xlsx
if errorlevel 1 ( echo [ERREUR] Import echoue & pause & exit /b 1 )
goto DEMARRER

:DEMO1
echo  [DEMO 1] Centre Hospitalier de Valmont - Scenario ransomware LockBit
echo.
python --version > nul 2>&1
if errorlevel 1 ( echo [ERREUR] Python introuvable & pause & exit /b 1 )
if exist scribe.db del /f scribe.db
if exist app\static\config.js del /f app\static\config.js
python setup_demo1.py
if errorlevel 1 ( echo [ERREUR] setup_demo1.py & pause & exit /b 1 )
python setup_capacite_demo.py
python seed_demo_crise.py
if errorlevel 1 ( echo [ERREUR] seed_demo_crise.py & pause & exit /b 1 )
goto DEMARRER

:DEMO2
echo  [DEMO 2] Clinique Saint-Benoit de Montrelay
echo.
python --version > nul 2>&1
if errorlevel 1 ( echo [ERREUR] Python introuvable & pause & exit /b 1 )
if exist scribe.db del /f scribe.db
if exist app\static\config.js del /f app\static\config.js
python setup_demo2.py
if errorlevel 1 ( echo [ERREUR] setup_demo2.py & pause & exit /b 1 )
goto DEMARRER

:DOCKER
echo  [DOCKER] Verification de Docker...
docker --version > nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Docker introuvable.
    echo  Installez Docker Desktop : https://www.docker.com/products/docker-desktop
    pause
    goto MENU
)
echo.
echo  Mode Docker :
echo   1  Demo (mode par defaut - aucun fichier requis)
echo   2  Mon etablissement (monte config.xml en volume)
echo.
set DSUB=
set /p DSUB=Votre choix (1-2) : 

if "%DSUB%"=="2" goto DOCKER_CUSTOM

echo  Demarrage en mode demo...
docker compose up -d
if errorlevel 1 ( echo [ERREUR] docker compose a echoue & pause & goto MENU )
echo.
echo  SCRIBE demarre sur http://localhost:8000
echo  Login : dircrise / Scribe2026!
echo  Logs : docker compose logs -f
pause
goto FIN

:DOCKER_CUSTOM
if not exist config.xml (
    echo  [ERREUR] config.xml introuvable dans ce dossier.
    pause
    goto MENU
)
echo  Demarrage avec config.xml...
docker compose up -d -e SCRIBE_CONFIG=/data/config.xml
echo  Copie de config.xml dans le volume Docker...
docker cp config.xml scribe:/data/config.xml
docker restart scribe
echo.
echo  SCRIBE demarre sur http://localhost:8000
echo  Logs : docker compose logs -f
pause
goto FIN

:DEMARRER
echo.
echo  =====================================================
echo   SCRIBE demarre sur http://localhost:8000
echo   Login    : dircrise
echo   Password : Scribe2026! (sauf si modifie dans le fichier Excel)
echo  =====================================================
echo.
echo  Ctrl+C pour arreter
echo.
python main.py
pause

:FIN
exit /b 0
