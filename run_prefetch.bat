@echo off
cd /d %~dp0

:: Run semantic_prefetch.py using venv python
".venv\Scripts\python.exe" semantic_prefetch.py