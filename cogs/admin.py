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
        # Loads the events defined in data/seed_events.py.
        # Only ADDS the ones that don't exist yet (by id); never
        # overwrites one that's already created.

        # Note: this already happens automatically when the bot
        # starts up. This command is only useful if you've added new
        # events to seed_events.py and want to load them without
        # restarting.

        from utils.seed_loader import load_seed_events

        created, already_existed = load_seed_events(self.bot.get_event_manager(ctx.guild.id))

        summary = f"{len(created)} new events created."

        if already_existed:
            summary += f"\n{len(already_existed)} already existed and were left untouched."

        await ctx.send(summary)

    # --------------------------------------------------
    # Set the event's signup tasks
    # --------------------------------------------------

    @commands.command(name="set_tasks")
    async def set_tasks(self, ctx, event_id: str, *, tasks: str):
        # Sets the internal tasks of an event, comma-separated.
        # Example: !set_tasks foundry Messages & teams, Battle coordination
        # To clear all tasks: !set_tasks foundry -

        event = self.bot.get_event_manager(ctx.guild.id).get_event(event_id)

        if event is None:
            return await ctx.send("Event not found.")

        if tasks.strip() == "-":
            event.tasks = []
        else:
            event.tasks = [t.strip() for t in tasks.split(",") if t.strip()]

        self.bot.get_event_manager(ctx.guild.id).save()

        if event.tasks:
            task_list = "\n".join(f"- {t}" for t in event.tasks)
            await ctx.send(
                f"Tasks for **{event.name}** updated:\n{task_list}"
            )
        else:
            await ctx.send(
                f"**{event.name}** no longer has any signup tasks defined."
            )

    # --------------------------------------------------
    # Force re-sync of Slash Commands (fixes stale/renamed commands)
    # --------------------------------------------------

    @commands.command(name="sync_commands")
    async def sync_commands(self, ctx):
        # Clears leftover GLOBAL commands (e.g. old Spanish-named ones
        # from earlier versions), reloads all cogs so their commands
        # register again, and re-syncs everything for this server.
        # Use this if an old or renamed command still shows up or
        # errors out, or if commands disappear after a cleanup.

        await ctx.send("Re-syncing commands, please wait...")

        try:
            # Step 1: wipe any leftover global commands on Discord's side
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()

            # Step 2: reload every cog so their commands register again
            # in the bot's local command tree (clearing above empties it)
            for extension in list(self.bot.extensions.keys()):
                await self.bot.reload_extension(extension)

            # Step 3: rebuild this server's commands from the
            # freshly-repopulated tree
            self.bot.tree.clear_commands(guild=ctx.guild)
            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)

            await ctx.send(
                f"Done. Cleared old global commands, reloaded all cogs, and synced "
                f"{len(synced)} commands for this server. If Discord still shows an "
                "old command, fully restart your Discord client (not just reload)."
            )
        except Exception as e:
            await ctx.send(f"Sync failed: {e}")

    # --------------------------------------------------
    # Info
    # --------------------------------------------------

    @commands.command(name="event_info")
    async def event_info(self, ctx, event_id: str):

        event = self.bot.get_event_manager(ctx.guild.id).get_event(event_id)

        if event is None:
            return await ctx.send("Event not found.")

        embed = discord.Embed(
            title=event.name,
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="ID",
            value=event.id,
            inline=True
        )

        embed.add_field(
            name="Day",
            value=day_label(event),
            inline=True
        )

        embed.add_field(
            name="Time",
            value=f"{event.time} UTC",
            inline=True
        )

        embed.add_field(
            name="Status",
            value="Active" if event.active else "Inactive",
            inline=True
        )

        embed.add_field(
            name="Duration",
            value=str(event.duration) if event.duration else "Not set",
            inline=True
        )

        embed.add_field(
            name="Reminders",
            value=", ".join(f"{m} min" for m in event.reminders),
            inline=False
        )

        embed.add_field(
            name="Signup tasks",
            value=", ".join(event.tasks) if event.tasks else "This event has no tasks defined",
            inline=False
        )

        embed.add_field(
            name="Responsible",
            value=", ".join(event.assigned_roles) if event.assigned_roles else "None assigned",
            inline=False
        )

        if event.notes:
            embed.add_field(
                name="Notes",
                value=event.notes,
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
