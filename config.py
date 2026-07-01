import os

# ======================================================
# DISCORD
# ======================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# ======================================================
# GUILD
# ======================================================

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

# ======================================================
# CANALES
# ======================================================

# Canal donde se enviarán automáticamente los avisos
ANNOUNCEMENT_CHANNEL_ID = int(
    os.getenv("ANNOUNCEMENT_CHANNEL_ID", "0")
)

# Canal donde se publica y actualiza el tablón de calendario
CALENDAR_CHANNEL_ID = int(
    os.getenv("CALENDAR_CHANNEL_ID", "0")
)

# ======================================================
# ROLES
# ======================================================

ROLE_R4_NAME = os.getenv("ROLE_R4_NAME", "R4")
ROLE_R5_NAME = os.getenv("ROLE_R5_NAME", "R5")

# ======================================================
# HORARIO
# ======================================================

TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid")

# ======================================================
# RECORDATORIOS
# ======================================================

DEFAULT_REMINDERS = [60, 30, 15, 5]

# ======================================================
# DEBUG
# ======================================================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
