import discord
from discord.ext import commands

from utils import cycle_manager

DAYS = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo",
]


def fmt(d) -> str:
    return f"{DAYS[d.weekday()]} {d.strftime('%d/%m')}"


class CycleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="set_svs_date")
    @commands.has_permissions(manage_guild=True)
    async def set_svs_date(self, ctx, fecha: str):
        """Fija la fecha del próximo SvS Battle (debe ser un Sábado). Ej: !set_svs_date 12/07/2026"""

        parts = fecha.strip().split("/")
        if len(parts) != 3:
            return await ctx.send("❌ Usa el formato DD/MM/AAAA, ej: `12/07/2026`.")

        try:
            from datetime import date
            day, month, year = map(int, parts)
            anchor = date(year, month, day)
        except ValueError:
            return await ctx.send("❌ Fecha inválida.")

        if anchor.weekday() != 5:
            return await ctx.send(
                f"⚠️ Esa fecha cae en {DAYS[anchor.weekday()]}, y SvS Battle siempre es en Sábado. "
                "Revisa la fecha e inténtalo de nuevo."
            )

        cycle_manager.set_svs_battle_date(anchor)

        await ctx.send(
            f"✅ Fecha de SvS Battle fijada: **{fmt(anchor)}**.\n"
            f"Usa `!ciclo` para ver todas las fechas calculadas de este mes."
        )

    @commands.command(name="ciclo")
    async def ciclo(self, ctx):
        """Muestra las fechas calculadas del ciclo mensual actual."""

        anchor = cycle_manager.get_svs_battle_date()

        if anchor is None:
            return await ctx.send(
                "❌ Todavía no se ha fijado la fecha de SvS Battle. "
                "Un admin debe usar `!set_svs_date DD/MM/AAAA` primero."
            )

        cycle = cycle_manager.compute_cycle(anchor)

        embed = discord.Embed(
            title="🔄 Ciclo mensual calculado",
            description=f"Basado en SvS Battle: **{fmt(anchor)}**",
            color=discord.Color.gold()
        )

        for nombre, fechas in cycle.items():
            if len(fechas) == 1:
                valor = fmt(fechas[0])
            else:
                valor = ", ".join(fmt(f) for f in fechas)

            embed.add_field(name=nombre, value=valor, inline=False)

        embed.set_footer(
            text="Usa estas fechas con /disponible fecha:DD/MM en el evento correspondiente."
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CycleCog(bot))
