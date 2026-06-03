@echo off
REM Lance le script fusion_tool.py en mode merge
REM Ce batch suppose que fusion_tool.py se trouve dans le même dossier que le batch

py "%~dp0fusion_tool.py" merge "%~dp0mon_super_fichier.dart" --project_dir "%~dp0"
if %errorlevel% neq 0 (
    echo ERREUR : le script a échoué avec le code %errorlevel%
)
pause
