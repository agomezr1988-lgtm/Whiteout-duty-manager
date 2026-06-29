import os

# Token (aunque lo lees en main, lo dejamos centralizado por orden)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Prefijo de comandos (si luego migras a slash commands, esto queda opcional)
COMMAND_PREFIX = "!"

# IDs opcionales (puedes usarlos para debug o servidores específicos)
GUILD_ID = os.getenv("GUILD_ID")

# Config de roles base (R4 / R5 management)
ROLE_R4_NAME = "R4"
ROLE_R5_NAME = "R5"

# Zona horaria (importante para eventos semanales)
TIMEZONE = "Europe/Madrid"

