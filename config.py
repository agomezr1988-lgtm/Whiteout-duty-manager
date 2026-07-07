import os

# ======================================================
# DISCORD
# ======================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# ======================================================
# GUILD (kept for backward compatibility; not required anymore,
# since the bot now syncs commands in every server it's in)
# ======================================================

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

# ======================================================
# CHANNELS (default values; can be overridden per server via
# /management)
# ======================================================

# Channel where announcements are sent automatically
ANNOUNCEMENT_CHANNEL_ID = int(
    os.getenv("ANNOUNCEMENT_CHANNEL_ID", "0")
)

# Channel where the calendar board is posted and kept updated
CALENDAR_CHANNEL_ID = int(
    os.getenv("CALENDAR_CHANNEL_ID", "0")
)

# ======================================================
# ROLES (default values; can be overridden per server via
# /management)
# ======================================================

ROLE_R4_NAME = os.getenv("ROLE_R4_NAME", "R4")
ROLE_R5_NAME = os.getenv("ROLE_R5_NAME", "R5")

# ======================================================
# TIMEZONE
# ======================================================

TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid")

# ======================================================
# REMINDERS
# ======================================================

DEFAULT_REMINDERS = [60, 30, 15, 5]

# ======================================================
# DEBUG
# ======================================================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
