import logging

import discord
from discord.ext import commands, tasks

from utils import guild_config
from utils.time_utils import now_utc, parse_time_utc

logger = logging.getLogger(__name__)


class SchedulerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sent_notifications = set()
        self.check_events.start()

    def cog_unload(self):
        self.check_events.cancel()

    @tasks.loop(minutes=1)
    async def check_events(self):
        now = now_utc()

        weekday = now.weekday()
        current_hour = now.hour
        current_minute = now.minute
        today_iso = now.date().isoformat()

        # Goes through each server separately: each one has its own
        # events, availability, and announcement channel.
        for guild in self.bot.guilds:
            try:
                event_manager = self.bot.get_event_manager(guild.id)
                availability_manager = self.bot.get_availability_manager(guild.id)

                for event in event_manager.get_all_events():

                    if not event.active:
                        continue

                    # Does this event "happen" today?
                    if event.daily:
                        happens_today = True
                    elif event.weekday is not None:
                        happens_today = event.weekday == weekday
                    else:
                        # Variable-date event: only counts as "today"
                        # if someone signed up for today's date.
                        happens_today = bool(
                            availability_manager.get_for_event(event.id, date=today_iso)
                        )

                    if not happens_today:
                        continue

                    event_hour, event_minute = parse_time_utc(event.time)

                    # Event starting exactly now
                    if (
                        current_hour == event_hour
                        and current_minute == event_minute
                    ):

                        key = f"{guild.id}-{event.id}-start-{now.strftime('%Y%m%d%H%M')}"

                        if key not in self.sent_notifications:
                            self.sent_notifications.add(key)

                            await self.notify(
                                guild,
                                event,
                                "The event is starting now.",
                                availability_manager,
                                today_iso,
                            )

                    # Reminders
                    await self.check_reminders(
                        guild,
                        event_manager,
                        availability_manager,
                        event,
                        now,
                        today_iso,
                        event_hour,
                        event_minute
                    )

            except Exception:
                logger.exception(f"Scheduler error for server {guild.id}")

    @check_events.before_loop
    async def before_check_events(self):
        await self.bot.wait_until_ready()

    async def check_reminders(
        self,
        guild,
        event_manager,
        availability_manager,
        event,
        now,
        today_iso,
        event_hour,
        event_minute
    ):

        event_time = now.replace(
            hour=event_hour,
            minute=event_minute,
            second=0,
            microsecond=0
        )

        diff = int((event_time - now).total_seconds() / 60)

        if diff < 0:
            return

        if diff in event.reminders:

            key = f"{guild.id}-{event.id}-{diff}-{now.strftime('%Y%m%d')}"

            if key in self.sent_notifications:
                return

            self.sent_notifications.add(key)

            event.last_notified = key

            event_manager.save()

            await self.notify(
                guild,
                event,
                f"Reminder: {diff} minutes left.",
                availability_manager,
                today_iso,
            )

    async def notify(self, guild, event, message, availability_manager, date_iso):

        # 1) Post in the server's announcement channel (if configured)
        channel = self.get_channel(guild.id)

        if channel is not None:
            embed = discord.Embed(
                title="Alliance Event",
                color=discord.Color.orange()
            )

            embed.add_field(name="Event", value=event.name, inline=False)
            embed.add_field(name="Time (UTC)", value=event.time, inline=True)
            embed.add_field(name="Message", value=message, inline=False)

            if event.assigned_roles:
                embed.add_field(
                    name="Responsible",
                    value="\n".join(event.assigned_roles),
                    inline=False
                )

            try:
                await channel.send(
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            except discord.Forbidden:
                logger.warning(f"[{guild.id}] No permission to post in the announcement channel.")
        else:
            logger.warning(f"[{guild.id}] Announcement channel not found.")

        # 2) Private reminder to each person signed up for this event
        await self.notify_signups(guild, event, message, availability_manager, date_iso)

    async def notify_signups(self, guild, event, message, availability_manager, date_iso):
        """Sends a direct message to each user signed up for this
        event (recurring, or for today's date)."""

        signups = availability_manager.get_for_event(event.id, date=date_iso)

        for entry in signups:

            member = guild.get_member(int(entry.user_id))

            if member is None:
                continue

            embed = discord.Embed(
                title="Event Management Reminder",
                description=f"**{event.name}**",
                color=discord.Color.blurple()
            )

            embed.add_field(name="Server", value=guild.name, inline=False)
            embed.add_field(name="Time (UTC)", value=event.time, inline=True)
            embed.add_field(name="Notice", value=message, inline=False)

            if entry.task:
                embed.add_field(name="Your task", value=entry.task, inline=False)

            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                logger.info(
                    f"[{guild.id}] Could not DM {entry.user_name} "
                    "(their direct messages are closed)."
                )
            except Exception:
                logger.exception(f"[{guild.id}] Error sending reminder to {entry.user_name}")

    def get_channel(self, guild_id):

        channel_id = guild_config.get_announcement_channel(guild_id)

        if not channel_id:
            return None

        return self.bot.get_channel(channel_id)


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
