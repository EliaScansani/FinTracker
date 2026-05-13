@echo off
:: Questo file viene eseguito dal Task Scheduler di Windows ogni mattina.
:: Attiva il virtual environment e lancia lo scheduler Python.

:: Vai nella cartella del progetto (modifica il percorso con il tuo)
cd /d "C:\Users\scans\Desktop\tempo_libero\FinTracker"

:: Attiva il virtual environment
call venv\Scripts\activate

:: Esegui lo scheduler
python scheduler.py

:: Disattiva il venv
deactivate