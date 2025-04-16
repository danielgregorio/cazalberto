import json
import os
import logging

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Arquivo de comandos
COMMANDS_FILE = "commands.json"
BACKUP_FILE = "commands_backup.json"

def limpar_duplicatas():
    """Limpa comandos duplicados do arquivo commands.json"""
    
    # Verifica se o arquivo existe
    if not os.path.exists(COMMANDS_FILE):
        logging.error(f"❌ Arquivo {COMMANDS_FILE} não encontrado!")
        return
    
    # Faz um backup antes de modificar
    try:
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            commands = json.load(f)
        
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(commands, f, indent=4, ensure_ascii=False)
        
        logging.info(f"✅ Backup criado em {BACKUP_FILE}")
    except Exception as e:
        logging.error(f"❌ Erro ao criar backup: {e}")
        return
    
    # Analisa os comandos para identificar duplicatas
    comando_para_caminho = {}
    caminhos_para_comandos = {}
    comandos_duplicados = {}
    
    # Primeira passagem: identificar duplicatas
    for comando, caminho in commands.items():
        # Normaliza o caminho (remove espaços extras, etc.)
        caminho = caminho.strip()
        
        # Verifica se o comando já existe
        if comando in comando_para_caminho:
            if comando not in comandos_duplicados:
                comandos_duplicados[comando] = [comando_para_caminho[comando]]
            comandos_duplicados[comando].append(caminho)
        else:
            comando_para_caminho[comando] = caminho
        
        # Registra comandos que apontam para o mesmo arquivo
        if caminho not in caminhos_para_comandos:
            caminhos_para_comandos[caminho] = []
        caminhos_para_comandos[caminho].append(comando)
    
    # Mostra estatísticas
    total_comandos = len(commands)
    comandos_unicos = len(comando_para_caminho)
    caminhos_unicos = len(caminhos_para_comandos)
    
    logging.info(f"📊 Estatísticas:")
    logging.info(f"  Total de comandos: {total_comandos}")
    logging.info(f"  Comandos únicos: {comandos_unicos}")
    logging.info(f"  Caminhos únicos: {caminhos_unicos}")
    logging.info(f"  Comandos duplicados: {len(comandos_duplicados)}")
    
    # Mostrar duplicatas (limitado a 20 para não sobrecarregar o console)
    if comandos_duplicados:
        logging.info("🔄 Exemplos de comandos duplicados:")
        count = 0
        for comando, caminhos in comandos_duplicados.items():
            logging.info(f"  '{comando}' tem {len(caminhos)} entradas diferentes:")
            for caminho in caminhos[:3]:  # Mostra até 3 caminhos por comando
                logging.info(f"    - {caminho}")
            count += 1
            if count >= 20:
                logging.info(f"  ... e mais {len(comandos_duplicados) - 20} comandos duplicados")
                break
    
    # Mostrar caminhos com múltiplos comandos (limitado a 20)
    multi_comandos = {caminho: cmds for caminho, cmds in caminhos_para_comandos.items() if len(cmds) > 1}
    if multi_comandos:
        logging.info(f"🔀 Caminhos com múltiplos comandos: {len(multi_comandos)}")
        count = 0
        for caminho, cmds in multi_comandos.items():
            logging.info(f"  '{caminho}' tem {len(cmds)} comandos diferentes:")
            for cmd in cmds[:3]:  # Mostra até 3 comandos por caminho
                logging.info(f"    - {cmd}")
            count += 1
            if count >= 20:
                logging.info(f"  ... e mais {len(multi_comandos) - 20} caminhos com múltiplos comandos")
                break
    
    # Perguntar se deseja limpar duplicatas
    choice = input("\nDeseja remover duplicatas e manter apenas uma entrada por comando? (s/n): ")
    if choice.lower() != 's':
        logging.info("❌ Operação cancelada pelo usuário.")
        return
    
    # Cria um novo dicionário sem duplicatas
    commands_cleaned = {}
    for comando, caminho in comando_para_caminho.items():
        commands_cleaned[comando] = caminho
    
    # Salva o arquivo limpo
    try:
        with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(commands_cleaned, f, indent=4, ensure_ascii=False)
        
        logging.info(f"✅ Arquivo {COMMANDS_FILE} limpo com sucesso!")
        logging.info(f"  Antes: {total_comandos} comandos")
        logging.info(f"  Depois: {len(commands_cleaned)} comandos")
        logging.info(f"  Removidos: {total_comandos - len(commands_cleaned)} duplicatas")
    except Exception as e:
        logging.error(f"❌ Erro ao salvar arquivo limpo: {e}")

if __name__ == "__main__":
    limpar_duplicatas()
    input("\nPressione Enter para sair...")
