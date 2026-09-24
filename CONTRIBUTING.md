# Contribuindo para o Cazalberto

Obrigado pelo seu interesse em contribuir para o Cazalberto! Este documento fornece algumas diretrizes para contribuir com o projeto.

## Como contribuir

1. **Fork** o repositório
2. **Clone** o repositório forkado para sua máquina local
3. **Crie uma branch** para a sua feature ou correção
4. **Desenvolva** sua feature ou correção
5. **Teste** suas alterações
6. **Commit** suas alterações com mensagens claras
7. **Push** para a sua branch
8. Envie um **Pull Request** para o repositório principal

## Estrutura de pastas

O código fica no pacote `cazalberto/` (veja a seção "Estrutura" do [README](README.md)):

- **Regras e dados** ficam em `audio/`, `playlists.py` e `storage.py`, sem depender do Discord, para poderem ser testados.
- **Comandos** ficam em `cogs/` e só fazem a ponte entre o Discord e esses serviços.
- **Erros esperados** (entrada inválida, áudio que não existe) são levantados como `UserError("mensagem")`.
  O bot mostra a mensagem ao usuário; qualquer outro erro vai para o log.

## Ambiente de desenvolvimento

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
ruff format .
```

A CI roda esses mesmos comandos em todo pull request.

## Adicionando novos comandos

1. Coloque o comando no cog certo em `cazalberto/cogs/`, ou crie um cog novo e inclua-o em `EXTENSIONS` (`cazalberto/bot.py`).
2. Se tiver lógica que não depende do Discord, coloque-a num módulo à parte e escreva testes em `tests/`.
3. Atualize a tabela de comandos do README. O `/ajuda` é gerado automaticamente.
4. Depois de mudar comandos slash, rode `!sync aqui` (ou `python -m cazalberto --sync`).

## Reportando bugs

Se você encontrar um bug, por favor abra uma issue com os seguintes detalhes:

- Descrição clara do bug
- Passos para reproduzir o problema
- Comportamento esperado
- Comportamento atual
- Screenshots, se aplicável
- Informações do ambiente (sistema operacional, versão do Python, etc.)

## Solicitando features

Se você tem uma ideia para uma nova feature, por favor abra uma issue com os seguintes detalhes:

- Descrição clara da feature
- Por que essa feature seria útil
- Como você imagina que a feature funcionaria
