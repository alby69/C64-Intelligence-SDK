@echo off
setlocal enabledelayedexpansion

set VENV_PYTHON=.venv\Scripts\python
set VENV_PIP=.venv\Scripts\pip

goto %1

:: ── HELP ────────────────────────────────────
:help
:--help
:-h
echo.
echo C64 Intelligence Studio — Comandi Windows
echo.
echo   make.bat setup           Installa TUTTO (venv, editor, backend, frontend)
echo   make.bat venv            Crea .venv virtual environment
echo   make.bat backend-deps    Installa dipendenze backend
echo   make.bat frontend-deps   Installa dipendenze frontend
echo   make.bat editor-build    Installa editor in .venv
echo.
echo   make.bat ide-backend     Avvia backend (FastAPI :8000)
echo   make.bat ide-frontend    Avvia frontend (Vite :5173)
echo   make.bat plugins         Elenca plugin
echo   make.bat plugin-test     Test plugin system
echo   make.bat editor-test     Test editor
echo   make.bat geckos-build    Compila GeckOS-NG
echo   make.bat geckos-status   Stato build GeckOS
echo   make.bat clean           Pulisci output\
echo.
echo   make.bat docker-build    Build immagini Docker
echo   make.bat docker-run      Avvia TUI legacy
echo.
goto :eof

:: ── SETUP ───────────────────────────────────
:setup
call :venv
call :editor-build
call :backend-deps
call :frontend-deps
echo.
echo Setup completato!
goto :eof

:: ── VENV ────────────────────────────────────
:venv
if exist .venv\Scripts\python.exe (
    echo .venv gia' esistente.
    goto :eof
)
echo Creazione ambiente virtuale...
python -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo ERRORE: python non trovato. Assicurati che Python sia installato.
    exit /b 1
)
echo .venv creato.
goto :eof

:: ── EDITOR BUILD ────────────────────────────
:editor-build
call :venv
%VENV_PIP% install -e "editor[test]"
if %ERRORLEVEL% neq 0 echo ERRORE: editor-build fallito.
goto :eof

:: ── EDITOR TEST ─────────────────────────────
:editor-test
call :venv
%VENV_PYTHON% -m pytest editor/tests/ -v
goto :eof

:: ── BACKEND DEPS ────────────────────────────
:backend-deps
call :venv
%VENV_PIP% install -r services/core_service/requirements.txt 2>nul
if %ERRORLEVEL% neq 0 (
    %VENV_PIP% install fastapi uvicorn pydantic
)
if %ERRORLEVEL% neq 0 echo ERRORE: backend-deps fallito.
goto :eof

:: ── BACKEND START ───────────────────────────
:ide-backend
:backend-start
echo.
echo ============================================
echo  Backend in ascolto su http://localhost:8000
echo  API docs: http://localhost:8000/docs
echo ============================================
call :venv
cd services\core_service
..\..\.venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
goto :eof

:: ── FRONTEND DEPS ───────────────────────────
:frontend-deps
echo Installazione dipendenze frontend...
cd frontend
call npm install
cd ..
if %ERRORLEVEL% neq 0 echo ERRORE: frontend-deps fallito.
goto :eof

:: ── FRONTEND START ──────────────────────────
:ide-frontend
:frontend-start
echo.
echo ============================================
echo  Frontend in ascolto su http://localhost:5173
echo  Assicurati che il backend sia in esecuzione:
echo    make.bat ide-backend
echo ============================================
cd frontend
call npm run dev
goto :eof

:: ── PLUGINS ─────────────────────────────────
:plugins
call :venv
%VENV_PYTHON% scripts/list_plugins.py
goto :eof

:: ── PLUGIN TEST ─────────────────────────────
:plugin-test
call :venv
%VENV_PYTHON% -m pytest test_plugin_system.py -v
goto :eof

:: ── GECKOS ──────────────────────────────────
:geckos-build
call :venv
%VENV_PYTHON% plugins/geckos/wrapper.py build
goto :eof

:geckos-status
call :venv
%VENV_PYTHON% plugins/geckos/wrapper.py status
goto :eof

:: ── CLEAN ───────────────────────────────────
:clean
if exist output\ rmdir /s /q output
echo output\ pulito.
goto :eof

:: ── DOCKER ──────────────────────────────────
:docker-build
docker compose build
goto :eof

:docker-run
docker compose run --rm pyc64
goto :eof

:: ── DEFAULT ─────────────────────────────────
echo Comando sconosciuto: %1
echo.
echo Usa: make.bat setup^|ide-backend^|ide-frontend^|plugins^|help
echo Per l'elenco completo: make.bat help
goto :eof
