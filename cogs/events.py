import discord
from discord.ext import commands

from utils.event_model import Event
from utils.time_utils import parse_time_utc


DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def day_label(event) -> str:
    # Returns the day name, or a special label if it has none.
    if event.daily:
        return "Daily"
    if event.weekday is None:
        return "Variable date"
    return DAYS[event.weekday]


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------
    # Create event
    # --------------------------------------------------

    @commands.command(name="create_event")
    @commands.has_permissions(manage_guild=True)
    async def create_event(
        self,
        ctx,
        event_id: str,
        weekday: str,
        time: str,
        *,
        name: str
    ):

        if weekday.lower() in ("variable", "var", "-", "none"):
            weekday_value = None
        else:
            try:
                weekday_value = int(weekday)
            except ValueError:
                return await ctx.send(
                    "Day must be a number (0=Monday...6=Sunday) or the word `variable`."
                )

            if not 0 <= weekday_value <= 6:
                return await ctx.send(
                    "Day must be between 0 (Monday) and 6 (Sunday), or `variable`."
                )

        try:
            parse_time_utc(time)
        except ValueError as e:
            return await ctx.send(str(e))

        if self.bot.get_event_manager(ctx.guild.id).event_exists(event_id):
            return await ctx.send(
                "An event with that ID already exists."
            )

        event = Event(
            id=event_id,
            name=name,
            description="Created from Discord",
            weekday=weekday_value,
            time=time,
        )

        self.bot.get_event_manager(ctx.guild.id).add_event(event)

        await ctx.send(
            f"Event **{name}** created successfully."
        )

    # --------------------------------------------------
    # List events
    # --------------------------------------------------

    @commands.command(name="events")
    async def list_events(self, ctx):

        events = self.bot.get_event_manager(ctx.guild.id).get_all_events()

        if not events:
            return await ctx.send(
                "No events registered."
            )

        # An embed only supports 25 fields: with many events they
        # need to be listed as text instead of one field per event.
        lines = []

        for event in events:
            status = "[ON] " if event.active else "[OFF]"
            lines.append(
                f"{status} **{event.name}** - ID `{event.id}` - "
                f"{day_label(event)} {event.time} UTC"
            )

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
                title="Configured Events" if i == 0 else "\u200b",
                description=chunk,
                color=discord.Color.blurple()
            )
            embeds.append(embed)

        await ctx.send(embeds=embeds[:10])

    # --------------------------------------------------
    # Today's events
    # --------------------------------------------------

    @commands.command(name="today")
    async def today(self, ctx):

        weekday = discord.utils.utcnow().weekday()

        events = self.bot.get_event_manager(ctx.guild.id).get_today_events(
            weekday
        )

        if not events:
            return await ctx.send(
                "No events today."
            )

        embed = discord.Embed(
            title="Today's Events",
            color=discord.Color.green()
        )

        for event in events:

            roles = (
                ", ".join(event.assigned_roles)
                if event.assigned_roles
                else "None assigned"
            )

            embed.add_field(
                name=event.name,
                value=(
                    f"Time: {event.time} UTC\n"
                    f"Responsible: {roles}"
                ),
                inline=False
            )

        await ctx.send(embed=embed)

    # --------------------------------------------------
    # Delete event
    # --------------------------------------------------

    @commands.command(name="delete_event")
    @commands.has_permissions(manage_guild=True)
    async def delete_event(self, ctx, event_id: str):

        if self.bot.get_event_manager(ctx.guild.id).remove_event(event_id):
            await ctx.send("Event deleted successfully.")
        else:
            await ctx.send("Event not found.")


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
