import discord
from discord import app_commands
from discord.ext import commands


def day_label(event) -> str:
    DAYS = [
        "Lunes", "Martes", "Miércoles", "Jueves",
        "Viernes", "Sábado", "Domingo",
    ]
    if event.weekday is None:
        return "Fecha variable"
    return DAYS[event.weekday]


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

        # Un embed solo admite 25 campos: con muchos eventos hay que
        # listarlos como texto en vez de un campo por evento.
        lines = []

        for event in events:
            estado = "🟢" if event.active else "🔴"
            lines.append(
                f"{estado} **{event.name}** — 🆔 `{event.id}` — "
                f"{day_label(event)} {event.time} UTC"
            )

        # Trocea en bloques de hasta 4000 caracteres (límite de descripción: 4096)
        chunks = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > 4000:
                chunks.append(current)
                current = ""
            current += line + "\n"
        if current:
            chunks.append(current)

        embeds = []
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title="📅 Eventos configurados" if i == 0 else "\u200b",
                description=chunk,
                color=discord.Color.blurple()
            )
            embeds.append(embed)

        await interaction.response.send_message(embeds=embeds[:10], ephemeral=True)


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
