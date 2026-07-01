import discord
from discord import app_commands
from discord.ext import commands

DAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


class DashboardView(discord.ui.View):
    """Botones del panel de control. timeout=180: tras 3 minutos
    sin uso, el botón deja de responder (mensaje efímero de todos
    modos, así que no supone un problema)."""

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=180)
        self.bot = bot

    @discord.ui.button(
        label="📋 Ver todos los eventos",
        style=discord.ButtonStyle.primary,
    )
    async def ver_eventos(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        events = self.bot.event_manager.get_all_events()

        if not events:
            return await interaction.response.send_message(
                "📭 No hay eventos registrados.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📅 Eventos configurados",
            color=discord.Color.blurple()
        )

        for event in events:

            estado = "🟢 Activo" if event.active else "🔴 Inactivo"

            embed.add_field(
                name=event.name,
                value=(
                    f"🆔 `{event.id}`\n"
                    f"📅 {DAYS[event.weekday]}\n"
                    f"🕒 {event.time} UTC\n"
                    f"{estado}"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="panel",
        description="Abre el panel de control del bot"
    )
    async def panel(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="⚙️ Panel de control — Whiteout Duty Manager",
            description="Usa los botones de abajo para consultar información.",
            color=discord.Color.blurple()
        )

        view = DashboardView(self.bot)

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(DashboardCog(bot))
