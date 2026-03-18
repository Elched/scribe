@echo off
echo ==========================================
echo  SCRIBE v1.2.0 - Mise a jour
echo ==========================================
echo.

:: Tuer le serveur si en cours
echo [1/4] Arret du serveur...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

:: Supprimer le cache Python  
echo [2/4] Nettoyage cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

:: Verifier que index.html est bien la nouvelle version
echo [3/4] Verification index.html...
findstr /c:"JSZip 3.10.1" app\static\index.html >nul
if errorlevel 1 (
    echo ERREUR: index.html ne contient pas JSZip inline !
    echo Verifiez que vous avez bien remplace app\static\index.html
    pause
    exit /b 1
) else (
    echo OK - JSZip inline detecte
)
findstr /c:"azLog" app\static\index.html >nul
if errorlevel 1 (
    echo ERREUR: index.html ne contient pas les logs de debug
    pause
    exit /b 1
) else (
    echo OK - Console de debug detectee
)

:: Demarrer le serveur
echo [4/4] Demarrage du serveur...
echo.
echo Serveur demarre sur http://localhost:8000
echo Appuyez sur Ctrl+C pour arreter
echo.
python main.py
