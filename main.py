import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
from utils.event_manager import EventManager
from utils.availability_manager import AvailabilityManager

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
    """
    Bot multi-servidor: cada servidor (guild) tiene sus propios
    eventos, disponibilidad, ciclo de SvS y configuración (nombres
    de roles R4/R5, canales). Los datos se guardan por separado en
    data/guilds/<guild_id>/.
    """

    def __init__(self):

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )

        # Un EventManager y un AvailabilityManager por servidor,
        # creados la primera vez que se necesitan (bajo demanda).
        self._event_managers = {}
        self._availability_managers = {}

    # --------------------------------------------------
    # Acceso a los gestores por servidor
    # --------------------------------------------------
    def get_event_manager(self, guild_id: int) -> EventManager:
        if guild_id not in self._event_managers:
            manager = EventManager(guild_id)

            # Auto-carga de eventos de referencia para este servidor
            from utils.seed_loader import load_seed_events
            creados, _ = load_seed_events(manager)
            if creados:
                logger.info(f"[{guild_id}] Eventos cargados automáticamente: {len(creados)}")

            self._event_managers[guild_id] = manager

        return self._event_managers[guild_id]

    def get_availability_manager(self, guild_id: int) -> AvailabilityManager:
        if guild_id not in self._availability_managers:
            self._availability_managers[guild_id] = AvailabilityManager(guild_id)

        return self._availability_managers[guild_id]

    async def setup_hook(self):

        cogs = [
            "cogs.admin",
            "cogs.events",
            "cogs.scheduler",
            "cogs.availability",
            "cogs.dashboard",
            "cogs.cycle",
        ]

        for cog in cogs:

            try:
                await self.load_extension(cog)
                logger.info(f"Cog cargado: {cog}")

            except Exception:
                logger.exception(f"No se pudo cargar {cog}")

    async def on_ready(self):

        logger.info("--------------------------------------")
        logger.info(f"Bot conectado como {self.user}")
        logger.info(f"ID: {self.user.id}")
        logger.info(f"Servidores: {len(self.guilds)}")
        logger.info("--------------------------------------")

        # Prepara los datos y sincroniza los Slash Commands en CADA
        # servidor donde está el bot, para que aparezcan al instante
        # (sincronización global puede tardar hasta 1 hora).
        for guild in self.guilds:

            manager = self.get_event_manager(guild.id)
            logger.info(f"[{guild.name}] Eventos cargados: {len(manager.get_all_events())}")

            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"[{guild.name}] Slash Commands sincronizados: {len(synced)}")
            except Exception:
                logger.exception(f"[{guild.name}] Error sincronizando Slash Commands")

        logger.info("Whiteout Duty Manager iniciado correctamente.")

    async def on_guild_join(self, guild: discord.Guild):
        """Si el bot se une a un servidor nuevo mientras ya está
        corriendo, prepara sus datos y sincroniza los comandos ahí
        también, sin necesidad de reiniciar."""

        logger.info(f"Bot añadido a un nuevo servidor: {guild.name} ({guild.id})")

        self.get_event_manager(guild.id)

        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"[{guild.name}] Slash Commands sincronizados: {len(synced)}")
        except Exception:
            logger.exception(f"[{guild.name}] Error sincronizando Slash Commands")


# ======================================================
# MAIN
# ======================================================

async def main():

    bot = WhiteoutBot()

    async with bot:
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
