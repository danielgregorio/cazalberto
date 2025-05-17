@echo off
REM Script para iniciar Cazalberto em Docker no Windows

REM Verifica se o Docker está instalado
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo X Docker nao esta instalado. Por favor, instale o Docker Desktop primeiro.
    pause
    exit /b 1
)

REM Verifica se o Docker Compose está instalado
docker-compose --version > nul 2>&1
if %errorlevel% neq 0 (
    echo X Docker Compose nao esta instalado. 
    pause
    exit /b 1
)

REM Verifica se o arquivo .env existe
if not exist .env (
    echo ! Arquivo .env nao encontrado. Criando...
    echo DISCORD_TOKEN=> .env
    echo V Arquivo .env criado. Por favor, edite-o e adicione seu token do Discord.
    pause
    exit /b 1
)

REM Verifica se o token está configurado
findstr /C:"DISCORD_TOKEN=" .env > nul
if %errorlevel% neq 0 (
    echo X Token do Discord nao configurado no arquivo .env
    echo Por favor, edite o arquivo .env e adicione seu token: DISCORD_TOKEN=seu_token_aqui
    pause
    exit /b 1
)

REM Cria diretórios necessários
if not exist audio_clips mkdir audio_clips
if not exist wow-music\legion mkdir wow-music\legion
if not exist wow-music\classic mkdir wow-music\classic
if not exist wow-music\wotlk mkdir wow-music\wotlk

REM Verifica se commands.json e playlists.json existem, e cria se não existirem
if not exist commands.json (
    echo {}> commands.json
    echo V Arquivo commands.json criado.
)

if not exist playlists.json (
    echo {"playlists":[]}>playlists.json
    echo V Arquivo playlists.json criado.
)

REM Inicia o container
echo ==============================================
echo          Iniciando Cazalberto...
echo ==============================================
docker-compose up -d

REM Verifica se iniciou com sucesso
if %errorlevel% equ 0 (
    echo.
    echo V Cazalberto iniciado com sucesso!
    echo.
    echo Comandos uteis:
    echo   - Ver logs: docker-compose logs
    echo   - Parar bot: docker-compose down
    echo   - Reiniciar: docker-compose restart
    echo.
    echo Use !sync no Discord para sincronizar os comandos slash.
) else (
    echo X Erro ao iniciar Cazalberto. Verifique os logs: docker-compose logs
)

pause
