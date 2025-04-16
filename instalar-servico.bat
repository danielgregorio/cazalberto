@echo off
echo ==============================================
echo  Instalando Cazalberto como tarefa agendada
echo ==============================================
echo.

REM Verifica se está sendo executado como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERRO: Este script precisa ser executado como Administrador!
    echo Por favor, clique com o botão direito e selecione "Executar como administrador".
    echo.
    pause
    exit /b 1
)

REM Caminhos específicos para sua instalação
set BOT_DIR=C:\Users\Daniel\OneDrive\Projetos\cazalberto\
set BOT_SCRIPT=%BOT_DIR%bot.py

echo Diretório do Bot: %BOT_DIR%
echo Script do Bot: %BOT_SCRIPT%

echo Criando tarefa agendada para iniciar o Cazalberto na inicialização...

REM Usando py em vez do caminho completo para python
schtasks /create /tn "CazalbertoBot" /tr "cmd /c cd /d %BOT_DIR% && python bot.py" /sc onstart /ru SYSTEM /f

if %errorLevel% neq 0 (
    echo ERRO: Não foi possível criar a tarefa agendada.
    pause
    exit /b 1
) else (
    echo Tarefa criada com sucesso!
    echo O bot Cazalberto iniciará automaticamente quando o sistema for iniciado.
    echo.
    echo Iniciando o bot agora...
    
    REM Inicia o bot em uma nova janela
    start cmd /c "cd /d %BOT_DIR% && python bot.py"
    
    echo.
    echo Concluído!
)

pause