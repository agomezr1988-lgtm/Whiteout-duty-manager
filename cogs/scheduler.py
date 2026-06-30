import logging

import discord
from discord.ext import commands, tasks

from config import ANNOUNCEMENT_CHANNEL_ID
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

        try:
            events = self.bot.event_manager.get_today_events(weekday)

            for event in events:

                if not event.active:
                    continue

                event_hour, event_minute = parse_time_utc(event.time)

                # Evento exacto
                if (
                    current_hour == event_hour
                    and current_minute == event_minute
                ):

                    key = f"{event.id}-start-{now.strftime('%Y%m%d%H%M')}"

                    if key not in self.sent_notifications:
                        self.sent_notifications.add(key)

                        await self.notify(
                            event,
                            "🚨 **El evento comienza ahora.**"
                        )

                # Recordatorios
                await self.check_reminders(
                    event,
                    now,
                    event_hour,
                    event_minute
                )

        except Exception:
            logger.exception("Error en Scheduler")

    @check_events.before_loop
    async def before_check_events(self):
        await self.bot.wait_until_ready()

    async def check_reminders(
        self,
        event,
        now,
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

            key = f"{event.id}-{diff}-{now.strftime('%Y%m%d')}"

            if key in self.sent_notifications:
                return

            self.sent_notifications.add(key)

            event.last_notified = key

            self.bot.event_manager.save()

            await self.notify(
                event,
                f"⏳ **Recordatorio:** quedan **{diff} minutos**."
            )

    async def notify(self, event, message):

        channel = self.get_channel()

        if channel is None:
            logger.warning("No se encontró el canal de anuncios.")
            return

        embed = discord.Embed(
            title="📅 Evento de Alianza",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Evento",
            value=event.name,
            inline=False
        )

        embed.add_field(
            name="Hora (UTC)",
            value=event.time,
            inline=True
        )

        embed.add_field(
            name="Mensaje",
            value=message,
            inline=False
        )

        if event.assigned_roles:

            embed.add_field(
                name="Responsables",
                value="\n".join(event.assigned_roles),
                inline=False
            )

        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )

    def get_channel(self):

        if not ANNOUNCEMENT_CHANNEL_ID:
            return None

        return self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
