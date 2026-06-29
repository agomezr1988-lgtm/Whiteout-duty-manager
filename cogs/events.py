import discord
from discord.ext import commands

from utils.event_model import Event
from utils.event_manager import EventManager


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # EventManager global en memoria (luego lo pasamos a persistencia)
        if not hasattr(bot, "event_manager"):
            bot.event_manager = EventManager()

    # -------------------------
    # CREAR EVENTO
    # -------------------------
    @commands.command(name="create_event")
    async def create_event(self, ctx, event_id: str, weekday: int, time: str, *, name: str):
        """
        Crea un evento semanal.
        Ejemplo:
        !create_event guerra 4 20:00 Guerra de Alianza
        """

        if weekday < 0 or weekday > 6:
            return await ctx.send("❌ weekday debe ser entre 0 (Lunes) y 6 (Domingo).")

        event = Event(
            id=event_id,
            name=name,
            description="Evento creado desde Discord",
            weekday=weekday,
            time=time,
            assigned_roles=[]
        )

        self.bot.event_manager.add_event(event)

        await ctx.send(f"✅ Evento creado: **{name}** ({weekday} - {time})")

    # -------------------------
    # LISTAR EVENTOS
    # -------------------------
    @commands.command(name="events")
    async def list_events(self, ctx):
        """
        Lista todos los eventos configurados.
        """

        events = self.bot.event_manager.get_all_events()

        if not events:
            return await ctx.send("📭 No hay eventos configurados.")

        embed = discord.Embed(
            title="📅 Eventos configurados",
            color=discord.Color.blue()
        )

        for e in events:
            embed.add_field(
                name=f"{e.name} ({e.id})",
                value=f"📆 Día: {e.weekday} | 🕒 {e.time} | 🟢 {'Activo' if e.active else 'Inactivo'}",
                inline=False
            )

        await ctx.send(embed=embed)

    # -------------------------
    # EVENTOS DE HOY
    # -------------------------
    @commands.command(name="today")
    async def today_events(self, ctx):
        """
        Muestra eventos del día actual.
        """

        weekday = ctx.message.created_at.weekday()
        events = self.bot.event_manager.get_today_events(weekday)

        if not events:
            return await ctx.send("📭 No hay eventos hoy.")

        embed = discord.Embed(
            title="🔥 Eventos de hoy",
            color=discord.Color.green()
        )

        for e in events:
            embed.add_field(
                name=e.name,
                value=f"🕒 {e.time} | Roles: {', '.join(e.assigned_roles) or 'Ninguno'}",
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
