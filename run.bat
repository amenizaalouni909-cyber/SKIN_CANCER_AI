@echo off
title Skin Cancer AI — Lancement
color 0A
echo.
echo  =========================================
echo   SKIN CANCER AI — Demarrage du serveur
echo  =========================================
echo.

set "PATH=%LOCALAPPDATA%\Programs\Python\Python312\;%LOCALAPPDATA%\Programs\Python\Python312\Scripts\;%PATH%"

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Python non trouve. Verifiez l'installation.
    pause
    exit /b 1
)

if not exist "model\vgg16_skin_cancer.h5" (
    echo  [ATTENTION] Fichier modele introuvable :
    echo              model\vgg16_skin_cancer.h5
    echo.
    echo  Placez le fichier .h5 dans le dossier model\ puis relancez.
    echo.
    pause
    exit /b 1
)

echo  [OK] Modele detecte.
echo  [OK] Lancement de Flask sur http://127.0.0.1:5000
echo.
echo  Ouvrez votre navigateur et allez sur : http://127.0.0.1:5000
echo  Connexion : admin / 1234
echo.
echo  (Appuyez sur Ctrl+C pour arreter le serveur)
echo.

python app.py

pause
