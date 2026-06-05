@echo off
title CityLearn MADRL LIVE OUTPUT
cd /d "%~dp0"
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -Command "$ts = Get-Date -Format 'yyyyMMdd_HHmmss'; & scripts\run_citylearn_v3_full_training_visible.ps1 -OutputRoot ('outputs\citylearn_v3_madrl_iquitos_official_full_cuda_LIVE_' + $ts) -Scenario ALL -Seed 0 -EpisodeTimeSteps 8760 -Episodes 5 -TorchThreads 12 -LiveProgressInterval 250 -Cuda -LiveOutput"
