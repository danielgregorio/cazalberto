import discord
from discord import ui
import os
import logging
from discord.ext import commands
from discord import app_commands
import aiohttp
import aiofiles
import difflib
import math

from config import AUDIO_FOLDER, COMMANDS_FILE, WOW_OST_FOLDER, WOW_EXPANSION_DIRS, WOW_ENABLED
from utils import load_json, save_json, download_file

# Vista de botões para áudios
class AudioButtonsView(ui.View):
    """View com botões para reprodução direta de áudios."""
    
    def __init__(self, cog, audio_commands, timeout=180, is_wow=False, wow_prefix=None, page=0, total_pages=1):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.audio_commands = audio_commands
        self.is_wow = is_wow
        self.wow_prefix = wow_prefix
        self.page = page
        self.total_pages = total_pages
        
        # Botões de navegação (apenas se houver mais de uma página)
        if total_pages > 1:
            # Botão Anterior (desativado na primeira página)
            self.add_item(ui.Button(
                style=discord.ButtonStyle.secondary,
                label="◀️ Página Anterior",
                custom_id="prev_page",
                disabled=(page == 0),
                row=0
            ))
            
            # Indicador de página
            self.add_item(ui.Button(
                style=discord.ButtonStyle.secondary,
                label=f"Página {page+1}/{total_pages}",
                custom_id="page_indicator",
                disabled=True,
                row=0
            ))
            
            # Botão Próxima (desativado na última página)
            self.add_item(ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Próxima Página ▶️",
                custom_id="next_page",
                disabled=(page == total_pages - 1),
                row=0
            ))
        
        # Índice inicial para esta página
        start_idx = page * 15  # 15 botões por página (5 botões por linha, 3 linhas)
        end_idx = min(start_idx + 15, len(audio_commands))
        
        # Adiciona botões para os áudios (5 por linha)
        for i, cmd in enumerate(audio_commands[start_idx:end_idx]):
            # Determina a linha do botão (considerando que os botões de navegação usam a linha 0)
            row = (i // 5) + 1  # +1 porque a linha 0 é para navegação
            
            # Para comandos longos, trunca o texto para caber no botão
            display_name = cmd
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."
            
            # Cria o botão
            play_button = ui.Button(
                style=discord.ButtonStyle.primary,
                label=display_name,
                custom_id=f"play_{cmd}",
                row=row
            )
            
            self.add_item(play_button)
    
    async def interaction_check(self, interaction):
        """Chamado quando um botão é clicado."""
        custom_id = interaction.data["custom_id"]
        
        # Navegação entre páginas
        if custom_id == "prev_page":
            if self.page > 0:
                new_page = self.page - 1
                
                # Cria uma nova view com a página anterior
                new_view = AudioButtonsView(
                    self.cog, 
                    self.audio_commands, 
                    is_wow=self.is_wow, 
                    wow_prefix=self.wow_prefix,
                    page=new_page, 
                    total_pages=self.total_pages
                )
                
                # Atualiza a mensagem com a nova view
                await interaction.response.edit_message(view=new_view)
                return True
        
        elif custom_id == "next_page":
            if self.page < self.total_pages - 1:
                new_page = self.page + 1
                
                # Cria uma nova view com a próxima página
                new_view = AudioButtonsView(
                    self.cog, 
                    self.audio_commands, 
                    is_wow=self.is_wow, 
                    wow_prefix=self.wow_prefix,
                    page=new_page, 
                    total_pages=self.total_pages
                )
                
                # Atualiza a mensagem com a nova view
                await interaction.response.edit_message(view=new_view)
                return True
        
        # Botão de reprodução
        elif custom_id.startswith("play_"):
            # Extrai o nome do comando de áudio
            cmd_name = custom_id[5:]  # Remove o prefixo "play_"
            
            # Para áudios do WoW, adiciona o prefixo da expansão
            if self.is_wow and self.wow_prefix:
                full_cmd = f"{self.wow_prefix}-{cmd_name}"
            else:
                full_cmd = cmd_name
            
            # Defere a interação para processar o áudio
            await interaction.response.defer(ephemeral=True)
            
            # Toca o áudio
            await self.cog.play_audio(interaction, full_cmd)
        
        return True

class AudioCommands(commands.Cog):
    """Comandos para reprodução e gerenciamento de áudio."""
    
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = load_json(COMMANDS_FILE)
        
        # Verificando se recursos do WoW estão disponíveis
        self.wow_mode = WOW_ENABLED
        if self.wow_mode:
            logging.info(f"✅ Modo WoW ativado! Pasta encontrada: {WOW_OST_FOLDER}")
        else:
            logging.warning(f"⚠️ Modo WoW desativado. Pasta não encontrada: {WOW_OST_FOLDER}")
        
        # Mapeamento de expansões
        self.expansion_prefixes = {
            "0": "classic", "1": "tbc", "2": "wotlk", "3": "cata", 
            "4": "mop", "5": "wod", "6": "legion", "7": "bfa",
            "8": "sl", "9": "df", "10": "tww", "11": "undermine",
            
            "classic": "classic", "vanilla": "classic",
            "tbc": "tbc", "burning": "tbc", "crusade": "tbc",
            "wotlk": "wotlk", "lich": "wotlk", "wrath": "wotlk",
            "cata": "cata", "cataclysm": "cata",
            "mop": "mop", "mists": "mop", "pandaria": "mop",
            "wod": "wod", "draenor": "wod", "warlords": "wod",
            "legion": "legion",
            "bfa": "bfa", "battle": "bfa", "azeroth": "bfa",
            "sl": "sl", "shadowlands": "sl",
            "df": "df", "dragonflight": "df",
            "tww": "tww", "war": "tww", "within": "tww",
            "undermine": "undermine"
        }
        
        # Nomes amigáveis para exibição
        self.expansion_names = {
            "classic": "World of Warcraft: Classic",
            "tbc": "The Burning Crusade",
            "wotlk": "Wrath of the Lich King",
            "cata": "Cataclysm",
            "mop": "Mists of Pandaria",
            "wod": "Warlords of Draenor",
            "legion": "Legion",
            "bfa": "Battle for Azeroth",
            "sl": "Shadowlands",
            "df": "Dragonflight",
            "tww": "The War Within",
            "undermine": "Undermine"
        }
        
        # Cache para arquivos encontrados - apenas inicializado se o modo WoW estiver ativo
        if self.wow_mode:
            self.wow_audio_cache = {}
        
    async def play_audio(self, interaction, comando):
        """Método universal para tocar áudio, usado pelo comando /tocar e pelos botões."""
        # Log para debug
        logging.info(f"🎵 Tocando áudio: {comando}")
        
        # Verificar primeiro nos comandos personalizados
        if comando in self.custom_commands:
            filepath = self.custom_commands[comando]
            if not os.path.exists(filepath):
                await interaction.followup.send(f"❌ O arquivo `{comando}` não foi encontrado.", ephemeral=True)
                return
            
            # Obtém ou cria uma conexão de voz
            try:
                vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
                if not vc or not vc.is_connected():
                    if interaction.user.voice:
                        vc = await interaction.user.voice.channel.connect()
                    else:
                        await interaction.followup.send("❌ Você precisa estar em um canal de voz!", ephemeral=True)
                        return
                
                vc.stop()
                vc.play(discord.FFmpegPCMAudio(filepath))
                await interaction.followup.send(f"🎵 Tocando: `{comando}`", ephemeral=True)
                return
            except Exception as e:
                logging.error(f"❌ Erro ao tocar áudio: {e}")
                await interaction.followup.send(f"❌ Erro ao tocar áudio: {str(e)}", ephemeral=True)
                return
        
        # Se o comando não existe nos personalizados, verificamos se é um comando do WoW
        wow_filepath = None
        if self.wow_mode:
            # Tenta encontrar o arquivo
            wow_filepath = self.find_wow_audio(comando)
            
            # Registra o resultado
            if wow_filepath:
                logging.info(f"✅ Encontrado arquivo WoW: {wow_filepath}")
            else:
                logging.info(f"❌ Arquivo WoW não encontrado para: {comando}")
        
        # Se encontramos um arquivo WoW, tocamos
        if wow_filepath and os.path.exists(wow_filepath):
            # Conecta ao canal de voz
            try:
                vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
                if not vc or not vc.is_connected():
                    if interaction.user.voice:
                        vc = await interaction.user.voice.channel.connect()
                    else:
                        await interaction.followup.send("❌ Você precisa estar em um canal de voz!", ephemeral=True)
                        return
                
                # Toca o áudio
                if vc.is_playing():
                    vc.stop()
                    
                vc.play(discord.FFmpegPCMAudio(wow_filepath))
                
                filename = os.path.basename(wow_filepath)
                logging.info(f"🎵 Tocando arquivo WoW: {filename}")
                await interaction.followup.send(f"🎵 Tocando WoW OST: `{comando}` (arquivo: {filename})", ephemeral=True)
                return
            except Exception as e:
                logging.error(f"❌ Erro ao tocar áudio WoW: {e}")
                await interaction.followup.send(f"❌ Erro ao tocar áudio: {str(e)}", ephemeral=True)
                return
        
        # Se chegou aqui, o comando não foi encontrado
        await interaction.followup.send(f"❌ Comando `{comando}` não encontrado.", ephemeral=True)
    
    def find_similar_commands(self, input_command, commands, threshold=0.6, max_suggestions=5):
        """
        Find similar commands with a fuzzy match
        
        Args:
            input_command (str): User's input command
            commands (dict/list): Available commands
            threshold (float): Similarity threshold (0-1)
            max_suggestions (int): Maximum number of suggestions
        
        Returns:
            list: Similar commands suggestions
        """
        if isinstance(commands, dict):
            commands = list(commands.keys())
        
        # Usa difflib para encontrar comandos similares
        suggestions = [
            cmd for cmd in commands 
            if difflib.SequenceMatcher(None, input_command.lower(), cmd.lower()).ratio() >= threshold
        ]
        
        # Ordena por similaridade e limita o número de sugestões
        suggestions.sort(
            key=lambda cmd: difflib.SequenceMatcher(None, input_command.lower(), cmd.lower()).ratio(), 
            reverse=True
        )
        
        return suggestions[:max_suggestions]
    
    def is_wow_command(self, command):
        """Verifica se um comando parece ser um comando do WoW."""
        # Verifica pelo formato padrão: expansão-nome
        for prefix in self.expansion_prefixes.values():
            if command.startswith(f"{prefix}-"):
                return True
                
        # Verifica pelos prefixos numéricos 
        for prefix_num in ["0-", "1-", "2-", "3-", "4-", "5-", "6-", "7-", "8-", "9-", "10-", "11-"]:
            if command.startswith(prefix_num):
                return True
                
        return False
    
    def find_wow_audio(self, command):
        """
        Tenta encontrar um arquivo de áudio do WoW com base no comando.
        Retorna o caminho completo do arquivo se encontrado, ou None caso contrário.
        """
        if not self.wow_mode:
            return None
            
        # Verifica o cache primeiro
        if command in self.wow_audio_cache:
            return self.wow_audio_cache[command]
            
        # Verifica se o comando segue o formato expansão-nome
        parts = command.split('-', 1)
        if len(parts) != 2:
            return None
            
        prefix, name = parts
        
        # Verifica se o prefixo é uma expansão válida
        if prefix not in self.expansion_prefixes:
            # Tenta obter o prefixo através do dicionário
            if prefix not in self.expansion_prefixes:
                return None
            prefix = self.expansion_prefixes[prefix]
        else:
            prefix = self.expansion_prefixes[prefix]
        
        # Verifica se temos diretórios para essa expansão
        if prefix not in WOW_EXPANSION_DIRS:
            return None
            
        # Busca em todos os diretórios da expansão
        for exp_dir in WOW_EXPANSION_DIRS[prefix]:
            dir_path = os.path.join(WOW_OST_FOLDER, exp_dir)
            
            # Verifica se o diretório existe
            if not os.path.exists(dir_path):
                continue
                
            try:
                # Busca arquivos que contenham o nome (case insensitive)
                for file in os.listdir(dir_path):
                    file_name, file_ext = os.path.splitext(file)
                    if file_ext.lower() != '.mp3':
                        continue
                    
                    # Tenta vários métodos de correspondência
                    # 1. Correspondência direta com o nome do arquivo
                    if name.lower() in file_name.lower():
                        filepath = os.path.join(dir_path, file)
                        # Armazena no cache para uso futuro
                        self.wow_audio_cache[command] = filepath
                        return filepath
                        
                    # 2. Verifica removendo números do início (ex: "01. Track Name.mp3")
                    if ". " in file_name:
                        clean_name = file_name.split(". ", 1)[1].lower()
                        if name.lower() in clean_name:
                            filepath = os.path.join(dir_path, file)
                            # Armazena no cache para uso futuro
                            self.wow_audio_cache[command] = filepath
                            return filepath
                            
                    # 3. Tenta substituir hífens por espaços para correspondência
                    name_with_spaces = name.replace("-", " ").lower()
                    if name_with_spaces in file_name.lower():
                        filepath = os.path.join(dir_path, file)
                        # Armazena no cache para uso futuro
                        self.wow_audio_cache[command] = filepath
                        return filepath
                        
                    # 4. Tenta substituir hífens por espaços no nome limpo
                    if ". " in file_name:
                        clean_name = file_name.split(". ", 1)[1].lower()
                        if name_with_spaces in clean_name:
                            filepath = os.path.join(dir_path, file)
                            # Armazena no cache para uso futuro
                            self.wow_audio_cache[command] = filepath
                            return filepath
            except Exception as e:
                logging.error(f"❌ Erro ao buscar em {dir_path}: {e}")
                
        return None
    
    @app_commands.command(name="tocar", description="Toca um áudio salvo.")
    async def tocar(self, ctx: discord.Interaction, comando: str):
        """Toca um áudio previamente salvo com suporte para áudios do WoW."""
        # Log para debug
        logging.info(f"🎵 Comando tocar: {comando}")
        
        # Usamos defer() para evitar timeout da interação
        await ctx.response.defer()
        
        # Chamamos o método universal de tocar áudio
        await self.play_audio(ctx, comando)
    
    @app_commands.command(name="wow", description="Lista os áudios de uma expansão específica do WoW.")
    async def aprendido_wow(self, ctx: discord.Interaction, expansao: str):
        """Lista os áudios de uma expansão específica do World of Warcraft com botões interativos."""
        # Verificamos primeiro se o modo WoW está ativado
        if not self.wow_mode:
            await ctx.response.send_message(
                "❌ O modo WoW está desativado porque a pasta não foi encontrada.\n"
                f"Pasta esperada: `{WOW_OST_FOLDER}`"
            )
            return
            
        logging.info(f"🔍 Comando aprendido_wow chamado com expansão: {expansao}")
        
        try:
            # Normaliza a entrada do usuário
            exp_input = expansao.lower().strip()
            
            # Tenta encontrar o prefixo correspondente
            if exp_input not in self.expansion_prefixes:
                available_expansions = "\n".join([
                    f"• {num}: {self.expansion_names[prefix]}" 
                    for num, prefix in [
                        ("0", "classic"), ("1", "tbc"), ("2", "wotlk"), 
                        ("3", "cata"), ("4", "mop"), ("5", "wod"), 
                        ("6", "legion"), ("7", "bfa"), ("8", "sl"), 
                        ("9", "df"), ("10", "tww"), ("11", "undermine")
                    ]
                ])
                
                await ctx.response.send_message(
                    f"❌ Expansão '{expansao}' não reconhecida.\n\n"
                    f"Expansões disponíveis:\n{available_expansions}\n\n"
                    f"Exemplo: `/wow classic` ou `/wow 0`"
                )
                return
            
            # Obtém o prefixo correto
            prefix = self.expansion_prefixes[exp_input]
            logging.info(f"📌 Prefixo encontrado: {prefix}")
            
            # Verifica se temos diretórios para essa expansão
            if prefix not in WOW_EXPANSION_DIRS:
                await ctx.response.send_message(f"❌ Não foram encontrados diretórios para a expansão '{expansao}'.")
                return
            
            # Verifica se os diretórios existem no sistema de arquivos
            existing_dirs = []
            for exp_dir in WOW_EXPANSION_DIRS[prefix]:
                dir_path = os.path.join(WOW_OST_FOLDER, exp_dir)
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    existing_dirs.append(dir_path)
                else:
                    logging.warning(f"⚠️ Diretório não encontrado: {dir_path}")
            
            if not existing_dirs:
                await ctx.response.send_message(
                    f"❌ Nenhum diretório válido encontrado para a expansão '{expansao}'.\n"
                    f"Pastas esperadas: {', '.join([os.path.join(WOW_OST_FOLDER, d) for d in WOW_EXPANSION_DIRS[prefix]])}"
                )
                return
                
            # Lista todos os arquivos da expansão
            all_files = []
            for dir_path in existing_dirs:
                try:
                    files = [f for f in os.listdir(dir_path) if f.lower().endswith('.mp3')]
                    logging.info(f"📂 Encontrados {len(files)} arquivos em {dir_path}")
                    
                    for file in files:
                        file_name, _ = os.path.splitext(file)
                        # Remove números do início (ex: "01. Track Name.mp3")
                        if ". " in file_name:
                            file_name = file_name.split(". ", 1)[1]
                        # Converte espaços em hífens para formato de comando
                        command_name = file_name.lower().replace(" ", "-")
                        all_files.append(command_name)
                except Exception as e:
                    logging.error(f"❌ Erro ao listar diretório {dir_path}: {e}")
            
            logging.info(f"🔢 Encontrados {len(all_files)} áudios para a expansão {prefix}")
            
            if not all_files:
                await ctx.response.send_message(
                    f"❌ Nenhum áudio encontrado para a expansão '{expansao}'.\n"
                    f"Verifique se existem arquivos .mp3 nas pastas:\n"
                    f"{', '.join(existing_dirs)}"
                )
                return
            
            # Ordena os arquivos
            all_files.sort()
            
            # Nome da expansão para exibição
            expansion_title = self.expansion_names.get(prefix, prefix.upper())
            
            # Calcula o número de páginas
            page_size = 15  # 15 botões por página (5 botões por linha, 3 linhas)
            total_pages = math.ceil(len(all_files) / page_size)
            
            # Cria uma view com botões para a primeira página
            view = AudioButtonsView(
                self, 
                all_files, 
                is_wow=True, 
                wow_prefix=prefix,
                page=0, 
                total_pages=total_pages
            )
            
            # Envia a mensagem com os botões
            await ctx.response.send_message(
                f"🎵 Áudios de {expansion_title} ({len(all_files)} no total)\n"
                f"Clique em um botão para tocar:",
                view=view
            )
        
        except Exception as e:
            logging.error(f"❌ Erro no comando aprendido_wow: {e}")
            await ctx.response.send_message(f"❌ Ocorreu um erro ao processar o comando: {str(e)}")

    @app_commands.command(name="aprendido", description="Lista todos os áudios aprendidos.")
    async def aprendido(self, ctx: discord.Interaction):
        """Lista todos os áudios aprendidos com botões interativos."""
        try:
            if not self.custom_commands:
                await ctx.response.send_message("❌ Nenhum áudio foi aprendido ainda.")
                return
            
            # Prepara a lista de comandos
            command_list = sorted(list(self.custom_commands.keys()))
            
            # Calcula o número de páginas
            page_size = 15  # 15 botões por página (5 botões por linha, 3 linhas)
            total_pages = math.ceil(len(command_list) / page_size)
            
            # Cria uma view com botões para a primeira página
            view = AudioButtonsView(
                self, 
                command_list,
                page=0, 
                total_pages=total_pages
            )
            
            # Envia a mensagem com os botões
            await ctx.response.send_message(
                f"🎵 Áudios disponíveis ({len(command_list)} no total)\n"
                f"Clique em um botão para tocar:",
                view=view
            )
            
            # Adiciona mensagem sobre áudios do WoW
            if self.wow_mode:
                await ctx.followup.send(
                    "ℹ️ Para ver os áudios de World of Warcraft, use `/wow [expansão]`.\n"
                    "Exemplo: `/wow classic` ou `/wow wotlk`"
                )
        
        except Exception as e:
            logging.error(f"❌ Erro no comando aprendido: {e}")
            await ctx.response.send_message("❌ Ocorreu um erro ao processar o comando.")

    @app_commands.command(name="aprender", description="Adiciona um novo áudio ao bot.")
    async def aprender(self, ctx: discord.Interaction, comando: str, url: str):
        """Adiciona um novo áudio ao bot a partir de uma URL."""
        comando = comando.lower().strip()
        
        # Verifica se o comando já existe
        if comando in self.custom_commands:
            await ctx.response.send_message(f"❌ O comando `{comando}` já existe!")
            return
        
        # Verifica se o nome do comando é válido
        if not comando or len(comando) > 32:
            await ctx.response.send_message("❌ O nome do comando deve ter entre 1 e 32 caracteres.")
            return
        
        await ctx.response.defer(thinking=True)
        
        try:
            # Garante que a pasta de áudio existe
            os.makedirs(AUDIO_FOLDER, exist_ok=True)
            
            # Nome do arquivo baseado no comando
            filename = f"{comando}.mp3"
            filepath = os.path.join(AUDIO_FOLDER, filename)
            
            # Baixa o arquivo
            success = await download_file(url, filepath)
            
            if not success:
                await ctx.followup.send("❌ Erro ao baixar o arquivo. Verifique se a URL é válida.")
                return
            
            # Adiciona o comando ao dicionário
            self.custom_commands[comando] = filepath
            save_json(COMMANDS_FILE, self.custom_commands)
            
            await ctx.followup.send(f"✅ Comando `{comando}` adicionado com sucesso! Use `/tocar {comando}` para reproduzir.")
        
        except Exception as e:
            logging.error(f"❌ Erro ao aprender comando: {e}")
            await ctx.followup.send(f"❌ Ocorreu um erro: {str(e)}")

    @app_commands.command(name="esquecer", description="Remove um áudio do bot.")
    async def esquecer(self, ctx: discord.Interaction, comando: str):
        """Remove um áudio do bot."""
        comando = comando.lower().strip()
        
        # Verifica se o comando existe
        if comando not in self.custom_commands:
            await ctx.response.send_message(f"❌ O comando `{comando}` não existe!")
            return
        
        try:
            # Obtém o caminho do arquivo
            filepath = self.custom_commands[comando]
            
            # Remove o comando do dicionário
            del self.custom_commands[comando]
            save_json(COMMANDS_FILE, self.custom_commands)
            
            # Tenta excluir o arquivo (apenas se estiver na pasta de áudio do bot)
            if os.path.exists(filepath) and AUDIO_FOLDER in filepath:
                try:
                    os.remove(filepath)
                    await ctx.response.send_message(f"✅ Comando `{comando}` e arquivo removidos com sucesso!")
                except:
                    # Se não conseguir remover o arquivo, pelo menos remove do dicionário
                    await ctx.response.send_message(f"✅ Comando `{comando}` removido do bot. (Arquivo não excluído)")
            else:
                await ctx.response.send_message(f"✅ Comando `{comando}` removido do bot.")
        
        except Exception as e:
            logging.error(f"❌ Erro ao esquecer comando: {e}")
            await ctx.response.send_message(f"❌ Ocorreu um erro: {str(e)}")

    @app_commands.command(name="sair", description="Faz o bot sair do canal de voz.")
    async def sair(self, ctx: discord.Interaction):
        """Faz o bot sair do canal de voz."""
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if vc and vc.is_connected():
            await vc.disconnect()
            await ctx.response.send_message("👋 Saí do canal de voz!")
        else:
            await ctx.response.send_message("❌ Não estou conectado a nenhum canal de voz!")

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(AudioCommands(bot))
