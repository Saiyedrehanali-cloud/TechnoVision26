@echo off
echo ========================================================
echo   Launching ASR Simulator Live Dashboard...
echo   Opening http://localhost:8000 in your browser
echo ========================================================
start http://localhost:8000
python iot_asr_demo.py live
pause
