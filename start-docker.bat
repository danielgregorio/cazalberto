@echo off
REM Inicia o Cazalberto com Docker no Windows.
cd /d "%~dp0"

docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo X Docker nao esta instalado. Instale o Docker Desktop primeiro.
    pause
    exit /b 1
)

if not exist .env (
    copy .env.example .env > nul
    echo ! Criei o arquivo .env. Edite-o, coloque seu DISCORD_TOKEN e rode de novo.
    pause
    exit /b 1
)

findstr /R /C:"^DISCORD_TOKEN=..*" .env > nul
if %errorlevel% neq 0 (
    echo X DISCORD_TOKEN esta vazio no .env.
    pause
    exit /b 1
)

if not exist data mkdir data
if not exist audio_clips mkdir audio_clips
if not exist wow-music mkdir wow-music

echo Iniciando Cazalberto...
docker compose up -d --build
if %errorlevel% neq 0 (
    echo X Erro ao iniciar. Veja os logs: docker compose logs
    pause
    exit /b 1
)

echo.
echo V Cazalberto iniciado!
echo   Logs:      docker compose logs -f
echo   Parar:     docker compose down
echo   Reiniciar: docker compose restart
echo.
echo Use !sync no Discord (como administrador) para registrar os comandos slash.
pause
