@echo off
echo ========================================
echo    NGROK - Expor CRM para Internet
echo ========================================
echo.
echo Este script inicia o ngrok para expor o CRM
echo.
echo Certifique-se de que:
echo [1] O CRM esta rodando em http://127.0.0.1:5000
echo [2] Voce instalou o ngrok em C:\ngrok\
echo [3] Voce configurou o token do ngrok
echo.
echo ========================================
echo.

REM Verifica se ngrok existe
if exist "C:\ngrok\ngrok.exe" (
    echo Iniciando ngrok...
    echo.
    cd /d "C:\ngrok"
    ngrok http 5000
) else (
    echo.
    echo ERRO: ngrok.exe nao encontrado em C:\ngrok\
    echo.
    echo Por favor:
    echo 1. Baixe ngrok em https://ngrok.com/download
    echo 2. Extraia ngrok.exe em C:\ngrok\
    echo 3. Configure o token: ngrok config add-authtoken SEU_TOKEN
    echo.
    echo Se instalou em outro local, edite este arquivo .bat
    echo e altere o caminho C:\ngrok\
    echo.
    pause
)
