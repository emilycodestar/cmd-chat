@echo off
echo ====================================
echo   CMD CHAT - Reiniciar Servidor
echo ====================================
echo.
echo Parando processos antigos...
taskkill /F /FI "WINDOWTITLE eq *cmd_chat.py serve*" 2>nul
timeout /t 2 /nobreak >nul
echo.
echo Iniciando servidor...
start "CMD CHAT Server" cmd /k "C:\Users\sousa\Projects\cmd-chat\.venv\Scripts\python.exe cmd_chat.py serve 127.0.0.1 1000 --password TestPass123"
echo.
echo Servidor iniciado em nova janela!
echo.
pause
