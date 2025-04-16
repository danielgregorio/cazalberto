# Cazalberto Discord Bot 🤖🎵

## Descrição
Cazalberto é um bot de Discord personalizado que permite reproduzir clipes de áudio e executar comandos divertidos.

## Pré-requisitos
- Python 3.9+
- FFmpeg instalado no sistema

## Instalação do FFmpeg

### Windows
1. Baixe o FFmpeg de: https://github.com/BtbN/FFmpeg-Builds/releases
2. Baixe a versão "ffmpeg-master-latest-win64-gpl.zip"
3. Extraia o zip
4. Adicione a pasta `bin` ao PATH do sistema:
   - Abra "Variáveis de Ambiente"
   - Em "Variáveis do Sistema", edite "Path"
   - Adicione o caminho completo para a pasta `bin` do FFmpeg
   - Exemplo: `C:\ffmpeg\bin`

### macOS (usando Homebrew)
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

## Configuração do Projeto

1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/cazalberto.git
cd cazalberto
```

2. Crie um ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências
```bash
pip install -r requirements.txt
```

4. Configuração do Token do Discord
- Crie um arquivo `.env` na raiz do projeto
- Adicione seu token do Discord:
```
DISCORD_TOKEN=seu_token_discord_aqui
```

## Executando o Bot
```bash
python bot.py
```

## Comandos Disponíveis
- `/tocar <comando>`: Toca um áudio previamente salvo
- `/aprender <comando> <url>`: Adiciona um novo áudio
- `/aprendido`: Lista áudios salvos
- `/esquecer <comando>`: Remove um áudio
- `/piada`: Conta uma piada aleatória
- `/sair`: Sai do canal de voz

## Solução de Problemas
- Certifique-se de que o FFmpeg está corretamente instalado e no PATH
- Verifique o arquivo `bot.log` para detalhes de erros
- Confirme que todas as dependências estão instaladas corretamente

## Contribuição
1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona Nova Funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

## Licença
MIT License (veja o arquivo LICENSE para detalhes completos)

## Créditos
Desenvolvido por Daniel Gregorio
