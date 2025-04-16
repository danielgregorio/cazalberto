import discord
import os
import logging
from discord.ext import commands
from discord import app_commands
import aiohttp
import aiofiles
import difflib

from config import AUDIO_FOLDER, COMMANDS_FILE
from utils import load_json, save_json

class AudioCommands(commands.Cog):
    """Comandos para reprodução e gerenciamento de áudio."""
    
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = load_json(COMMANDS_FILE)
        
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
    
    @app_commands.command(name="tocar", description="Toca um áudio salvo.")
    async def tocar(self, ctx: discord.Interaction, comando: str):
        """Toca um áudio previamente salvo com sugestões de comandos similares."""
        if comando in self.custom_commands:
            filepath = self.custom_commands[comando]
            if not os.path.exists(filepath):
                await ctx.response.send_message(f"❌ O arquivo `{comando}` não foi encontrado.")
                return
            
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if not vc or not vc.is_connected():
                if ctx.user.voice:
                    vc = await ctx.user.voice.channel.connect()
                else:
                    await ctx.response.send_message("❌ Você precisa estar em um canal de voz!")
                    return
            
            vc.stop()
            vc.play(discord.FFmpegPCMAudio(filepath))
            await ctx.response.send_message(f"🎵 Tocando: `{comando}`")
        else:
            # Encontra comandos similares APENAS para /tocar
            similar_commands = self.find_similar_commands(comando, self.custom_commands)
            
            if similar_commands:
                # Formata as sugestões de forma mais segura
                suggestions = ", ".join([f"`{cmd}`" for cmd in similar_commands])
                await ctx.response.send_message(
                    f"❌ Comando não encontrado. Você quis dizer: {suggestions}?"
                )
            else:
                await ctx.response.send_message("❌ Comando não encontrado.")

    @app_commands.command(name="aprendido_wow", description="Lista os áudios de uma expansão específica do WoW.")
    async def aprendido_wow(self, ctx: discord.Interaction, expansao: str):
        """Lista os áudios de uma expansão específica do World of Warcraft."""
        logging.info(f"🔍 Comando aprendido_wow chamado com expansão: {expansao}")
        
        try:
            if not self.custom_commands:
                await ctx.response.send_message("❌ Nenhum áudio foi aprendido ainda.")
                return
            
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
                    f"Exemplo: `/aprendido_wow classic` ou `/aprendido_wow 0`"
                )
                return
            
            # Obtém o prefixo correto
            prefix = self.expansion_prefixes[exp_input]
            logging.info(f"📌 Prefixo encontrado: {prefix}")
            
            # Filtra comandos
            filtered_commands = [
                cmd for cmd in self.custom_commands.keys() 
                if cmd.startswith(prefix + "-")
            ]
            
            logging.info(f"🔢 Comandos encontrados: {len(filtered_commands)}")
            
            if not filtered_commands:
                await ctx.response.send_message(f"❌ Nenhum áudio encontrado para a expansão '{expansao}'.")
                return
            
            # Prepara a lista de comandos
            filtered_commands.sort()
            
            # Nome da expansão para exibição
            expansion_title = self.expansion_names.get(prefix, prefix.upper())
            
            # Divide os comandos em chunks para evitar limite de caracteres
            def create_message_chunks(commands, max_length=1900):
                chunks = []
                current_chunk = []
                current_length = 0
                
                for cmd in commands:
                    cmd_line = f"• {cmd}\n"
                    if current_length + len(cmd_line) > max_length:
                        chunks.append(''.join(current_chunk))
                        current_chunk = [cmd_line]
                        current_length = len(cmd_line)
                    else:
                        current_chunk.append(cmd_line)
                        current_length += len(cmd_line)
                
                if current_chunk:
                    chunks.append(''.join(current_chunk))
                
                return chunks
            
            message_chunks = create_message_chunks(filtered_commands)
            
            # Envia a primeira mensagem
            first_message = (
                f"🎵 Áudios de {expansion_title} "
                f"({len(filtered_commands)} no total, Parte 1/{len(message_chunks)}):\n"
                f"{message_chunks[0]}"
            )
            await ctx.response.send_message(first_message)
            
            # Envia mensagens adicionais, se houverem
            for i, chunk in enumerate(message_chunks[1:], 2):
                additional_message = (
                    f"🎵 Áudios de {expansion_title} "
                    f"(Continuação, Parte {i}/{len(message_chunks)}):\n"
                    f"{chunk}"
                )
                await ctx.followup.send(additional_message)
        
        except Exception as e:
            logging.error(f"❌ Erro no comando aprendido_wow: {e}")
            await ctx.response.send_message("❌ Ocorreu um erro ao processar o comando.")

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(AudioCommands(bot))
