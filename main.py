import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
from utils.event_manager import EventManager

# ======================================================
# CARGAR .ENV
# ======================================================

load_dotenv()

# ======================================================
# LOGGING
# ======================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)

logger = logging.getLogger("WhiteoutBot")

# ======================================================
# INTENTS
# ======================================================

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True


# ======================================================
# BOT
# ======================================================

class WhiteoutBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )

        # Managers
        self.event_manager = EventManager()

    async def setup_hook(self):

        cogs = [
            "cogs.admin",
            "cogs.events",
            "cogs.scheduler",
        ]

        for cog in cogs:

            try:
                await self.load_extension(cog)
                logger.info(f"Cog cargado: {cog}")

            except Exception:
                logger.exception(f"No se pudo cargar {cog}")

        # Sincroniza Slash Commands (para el futuro)
        try:
            synced = await self.tree.sync()
            logger.info(f"Slash Commands sincronizados: {len(synced)}")
        except Exception:
            logger.exception("Error sincronizando Slash Commands")

    async def on_ready(self):

        logger.info("--------------------------------------")
        logger.info(f"Bot conectado como {self.user}")
        logger.info(f"ID: {self.user.id}")
        logger.info("--------------------------------------")

        logger.info(
            f"Eventos cargados: {len(self.event_manager.get_all_events())}"
        )

        logger.info("Whiteout Duty Manager iniciado correctamente.")


# ======================================================
# MAIN
# ======================================================

async def main():

    bot = WhiteoutBot()

    async with bot:
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
