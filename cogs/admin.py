import discord
from discord.ext import commands

from cogs.events import day_label


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------
    # Permission check
    # --------------------------------------------------

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.manage_guild

    # --------------------------------------------------
    # Assign a responsible person
    # --------------------------------------------------

    @commands.command(name="assign_role")
    async def assign_role(self, ctx, event_id: str, *, role: str):

        event = self.bot.get_event_manager(ctx.guild.id).get_event(event_id)

        if event is None:
            return await ctx.send("Event not found.")

        if role in event.assigned_roles:
            return await ctx.send("That role is already assigned.")

        event.assigned_roles.append(role)

        self.bot.get_event_manager(ctx.guild.id).save()

        await ctx.send(
            f"Role **{role}** assigned to **{event.name}**."
        )

    # --------------------------------------------------
    # Remove a responsible person
    # --------------------------------------------------

    @commands.command(name="unassign_role")
    async def unassign_role(self, ctx, event_id: str, *, role: str):

        event = self.bot.get_event_manager(ctx.guild.id).get_event(event_id)

        if event is None:
            return await ctx.send("Event not found.")

        if role not in event.assigned_roles:
            return await ctx.send("That role wasn't assigned.")

        event.assigned_roles.remove(role)

        self.bot.get_event_manager(ctx.guild.id).save()

        await ctx.send(
            f"Role **{role}** removed from **{event.name}**."
        )

    # --------------------------------------------------
    # Enable / Disable
    # --------------------------------------------------

    @commands.command(name="toggle_event")
    async def toggle_event(self, ctx, event_id: str):

        event = self.bot.get_event_manager(ctx.guild.id).get_event(event_id)

        if event is None:
            return await ctx.send("Event not found.")

        event.active = not event.active

        self.bot.get_event_manager(ctx.guild.id).save()

        status = "Active" if event.active else "Inactive"

        await ctx.send(
            f"Status updated.\n\n**{event.name}** -> {status}"
        )

    # --------------------------------------------------
    # Set time
    # --------------------------------------------------

    @commands.command(name="set_time")
    async def set_time(self, ctx, event_id: str, time: str):
        from utils.time_utils import parse_time_utc

        event = self.bot.get_event_manager(ctx.guild.id).get_event(event_id)

        if event is None:
            return await ctx.send("Event not found.")

        try:
            parse_time_utc(time)
        except ValueError as e:
            return await ctx.send(str(e))

        event.time = time
        self.bot.get_event_manager(ctx.guild.id).save()

        await ctx.send(f"Time for **{event.name}** updated to {time} UTC.")

    # --------------------------------------------------
    # Load events from data/seed_events.py
    # --------------------------------------------------

    @commands.command(name="seed_events")
    async def seed_events(self, ctx):
        """
        Loads the events defined in data/seed_events.py.
        Only ADDS the ones that don't exist yet (by id); never
        overwrites one that's already created.

        Note: this already happens automatically when the bot
        starts up. This command is only useful if you've added new
