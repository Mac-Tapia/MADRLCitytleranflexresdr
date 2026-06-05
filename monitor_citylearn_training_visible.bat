@echo off
title CityLearn MADRL training monitor
cd /d "%~dp0"
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File scripts\monitor_citylearn_training_visible.ps1 -OutputRoot outputs\citylearn_v3_madrl_iquitos_official_full_cuda_visible_relaunch_20260602_222217 -RefreshSeconds 30
