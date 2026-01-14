import discord
from discord import ui
import os
import logging
import asyncio
from discord.ext import commands
from discord import app_commands
import difflib
import math
from collections import deque
from typing import Optional, Dict, List

from config import (
    AUDIO_FOLDER, COMMANDS_FILE, WOW_OST_FOLDER, WOW_EXPANSION_DIRS,
    WOW_ENABLED, FAVORITES_FILE, STATS_FILE, RATE_LIMIT_COMMANDS, RATE_LIMIT_SECONDS
)
from utils import load_json, save_json, download_file, RateLimiter


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
            self.add_item(ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Página Anterior",
                custom_id="prev_page",
                disabled=(page == 0),
                row=0
            ))

            self.add_item(ui.Button(
                style=discord.ButtonStyle.secondary,
                label=f"Página {page+1}/{total_pages}",
                custom_id="page_indicator",
                disabled=True,
                row=0
            ))

            self.add_item(ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Próxima Página",
                custom_id="next_page",
                disabled=(page == total_pages - 1),
                row=0
            ))

        # Índice inicial para esta página
        start_idx = page * 15
        end_idx = min(start_idx + 15, len(audio_commands))

        # Adiciona botões para os áudios (5 por linha)
        for i, cmd in enumerate(audio_commands[start_idx:end_idx]):
            row = (i // 5) + 1

            display_name = cmd
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."

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

        if custom_id == "prev_page":
            if self.page > 0:
                new_page = self.page - 1
                new_view = AudioButtonsView(
                    self.cog,
                    self.audio_commands,
                    is_wow=self.is_wow,
                    wow_prefix=self.wow_prefix,
                    page=new_page,
                    total_pages=self.total_pages
                )
                await interaction.response.edit_message(view=new_view)
                return True

        elif custom_id == "next_page":
            if self.page < self.total_pages - 1:
                new_page = self.page + 1
                new_view = AudioButtonsView(
                    self.cog,
                    self.audio_commands,
                    is_wow=self.is_wow,
                    wow_prefix=self.wow_prefix,
                    page=new_page,
                    total_pages=self.total_pages
                )
                await interaction.response.edit_message(view=new_view)
                return True

        elif custom_id.startswith("play_"):
            cmd_name = custom_id[5:]

            if self.is_wow and self.wow_prefix:
                full_cmd = f"{self.wow_prefix}-{cmd_name}"
            else:
                full_cmd = cmd_name

            await interaction.response.defer(ephemeral=True)
            await self.cog.play_audio(interaction, full_cmd)

        return True


class AudioControlView(ui.View):
    """View com controles de reprodução (pausar, continuar, parar, volume)."""

    def __init__(self, cog, timeout=300):
        super().__init__(timeout=timeout)
        self.cog = cog

    @ui.button(label="Pausar", style=discord.ButtonStyle.secondary, custom_id="pause")
    async def pause_button(self, interaction: discord.Interaction, button: ui.Button):
        vc = discord.utils.get(self.cog.bot.voice_clients, guild=interaction.guild)
        if vc and vc.is_playing():
            vc.pause()
            button.label = "Continuar"
            button.custom_id = "resume"
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("Nenhum áudio tocando.", ephemeral=True)

    @ui.button(label="Parar", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_button(self, interaction: discord.Interaction, button: ui.Button):
        vc = discord.utils.get(self.cog.bot.voice_clients, guild=interaction.guild)
        if vc:
            vc.stop()
            # Limpa a fila
            guild_id = interaction.guild.id
            if guild_id in self.cog.audio_queues:
                self.cog.audio_queues[guild_id].clear()
            await interaction.response.send_message("Reprodução parada e fila limpa.", ephemeral=True)
        else:
            await interaction.response.send_message("Não estou conectado a um canal de voz.", ephemeral=True)

    @ui.button(label="Pular", style=discord.ButtonStyle.primary, custom_id="skip")
    async def skip_button(self, interaction: discord.Interaction, button: ui.Button):
        vc = discord.utils.get(self.cog.bot.voice_clients, guild=interaction.guild)
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()  # Isso vai triggar o after callback que toca o próximo
            await interaction.response.send_message("Pulando para o próximo áudio...", ephemeral=True)
        else:
            await interaction.response.send_message("Nenhum áudio tocando.", ephemeral=True)

    @ui.button(label="Loop: OFF", style=discord.ButtonStyle.secondary, custom_id="loop")
    async def loop_button(self, interaction: discord.Interaction, button: ui.Button):
        guild_id = interaction.guild.id
        self.cog.loop_enabled[guild_id] = not self.cog.loop_enabled.get(guild_id, False)

        if self.cog.loop_enabled[guild_id]:
            button.label = "Loop: ON"
            button.style = discord.ButtonStyle.success
        else:
            button.label = "Loop: OFF"
            button.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(view=self)


class AudioCommands(commands.Cog):
    """Comandos para reprodução e gerenciamento de áudio."""

    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = load_json(COMMANDS_FILE)
        self.favorites: Dict[int, List[str]] = load_json(FAVORITES_FILE) or {}
        self.stats: Dict[str, int] = load_json(STATS_FILE) or {}

        # Filas de áudio por servidor
        self.audio_queues: Dict[int, deque] = {}
        # Áudio atual por servidor
        self.current_audio: Dict[int, str] = {}
        # Loop habilitado por servidor
        self.loop_enabled: Dict[int, bool] = {}
        # Volume por servidor (0.0 a 2.0)
        self.volume: Dict[int, float] = {}

        # Rate limiter
        self.rate_limiter = RateLimiter(RATE_LIMIT_COMMANDS, RATE_LIMIT_SECONDS)

        # WoW mode
        self.wow_mode = WOW_ENABLED
        if self.wow_mode:
            logging.info(f"Modo WoW ativado! Pasta: {WOW_OST_FOLDER}")
            self.wow_audio_cache = {}
        else:
            logging.warning("Modo WoW desativado - pasta não encontrada")

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

    def _increment_stats(self, comando: str):
        """Incrementa estatísticas de uso de um comando."""
        self.stats[comando] = self.stats.get(comando, 0) + 1
        save_json(STATS_FILE, self.stats)

    def _get_queue(self, guild_id: int) -> deque:
        """Obtém ou cria a fila de áudio para um servidor."""
        if guild_id not in self.audio_queues:
            self.audio_queues[guild_id] = deque()
        return self.audio_queues[guild_id]

    def _get_volume(self, guild_id: int) -> float:
        """Obtém o volume para um servidor (padrão 1.0)."""
        return self.volume.get(guild_id, 1.0)

    async def _play_next(self, guild: discord.Guild, error=None):
        """Toca o próximo áudio da fila."""
        if error:
            logging.error(f"Erro na reprodução: {error}")

        guild_id = guild.id
        vc = discord.utils.get(self.bot.voice_clients, guild=guild)

        if not vc or not vc.is_connected():
            return

        # Se loop está habilitado, readiciona o áudio atual à fila
        if self.loop_enabled.get(guild_id, False) and guild_id in self.current_audio:
            self._get_queue(guild_id).append(self.current_audio[guild_id])

        queue = self._get_queue(guild_id)
        if not queue:
            self.current_audio.pop(guild_id, None)
            return

        next_audio = queue.popleft()
        self.current_audio[guild_id] = next_audio

        # Resolve o caminho do arquivo
        filepath = self._resolve_audio_path(next_audio)
        if not filepath or not os.path.exists(filepath):
            logging.warning(f"Arquivo não encontrado: {next_audio}")
            await self._play_next(guild)
            return

        # Cria source com volume ajustável
        source = discord.FFmpegPCMAudio(filepath)
        source = discord.PCMVolumeTransformer(source, volume=self._get_volume(guild_id))

        def after_callback(err):
            asyncio.run_coroutine_threadsafe(self._play_next(guild, err), self.bot.loop)

        vc.play(source, after=after_callback)

    def _resolve_audio_path(self, comando: str) -> Optional[str]:
        """Resolve o caminho do arquivo de áudio."""
        # Primeiro verifica nos comandos personalizados
        if comando in self.custom_commands:
            return self.custom_commands[comando]

        # Depois verifica no WoW
        if self.wow_mode:
            return self.find_wow_audio(comando)

        return None

    async def play_audio(self, interaction, comando: str, add_to_queue: bool = False):
        """Método universal para tocar áudio."""
        logging.info(f"Tocando áudio: {comando}")

        # Rate limiting
        if self.rate_limiter.is_rate_limited(interaction.user.id):
            remaining = self.rate_limiter.get_remaining_time(interaction.user.id)
            await interaction.followup.send(
                f"Aguarde {remaining:.1f}s antes de usar outro comando.",
                ephemeral=True
            )
            return

        # Resolve o caminho do arquivo
        filepath = self._resolve_audio_path(comando)

        if not filepath:
            # Tenta busca fuzzy
            suggestions = self.find_similar_commands(comando, self.custom_commands)
            if suggestions:
                suggestion_text = ", ".join([f"`{s}`" for s in suggestions[:5]])
                await interaction.followup.send(
                    f"Comando `{comando}` não encontrado. Você quis dizer: {suggestion_text}?",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(f"Comando `{comando}` não encontrado.", ephemeral=True)
            return

        if not os.path.exists(filepath):
            await interaction.followup.send(f"O arquivo `{comando}` não foi encontrado.", ephemeral=True)
            return

        # Incrementa estatísticas
        self._increment_stats(comando)

        # Conecta ao canal de voz
        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if not vc or not vc.is_connected():
                if interaction.user.voice:
                    vc = await interaction.user.voice.channel.connect()
                else:
                    await interaction.followup.send("Você precisa estar em um canal de voz!", ephemeral=True)
                    return

            guild_id = interaction.guild.id

            # Se add_to_queue ou já está tocando, adiciona à fila
            if add_to_queue or vc.is_playing():
                self._get_queue(guild_id).append(comando)
                position = len(self._get_queue(guild_id))
                await interaction.followup.send(
                    f"Adicionado `{comando}` à fila (posição {position}).",
                    ephemeral=True
                )
                return

            # Toca diretamente
            self.current_audio[guild_id] = comando
            source = discord.FFmpegPCMAudio(filepath)
            source = discord.PCMVolumeTransformer(source, volume=self._get_volume(guild_id))

            def after_callback(err):
                asyncio.run_coroutine_threadsafe(self._play_next(interaction.guild, err), self.bot.loop)

            vc.play(source, after=after_callback)

            # Cria view de controles
            view = AudioControlView(self)
            await interaction.followup.send(f"Tocando: `{comando}`", view=view, ephemeral=True)

        except discord.errors.ClientException as e:
            logging.error(f"Erro de conexão: {e}")
            await interaction.followup.send(f"Erro de conexão: {str(e)}", ephemeral=True)
        except Exception as e:
            logging.error(f"Erro ao tocar áudio: {type(e).__name__}: {e}")
            await interaction.followup.send(f"Erro ao tocar áudio: {str(e)}", ephemeral=True)

    def find_similar_commands(self, input_command: str, commands_dict: dict, threshold: float = 0.5, max_suggestions: int = 5) -> List[str]:
        """Encontra comandos similares usando fuzzy matching."""
        if isinstance(commands_dict, dict):
            commands_list = list(commands_dict.keys())
        else:
            commands_list = list(commands_dict)

        suggestions = []
        for cmd in commands_list:
            ratio = difflib.SequenceMatcher(None, input_command.lower(), cmd.lower()).ratio()
            if ratio >= threshold:
                suggestions.append((cmd, ratio))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [cmd for cmd, _ in suggestions[:max_suggestions]]

    def find_wow_audio(self, command: str) -> Optional[str]:
        """Encontra um arquivo de áudio do WoW."""
        if not self.wow_mode:
            return None

        if command in self.wow_audio_cache:
            return self.wow_audio_cache[command]

        parts = command.split('-', 1)
        if len(parts) != 2:
            return None

        prefix, name = parts

        if prefix not in self.expansion_prefixes:
            return None

        prefix = self.expansion_prefixes[prefix]

        if prefix not in WOW_EXPANSION_DIRS:
            return None

        for exp_dir in WOW_EXPANSION_DIRS[prefix]:
            dir_path = os.path.join(WOW_OST_FOLDER, exp_dir)

            if not os.path.exists(dir_path):
                continue

            try:
                for file in os.listdir(dir_path):
                    file_name, file_ext = os.path.splitext(file)
                    if file_ext.lower() != '.mp3':
                        continue

                    # Correspondência direta
                    if name.lower() in file_name.lower():
                        filepath = os.path.join(dir_path, file)
                        self.wow_audio_cache[command] = filepath
                        return filepath

                    # Remove números do início
                    if ". " in file_name:
                        clean_name = file_name.split(". ", 1)[1].lower()
                        if name.lower() in clean_name:
                            filepath = os.path.join(dir_path, file)
                            self.wow_audio_cache[command] = filepath
                            return filepath

                    # Substitui hífens por espaços
                    name_with_spaces = name.replace("-", " ").lower()
                    if name_with_spaces in file_name.lower():
                        filepath = os.path.join(dir_path, file)
                        self.wow_audio_cache[command] = filepath
                        return filepath

            except OSError as e:
                logging.error(f"Erro ao buscar em {dir_path}: {e}")

        return None

    # === COMANDOS DE ÁUDIO ===

    @app_commands.command(name="tocar", description="Toca um áudio salvo.")
    @app_commands.describe(comando="Nome do áudio a ser tocado")
    async def tocar(self, ctx: discord.Interaction, comando: str):
        """Toca um áudio previamente salvo."""
        await ctx.response.defer()
        await self.play_audio(ctx, comando)

    @app_commands.command(name="fila", description="Adiciona um áudio à fila de reprodução.")
    @app_commands.describe(comando="Nome do áudio a adicionar na fila")
    async def adicionar_fila(self, ctx: discord.Interaction, comando: str):
        """Adiciona um áudio à fila de reprodução."""
        await ctx.response.defer()
        await self.play_audio(ctx, comando, add_to_queue=True)

    @app_commands.command(name="ver_fila", description="Mostra a fila de reprodução atual.")
    async def ver_fila(self, ctx: discord.Interaction):
        """Mostra a fila de reprodução atual."""
        guild_id = ctx.guild.id
        queue = self._get_queue(guild_id)

        if not queue and guild_id not in self.current_audio:
            await ctx.response.send_message("A fila está vazia.", ephemeral=True)
            return

        lines = []
        if guild_id in self.current_audio:
            lines.append(f"**Tocando agora:** `{self.current_audio[guild_id]}`")

        if queue:
            lines.append("\n**Próximos na fila:**")
            for i, audio in enumerate(list(queue)[:10], 1):
                lines.append(f"{i}. `{audio}`")
            if len(queue) > 10:
                lines.append(f"... e mais {len(queue) - 10} áudios")

        await ctx.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="limpar_fila", description="Limpa a fila de reprodução.")
    async def limpar_fila(self, ctx: discord.Interaction):
        """Limpa a fila de reprodução."""
        guild_id = ctx.guild.id
        if guild_id in self.audio_queues:
            self.audio_queues[guild_id].clear()
        await ctx.response.send_message("Fila limpa!", ephemeral=True)

    @app_commands.command(name="pausar", description="Pausa a reprodução atual.")
    async def pausar(self, ctx: discord.Interaction):
        """Pausa a reprodução atual."""
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_playing():
            vc.pause()
            await ctx.response.send_message("Reprodução pausada.", ephemeral=True)
        else:
            await ctx.response.send_message("Nenhum áudio tocando.", ephemeral=True)

    @app_commands.command(name="continuar", description="Continua a reprodução pausada.")
    async def continuar(self, ctx: discord.Interaction):
        """Continua a reprodução pausada."""
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_paused():
            vc.resume()
            await ctx.response.send_message("Reprodução retomada.", ephemeral=True)
        else:
            await ctx.response.send_message("Nenhum áudio pausado.", ephemeral=True)

    @app_commands.command(name="pular", description="Pula para o próximo áudio da fila.")
    async def pular(self, ctx: discord.Interaction):
        """Pula para o próximo áudio da fila."""
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await ctx.response.send_message("Pulando para o próximo...", ephemeral=True)
        else:
            await ctx.response.send_message("Nenhum áudio tocando.", ephemeral=True)

    @app_commands.command(name="volume", description="Ajusta o volume da reprodução (0-200%).")
    @app_commands.describe(nivel="Nível do volume (0-200)")
    async def volume_cmd(self, ctx: discord.Interaction, nivel: int):
        """Ajusta o volume da reprodução."""
        if nivel < 0 or nivel > 200:
            await ctx.response.send_message("O volume deve ser entre 0 e 200.", ephemeral=True)
            return

        guild_id = ctx.guild.id
        self.volume[guild_id] = nivel / 100.0

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc and vc.source and hasattr(vc.source, 'volume'):
            vc.source.volume = self.volume[guild_id]

        await ctx.response.send_message(f"Volume ajustado para {nivel}%.", ephemeral=True)

    @app_commands.command(name="loop", description="Ativa/desativa o loop do áudio atual.")
    async def loop_cmd(self, ctx: discord.Interaction):
        """Ativa ou desativa o loop do áudio atual."""
        guild_id = ctx.guild.id
        self.loop_enabled[guild_id] = not self.loop_enabled.get(guild_id, False)

        status = "ativado" if self.loop_enabled[guild_id] else "desativado"
        await ctx.response.send_message(f"Loop {status}.", ephemeral=True)

    # === COMANDOS DE FAVORITOS ===

    @app_commands.command(name="favoritar", description="Adiciona um áudio aos seus favoritos.")
    @app_commands.describe(comando="Nome do áudio para favoritar")
    async def favoritar(self, ctx: discord.Interaction, comando: str):
        """Adiciona um áudio aos favoritos do usuário."""
        user_id = str(ctx.user.id)
        comando = comando.lower().strip()

        # Verifica se o áudio existe
        if comando not in self.custom_commands:
            await ctx.response.send_message(f"O áudio `{comando}` não existe.", ephemeral=True)
            return

        if user_id not in self.favorites:
            self.favorites[user_id] = []

        if comando in self.favorites[user_id]:
            await ctx.response.send_message(f"`{comando}` já está nos seus favoritos.", ephemeral=True)
            return

        self.favorites[user_id].append(comando)
        save_json(FAVORITES_FILE, self.favorites)
        await ctx.response.send_message(f"`{comando}` adicionado aos favoritos!", ephemeral=True)

    @app_commands.command(name="desfavoritar", description="Remove um áudio dos seus favoritos.")
    @app_commands.describe(comando="Nome do áudio para remover dos favoritos")
    async def desfavoritar(self, ctx: discord.Interaction, comando: str):
        """Remove um áudio dos favoritos do usuário."""
        user_id = str(ctx.user.id)
        comando = comando.lower().strip()

        if user_id not in self.favorites or comando not in self.favorites[user_id]:
            await ctx.response.send_message(f"`{comando}` não está nos seus favoritos.", ephemeral=True)
            return

        self.favorites[user_id].remove(comando)
        save_json(FAVORITES_FILE, self.favorites)
        await ctx.response.send_message(f"`{comando}` removido dos favoritos.", ephemeral=True)

    @app_commands.command(name="favoritos", description="Mostra seus áudios favoritos.")
    async def ver_favoritos(self, ctx: discord.Interaction):
        """Mostra os favoritos do usuário."""
        user_id = str(ctx.user.id)

        if user_id not in self.favorites or not self.favorites[user_id]:
            await ctx.response.send_message("Você não tem favoritos ainda.", ephemeral=True)
            return

        fav_list = self.favorites[user_id]
        page_size = 15
        total_pages = math.ceil(len(fav_list) / page_size)

        view = AudioButtonsView(self, fav_list, page=0, total_pages=total_pages)
        await ctx.response.send_message(
            f"Seus favoritos ({len(fav_list)} áudios):",
            view=view,
            ephemeral=True
        )

    # === COMANDOS DE ESTATÍSTICAS ===

    @app_commands.command(name="ranking", description="Mostra os áudios mais tocados.")
    @app_commands.describe(quantidade="Quantidade de áudios no ranking (padrão: 10)")
    async def ranking(self, ctx: discord.Interaction, quantidade: int = 10):
        """Mostra o ranking dos áudios mais tocados."""
        if not self.stats:
            await ctx.response.send_message("Nenhuma estatística disponível ainda.", ephemeral=True)
            return

        quantidade = min(max(1, quantidade), 25)
        sorted_stats = sorted(self.stats.items(), key=lambda x: x[1], reverse=True)[:quantidade]

        lines = ["**Ranking dos áudios mais tocados:**\n"]
        medals = ["", "", ""]

        for i, (audio, count) in enumerate(sorted_stats, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            lines.append(f"{medal} `{audio}` - {count} reproduções")

        await ctx.response.send_message("\n".join(lines), ephemeral=True)

    # === COMANDOS DE GERENCIAMENTO ===

    @app_commands.command(name="aprendido", description="Lista todos os áudios aprendidos.")
    async def aprendido(self, ctx: discord.Interaction):
        """Lista todos os áudios aprendidos com botões interativos."""
        try:
            if not self.custom_commands:
                await ctx.response.send_message("Nenhum áudio foi aprendido ainda.")
                return

            command_list = sorted(list(self.custom_commands.keys()))
            page_size = 15
            total_pages = math.ceil(len(command_list) / page_size)

            view = AudioButtonsView(self, command_list, page=0, total_pages=total_pages)

            await ctx.response.send_message(
                f"Áudios disponíveis ({len(command_list)} no total)\nClique em um botão para tocar:",
                view=view
            )

            if self.wow_mode:
                await ctx.followup.send(
                    "Para ver os áudios de World of Warcraft, use `/wow [expansão]`.\n"
                    "Exemplo: `/wow classic` ou `/wow wotlk`"
                )

        except Exception as e:
            logging.error(f"Erro no comando aprendido: {type(e).__name__}: {e}")
            await ctx.response.send_message("Ocorreu um erro ao processar o comando.")

    @app_commands.command(name="buscar", description="Busca áudios pelo nome.")
    @app_commands.describe(termo="Termo de busca")
    async def buscar(self, ctx: discord.Interaction, termo: str):
        """Busca áudios que contenham o termo especificado."""
        termo = termo.lower().strip()
        resultados = [cmd for cmd in self.custom_commands.keys() if termo in cmd.lower()]

        if not resultados:
            # Tenta busca fuzzy
            suggestions = self.find_similar_commands(termo, self.custom_commands, threshold=0.4)
            if suggestions:
                await ctx.response.send_message(
                    f"Nenhum resultado para `{termo}`. Sugestões: {', '.join([f'`{s}`' for s in suggestions])}",
                    ephemeral=True
                )
            else:
                await ctx.response.send_message(f"Nenhum resultado para `{termo}`.", ephemeral=True)
            return

        if len(resultados) <= 15:
            view = AudioButtonsView(self, resultados, page=0, total_pages=1)
            await ctx.response.send_message(
                f"Resultados para `{termo}` ({len(resultados)}):",
                view=view,
                ephemeral=True
            )
        else:
            total_pages = math.ceil(len(resultados) / 15)
            view = AudioButtonsView(self, resultados, page=0, total_pages=total_pages)
            await ctx.response.send_message(
                f"Resultados para `{termo}` ({len(resultados)}):",
                view=view,
                ephemeral=True
            )

    @app_commands.command(name="wow", description="Lista os áudios de uma expansão do WoW.")
    @app_commands.describe(expansao="Nome ou número da expansão (ex: classic, wotlk, 0, 2)")
    async def aprendido_wow(self, ctx: discord.Interaction, expansao: str):
        """Lista os áudios de uma expansão específica do World of Warcraft."""
        if not self.wow_mode:
            await ctx.response.send_message(
                "O modo WoW está desativado porque a pasta não foi encontrada.\n"
                f"Configure WOW_OST_FOLDER no .env ou crie uma pasta 'wow-music' no diretório do bot."
            )
            return

        exp_input = expansao.lower().strip()

        if exp_input not in self.expansion_prefixes:
            available = "\n".join([
                f"  {num}: {self.expansion_names[prefix]}"
                for num, prefix in [
                    ("0", "classic"), ("1", "tbc"), ("2", "wotlk"),
                    ("3", "cata"), ("4", "mop"), ("5", "wod"),
                    ("6", "legion"), ("7", "bfa"), ("8", "sl"),
                    ("9", "df"), ("10", "tww"), ("11", "undermine")
                ]
            ])
            await ctx.response.send_message(
                f"Expansão '{expansao}' não reconhecida.\n\nExpansões disponíveis:\n{available}\n\n"
                f"Exemplo: `/wow classic` ou `/wow 0`"
            )
            return

        prefix = self.expansion_prefixes[exp_input]

        if prefix not in WOW_EXPANSION_DIRS:
            await ctx.response.send_message(f"Diretórios não configurados para '{expansao}'.")
            return

        existing_dirs = []
        for exp_dir in WOW_EXPANSION_DIRS[prefix]:
            dir_path = os.path.join(WOW_OST_FOLDER, exp_dir)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                existing_dirs.append(dir_path)

        if not existing_dirs:
            await ctx.response.send_message(f"Nenhum diretório encontrado para '{expansao}'.")
            return

        all_files = []
        for dir_path in existing_dirs:
            try:
                files = [f for f in os.listdir(dir_path) if f.lower().endswith('.mp3')]
                for file in files:
                    file_name, _ = os.path.splitext(file)
                    if ". " in file_name:
                        file_name = file_name.split(". ", 1)[1]
                    command_name = file_name.lower().replace(" ", "-")
                    all_files.append(command_name)
            except OSError as e:
                logging.error(f"Erro ao listar {dir_path}: {e}")

        if not all_files:
            await ctx.response.send_message(f"Nenhum áudio encontrado para '{expansao}'.")
            return

        all_files.sort()
        expansion_title = self.expansion_names.get(prefix, prefix.upper())

        page_size = 15
        total_pages = math.ceil(len(all_files) / page_size)

        view = AudioButtonsView(
            self, all_files, is_wow=True, wow_prefix=prefix,
            page=0, total_pages=total_pages
        )

        await ctx.response.send_message(
            f"Áudios de {expansion_title} ({len(all_files)} no total)\nClique em um botão para tocar:",
            view=view
        )

    @app_commands.command(name="aprender", description="Adiciona um novo áudio ao bot.")
    @app_commands.describe(
        comando="Nome do comando (até 32 caracteres)",
        url="URL do arquivo de áudio"
    )
    async def aprender(self, ctx: discord.Interaction, comando: str, url: str):
        """Adiciona um novo áudio ao bot a partir de uma URL."""
        comando = comando.lower().strip()

        if comando in self.custom_commands:
            await ctx.response.send_message(f"O comando `{comando}` já existe!")
            return

        if not comando or len(comando) > 32:
            await ctx.response.send_message("O nome do comando deve ter entre 1 e 32 caracteres.")
            return

        await ctx.response.defer(thinking=True)

        try:
            os.makedirs(AUDIO_FOLDER, exist_ok=True)
            filename = f"{comando}.mp3"
            filepath = os.path.join(AUDIO_FOLDER, filename)

            success = await download_file(url, filepath)

            if not success:
                await ctx.followup.send("Erro ao baixar o arquivo. Verifique se a URL é válida.")
                return

            self.custom_commands[comando] = filepath
            save_json(COMMANDS_FILE, self.custom_commands)

            await ctx.followup.send(f"Comando `{comando}` adicionado! Use `/tocar {comando}` para reproduzir.")

        except OSError as e:
            logging.error(f"Erro de I/O ao aprender comando: {e}")
            await ctx.followup.send(f"Erro ao salvar arquivo: {str(e)}")
        except Exception as e:
            logging.error(f"Erro ao aprender comando: {type(e).__name__}: {e}")
            await ctx.followup.send(f"Ocorreu um erro: {str(e)}")

    @app_commands.command(name="esquecer", description="Remove um áudio do bot.")
    @app_commands.describe(comando="Nome do comando a ser removido")
    async def esquecer(self, ctx: discord.Interaction, comando: str):
        """Remove um áudio do bot."""
        comando = comando.lower().strip()

        if comando not in self.custom_commands:
            await ctx.response.send_message(f"O comando `{comando}` não existe!")
            return

        try:
            filepath = self.custom_commands[comando]
            del self.custom_commands[comando]
            save_json(COMMANDS_FILE, self.custom_commands)

            # Remove dos favoritos de todos os usuários
            for user_id in self.favorites:
                if comando in self.favorites[user_id]:
                    self.favorites[user_id].remove(comando)
            save_json(FAVORITES_FILE, self.favorites)

            # Remove das estatísticas
            if comando in self.stats:
                del self.stats[comando]
                save_json(STATS_FILE, self.stats)

            # Tenta excluir o arquivo
            if os.path.exists(filepath) and AUDIO_FOLDER in filepath:
                try:
                    os.remove(filepath)
                    await ctx.response.send_message(f"Comando `{comando}` e arquivo removidos!")
                except OSError:
                    await ctx.response.send_message(f"Comando `{comando}` removido (arquivo não excluído).")
            else:
                await ctx.response.send_message(f"Comando `{comando}` removido do bot.")

        except Exception as e:
            logging.error(f"Erro ao esquecer comando: {type(e).__name__}: {e}")
            await ctx.response.send_message(f"Ocorreu um erro: {str(e)}")

    @app_commands.command(name="sair", description="Faz o bot sair do canal de voz.")
    async def sair(self, ctx: discord.Interaction):
        """Faz o bot sair do canal de voz."""
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        if vc and vc.is_connected():
            # Limpa a fila
            guild_id = ctx.guild.id
            if guild_id in self.audio_queues:
                self.audio_queues[guild_id].clear()
            self.current_audio.pop(guild_id, None)

            await vc.disconnect()
            await ctx.response.send_message("Saí do canal de voz!")
        else:
            await ctx.response.send_message("Não estou conectado a nenhum canal de voz!")


async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(AudioCommands(bot))
