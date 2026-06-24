@echo off
title CityLearn MADRL LIVE OUTPUT
cd /d "%~dp0"
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -Command "$ts = Get-Date -Format 'yyyyMMdd_HHmmss'; $root = 'outputs\citylearn_v3_madrl_full_' + $ts; Set-Content outputs\latest_visible_training_output_root.txt $root -Encoding UTF8; & scripts\run_citylearn_v3_full_training_visible.ps1 -OutputRoot $root -Scenario ALL -Seed 0 -EpisodeTimeSteps 8760 -Episodes 75 -GpuProfile local4060_fast -ArtifactProfile efficient -TraceRecordInterval 10 -TraceDetail compact -Cuda -LiveOutput"
