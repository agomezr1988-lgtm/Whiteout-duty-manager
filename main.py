import discord
from discord.ext import commands
import os
import asyncio

# Intents (ajustables según necesidades del bot)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class WhiteoutBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """
        Se ejecuta al iniciar el bot antes de conectar.
        Aquí cargamos extensiones (cogs).
        """

        cogs = [
            "cogs.admin",
            "cogs.events",
            "cogs.scheduler",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"[OK] Cog cargado: {cog}")
            except Exception as e:
                print(f"[ERROR] Cog {cog} no cargado: {e}")

    async def on_ready(self):
        print(f"Bot conectado como {self.user} (ID: {self.user.id})")
        print("Sistema Whiteout Survival activo.")


def run_bot():
    bot = WhiteoutBot()
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        raise ValueError("No se encontró DISCORD_TOKEN en variables de entorno.")

    bot.run(token)


if __name__ == "__main__":
    run_bot()


