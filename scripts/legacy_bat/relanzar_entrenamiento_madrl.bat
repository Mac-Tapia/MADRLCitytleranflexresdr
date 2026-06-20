@echo off
title CityLearn v3 MADRL - Entrenamiento completo 4 algoritmos
cd /d "%~dp0"
echo ============================================================
echo  CityLearn v3 MADRL - RELANZAMIENTO COMPLETO
echo  4 algoritmos: HAPPO / MASAC / MATD3 / MAAC
echo  3 escenarios: E1 Flexibilidad / E2 CO2 / E3 Costos
echo  Dataset: citylearn_iquitos_2023_2025 (17 edificios)
echo ============================================================
echo.
echo  IMPORTANTE: No cierre esta ventana durante el entrenamiento.
echo  El error "forrtl: error (200)" ocurre al cerrar la ventana.
echo.
echo  Presione Enter para iniciar o Ctrl+C para cancelar...
pause > nul
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -Command "$ts = Get-Date -Format 'yyyyMMdd_HHmmss'; $root = 'outputs\citylearn_v3_madrl_full_' + $ts; Set-Content outputs\latest_visible_training_output_root.txt $root -Encoding UTF8; & scripts\run_citylearn_v3_full_training_visible.ps1 -OutputRoot $root -Scenario ALL -Seed 0 -EpisodeTimeSteps 8760 -Episodes 75 -GpuProfile local4060_fast -ArtifactProfile efficient -TraceRecordInterval 10 -TraceDetail compact -Cuda -LiveOutput"
