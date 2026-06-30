import discord
from discord.ext import commands

from utils.event_model import Event
from utils.time_utils import parse_time_utc


DAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------
    # Crear evento
    # --------------------------------------------------

    @commands.command(name="create_event")
    @commands.has_permissions(manage_guild=True)
    async def create_event(
        self,
        ctx,
        event_id: str,
        weekday: int,
        time: str,
        *,
        name: str
    ):

        if not 0 <= weekday <= 6:
            return await ctx.send(
                "❌ El día debe estar entre 0 (Lunes) y 6 (Domingo)."
            )

        try:
            parse_time_utc(time)
        except ValueError as e:
            return await ctx.send(str(e))

        if self.bot.event_manager.event_exists(event_id):
            return await ctx.send(
                "❌ Ya existe un evento con ese ID."
            )

        event = Event(
            id=event_id,
            name=name,
            description="Creado desde Discord",
            weekday=weekday,
            time=time,
        )

        self.bot.event_manager.add_event(event)

        await ctx.send(
            f"✅ Evento **{name}** creado correctamente."
        )

    # --------------------------------------------------
    # Lista de eventos
    # --------------------------------------------------

    @commands.command(name="events")
    async def list_events(self, ctx):

        events = self.bot.event_manager.get_all_events()

        if not events:
            return await ctx.send(
                "📭 No hay eventos registrados."
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

        await ctx.send(embed=embed)

    # --------------------------------------------------
    # Eventos de hoy
    # --------------------------------------------------

    @commands.command(name="today")
    async def today(self, ctx):

        weekday = discord.utils.utcnow().weekday()

        events = self.bot.event_manager.get_today_events(
            weekday
        )

        if not events:
            return await ctx.send(
                "📭 Hoy no hay eventos."
            )

        embed = discord.Embed(
            title="🔥 Eventos de hoy",
            color=discord.Color.green()
        )

        for event in events:

            roles = (
                ", ".join(event.assigned_roles)
                if event.assigned_roles
                else "Sin asignar"
            )

            embed.add_field(
                name=event.name,
                value=(
                    f"🕒 {event.time} UTC\n"
                    f"👥 {roles}"
                ),
                inline=False
            )

        await ctx.send(embed=embed)

    # --------------------------------------------------
    # Eliminar evento
    # --------------------------------------------------

    @commands.command(name="delete_event")
    @commands.has_permissions(manage_guild=True)
    async def delete_event(self, ctx, event_id: str):

        if self.bot.event_manager.remove_event(event_id):
            await ctx.send("🗑️ Evento eliminado correctamente.")
        else:
            await ctx.send("❌ Evento no encontrado.")


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
