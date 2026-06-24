@echo off
title MADRL CityLearn v3 — Entrenamiento Definitivo v4
cd /d D:\MADRLCitytleranflexresdr
echo.
echo ================================================================
echo   MADRL CityLearn v3 — Entrenamiento Definitivo v4
echo   HAPPO → MASAC → MATD3 → MAAC  (3 escenarios cada uno)
echo   Perfil: unified_comparable_v4
echo ================================================================
echo.
powershell.exe -ExecutionPolicy Bypass -NoExit -File "scripts\restart_happo_masac_v3.ps1"
