@echo off
REM Lance le script fusion_tool.py en mode merge
REM Ce batch suppose que fusion_tool.py se trouve dans le même dossier que le batch
python "%~dp0fusion_tool.py" merge mon_super_fichier.dart
pause