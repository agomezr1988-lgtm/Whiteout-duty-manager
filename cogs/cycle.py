import discord
from discord.ext import commands

from utils import cycle_manager

DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


def fmt(d) -> str:
    return f"{DAYS[d.weekday()]} {d.strftime('%d/%m')}"


class CycleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="set_svs_date")
    @commands.has_permissions(manage_guild=True)
    async def set_svs_date(self, ctx, date_str: str):
        # Sets the date of the next SvS Battle (must be a Saturday). Ex: !set_svs_date 12/07/2026

        parts = date_str.strip().split("/")
        if len(parts) != 3:
            return await ctx.send("Use the DD/MM/YYYY format, e.g. `12/07/2026`.")

        try:
            from datetime import date
            day, month, year = map(int, parts)
            anchor = date(year, month, day)
        except ValueError:
            return await ctx.send("Invalid date.")

        if anchor.weekday() != 5:
            return await ctx.send(
                f"That date falls on a {DAYS[anchor.weekday()]}, but SvS Battle is always on a "
                "Saturday. Please check the date and try again."
            )

        cycle_manager.set_svs_battle_date(ctx.guild.id, anchor)

        await ctx.send(
            f"SvS Battle date set: **{fmt(anchor)}**.\n"
            f"Use `!cycle` to see all the calculated dates for this month."
        )

    @commands.command(name="cycle")
    async def cycle(self, ctx):
        # Shows the calculated dates for the current monthly cycle.

        anchor = cycle_manager.get_svs_battle_date(ctx.guild.id)

        if anchor is None:
            return await ctx.send(
                "The SvS Battle date hasn't been set yet. "
                "An admin needs to use `!set_svs_date DD/MM/YYYY` first."
            )

        cycle_data = cycle_manager.compute_cycle(anchor)

        embed = discord.Embed(
            title="Calculated Monthly Cycle",
            description=f"Based on SvS Battle: **{fmt(anchor)}**",
            color=discord.Color.gold()
        )

        for name, dates in cycle_data.items():
            if len(dates) == 1:
                value = fmt(dates[0])
            else:
                value = ", ".join(fmt(d) for d in dates)

            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(
            text="Use these dates with /available date:DD/MM on the matching event."
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CycleCog(bot))
