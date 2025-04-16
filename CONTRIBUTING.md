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

Por favor, respeite a estrutura de pastas existente:

```
cazalberto/
├── bot.py                # Arquivo principal para iniciar o bot
├── config.py             # Configurações globais
├── utils.py              # Funções utilitárias
├── cogs/                 # Módulos de comandos organizados por categoria
│   ├── audio_commands.py
│   ├── playlist_commands.py
│   ├── wow_commands.py
│   └── misc_commands.py
├── data/                 # Pasta para armazenar dados
└── audio_clips/          # Pasta onde os áudios são armazenados
```

## Guidelines de código

- Siga as convenções PEP 8 para código Python
- Use docstrings para documentar funções, classes e métodos
- Escreva mensagens de commit claras e descritivas
- Adicione comentários quando necessário para explicar trechos complexos

## Adicionando novos comandos

Para adicionar um novo comando:

1. Adicione o comando ao cog apropriado, ou crie um novo cog se necessário
2. Documente o comando no arquivo README.md
3. Teste o comando antes de enviar

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
