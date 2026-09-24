"""Exceções com mensagem pronta para mostrar ao usuário no Discord."""


class UserError(Exception):
    """Erro esperado (entrada inválida, áudio inexistente...). A mensagem é
    enviada ao usuário como está, sem stack trace no log."""
