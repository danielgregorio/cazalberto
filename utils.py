import json
import os
import logging
import aiohttp
import aiofiles
from typing import Dict, Any, Union, List
from collections import defaultdict
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def normalize_path(path: str) -> str:
    """
    Normaliza um path para funcionar em qualquer sistema operacional.
    Converte backslashes para forward slashes e usa os.path.normpath.
    """
    if not path:
        return path
    # Substitui backslashes por forward slashes
    normalized = path.replace("\\", "/")
    # Usa normpath para limpar redundâncias
    return os.path.normpath(normalized)


def normalize_commands_paths(commands: Dict[str, str]) -> Dict[str, str]:
    """
    Normaliza todos os paths em um dicionário de comandos.
    """
    return {cmd: normalize_path(path) for cmd, path in commands.items()}


def load_json(file: str) -> Dict[str, Any]:
    """Load JSON data from a file with error handling."""
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Se for o arquivo de comandos, normaliza os paths
            if "commands" in file.lower() and isinstance(data, dict):
                # Verifica se algum path precisa ser normalizado
                needs_update = False
                for path in data.values():
                    if isinstance(path, str) and "\\" in path:
                        needs_update = True
                        break

                if needs_update:
                    data = normalize_commands_paths(data)
                    save_json(file, data)
                    logging.info(f"Paths normalizados automaticamente em {file}")

            return data
        except (json.JSONDecodeError, ValueError) as e:
            logging.warning(f"Erro: Arquivo {file} corrompido ({e}), resetando arquivo.")
            return {}
    return {}


def save_json(file: str, data: Dict[str, Any]) -> None:
    """Save JSON data to a file."""
    # Garante que o diretório existe (se houver diretório no path)
    dir_path = os.path.dirname(file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def ensure_folder(folder: str) -> None:
    """Ensure a directory exists."""
    if not os.path.exists(folder):
        os.makedirs(folder)


async def download_file(url: str, filepath: str) -> bool:
    """Download a file from a URL to the given filepath."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(filepath, "wb") as f:
                        await f.write(await response.read())
                    logging.info(f"Arquivo baixado com sucesso: {filepath}")
                    return True
                else:
                    logging.error(f"Erro ao baixar arquivo: Status {response.status}")
    except aiohttp.ClientError as e:
        logging.error(f"Erro de conexão ao baixar arquivo: {e}")
    except OSError as e:
        logging.error(f"Erro de I/O ao salvar arquivo: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado ao baixar arquivo: {type(e).__name__}: {e}")
    return False


def sanitize_name(name: str) -> str:
    """Sanitize a name for filesystem use, removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


def format_duration(seconds: int) -> str:
    """Format seconds into a human-readable duration string."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def truncate_text(text: str, max_length: int = 1900) -> Union[str, List[str]]:
    """
    Truncate text to fit within Discord's message limit.
    Returns either a single string or a list of chunks.
    """
    if len(text) <= max_length:
        return text

    # Split into multiple chunks
    chunks = []
    current_chunk = ""

    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:  # +1 for newline
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class RateLimiter:
    """
    Rate limiter simples para controlar uso de comandos por usuário.
    """
    def __init__(self, max_commands: int = 5, period_seconds: int = 10):
        self.max_commands = max_commands
        self.period_seconds = period_seconds
        self.user_commands: Dict[int, List[float]] = defaultdict(list)

    def is_rate_limited(self, user_id: int) -> bool:
        """
        Verifica se o usuário está limitado.
        Retorna True se limitado, False se pode executar.
        """
        current_time = time.time()

        # Limpa comandos antigos
        self.user_commands[user_id] = [
            cmd_time for cmd_time in self.user_commands[user_id]
            if current_time - cmd_time < self.period_seconds
        ]

        # Verifica se ultrapassou o limite
        if len(self.user_commands[user_id]) >= self.max_commands:
            return True

        # Registra o comando
        self.user_commands[user_id].append(current_time)
        return False

    def get_remaining_time(self, user_id: int) -> float:
        """
        Retorna quantos segundos faltam para o usuário poder usar comandos novamente.
        """
        if not self.user_commands[user_id]:
            return 0

        oldest_command = min(self.user_commands[user_id])
        remaining = self.period_seconds - (time.time() - oldest_command)
        return max(0, remaining)
