from datetime import datetime, timezone


def now_utc():
    """Hora actual en UTC"""
    return datetime.now(timezone.utc)


def parse_time_utc(time_str: str):
    """
    Convierte "HH:MM" en objeto time usable en UTC context
    """
    hour, minute = map(int, time_str.split(":"))
    return hour, minute

cogs/panel.py

import discord
from discord.ext import commands


class EventPanel(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    # -------------------------
    # BOTÓN: VER EVENTOS
    # -------------------------
    @discord.ui.button(label="📅 Ver eventos", style=discord.ButtonStyle.primary)
    async def view_events(self, interaction: discord.Interaction, button: discord.ui.Button):

        events = self.bot.event_manager.get_all_events()

        if not events:
            await interaction.response.send_message("📭 No hay eventos.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📅 Eventos de la alianza (UTC)",
            color=discord.Color.blue()
        )

        for e in events:
            embed.add_field(
                name=f"{e.name} ({e.id})",
                value=f"🕒 {e.time} UTC | 📆 Día {e.weekday} | {'🟢' if e.active else '🔴'}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------------
    # BOTÓN: CREAR EVENTO SIMPLE
    # -------------------------
    @discord.ui.button(label="➕ Crear evento", style=discord.ButtonStyle.success)
    async def create_event(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "🧩 Usa: `!create_event id weekday HH:MM nombre` (modo rápido activo)",
            ephemeral=True
        )

    # -------------------------
    # BOTÓN: PANEL R4/R5
    # -------------------------
    @discord.ui.button(label="👥 Roles R4/R5", style=discord.ButtonStyle.secondary)
    async def roles_panel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "⚙️ Usa `!assign_role` o `!event_info` para gestionar roles.",
            ephemeral=True
        )


class PanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="panel")
    async def panel(self, ctx):
        """
        Muestra el panel principal del bot.
        """

        embed = discord.Embed(
            title="⚙️ Panel de Control de Alianza",
            description="Gestión de eventos en UTC",
            color=discord.Color.dark_teal()
        )

        view = EventPanel(self.bot)

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PanelCog(bot))
