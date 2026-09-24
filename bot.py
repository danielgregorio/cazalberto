"""Atalho para iniciar o bot com `python bot.py`.

O código fica no pacote `cazalberto/`; o jeito recomendado é `python -m cazalberto`.
"""

from cazalberto.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
