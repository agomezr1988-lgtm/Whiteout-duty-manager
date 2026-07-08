import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
from utils.event_manager import EventManager
from utils.availability_manager import AvailabilityManager

# ======================================================
# LOAD .ENV
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
    # Multi-server bot: each server (guild) has its own events,
    # availability, SvS cycle, and configuration (R4/R5 role names,
    # channels). Data is stored separately under
    # data/guilds/<guild_id>/.

    def __init__(self):

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )

        # One EventManager and one AvailabilityManager per server,
        # created on demand the first time they're needed.
        self._event_managers = {}
        self._availability_managers = {}

    # --------------------------------------------------
    # Access to the per-server managers
    # --------------------------------------------------
    def get_event_manager(self, guild_id: int) -> EventManager:
        if guild_id not in self._event_managers:
            manager = EventManager(guild_id)

            # Auto-load reference events for this server
            from utils.seed_loader import load_seed_events
            created, _ = load_seed_events(manager)
            if created:
                logger.info(f"[{guild_id}] Events loaded automatically: {len(created)}")

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
                logger.info(f"Cog loaded: {cog}")

            except Exception:
                logger.exception(f"Could not load {cog}")

    async def on_ready(self):

        logger.info("--------------------------------------")
        logger.info(f"Bot connected as {self.user}")
        logger.info(f"ID: {self.user.id}")
        logger.info(f"Servers: {len(self.guilds)}")
        logger.info("--------------------------------------")

        # Prepares data and syncs Slash Commands in EVERY server the
        # bot is in, so they appear instantly (a global sync can
        # take up to an hour).
        for guild in self.guilds:

            manager = self.get_event_manager(guild.id)
            logger.info(f"[{guild.name}] Events loaded: {len(manager.get_all_events())}")

            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"[{guild.name}] Slash Commands synced: {len(synced)}")
            except Exception:
                logger.exception(f"[{guild.name}] Error syncing Slash Commands")

        logger.info("Whiteout Duty Manager started successfully.")

    async def on_guild_join(self, guild: discord.Guild):
        # If the bot joins a new server while already running,
        # prepares its data and syncs commands there too, without
        # needing a restart.

        logger.info(f"Bot added to a new server: {guild.name} ({guild.id})")

        self.get_event_manager(guild.id)

        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"[{guild.name}] Slash Commands synced: {len(synced)}")
        except Exception:
            logger.exception(f"[{guild.name}] Error syncing Slash Commands")


# ======================================================
# MAIN
# ======================================================

async def main():

    bot = WhiteoutBot()

    async with bot:
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
