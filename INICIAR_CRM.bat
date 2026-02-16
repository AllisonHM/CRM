@echo off
echo ========================================
echo    INICIAR CRM - Sistema Completo
echo ========================================
echo.
echo [1] Este script vai:
echo     - Iniciar o CRM em http://127.0.0.1:5000
echo.
echo [2] Em OUTRO terminal, execute:
echo     ngrok http 5000
echo.
echo [3] Configure o webhook no Z-API com a URL do ngrok
echo.
echo ========================================
echo.
pause
echo.
echo Iniciando CRM...
echo.
C:\Users\Allison\AppData\Local\Programs\Python\Python313\python.exe "C:\Users\Allison\Desktop\CRM completo\CRM\CRM.py"
