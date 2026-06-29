import discord
from discord.ext import commands, tasks
from utils.time_utils import now_utc, parse_time_utc


class SchedulerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_events.start()

    def cog_unload(self):
        self.check_events.cancel()

    # -------------------------
    # LOOP UTC GLOBAL
    # -------------------------
    @tasks.loop(minutes=1)
    async def check_events(self):
        now = now_utc()

        weekday = now.weekday()
        current_hour = now.hour
        current_minute = now.minute

        events = self.bot.event_manager.get_today_events(weekday)

        for event in events:
            if not event.active:
                continue

            event_hour, event_minute = parse_time_utc(event.time)

            # Evento exacto
            if current_hour == event_hour and current_minute == event_minute:
                await self.notify(event, "🚨 Evento comienza ahora (UTC)")

            # Recordatorios
            await self.check_reminders(event, now, event_hour, event_minute)

    # -------------------------
    # RECORDATORIOS OPTIMIZADOS
    # -------------------------
    async def check_reminders(self, event, now, event_hour, event_minute):

        event_time = now.replace(
            hour=event_hour,
            minute=event_minute,
            second=0,
            microsecond=0
        )

        diff = int((event_time - now).total_seconds() / 60)

        if diff in event.reminders:
            key = f"{event.id}-{diff}-{now.date()}"

            if event.last_notified == key:
                return

            event.last_notified = key

            await self.notify(
                event,
                f"⏳ Recordatorio UTC: evento en {diff} minutos"
            )

    # -------------------------
    # NOTIFICACIÓN
    # -------------------------
    async def notify(self, event, message):
        channel = self.get_channel()
        if not channel:
            return

        embed = discord.Embed(
            title="📅 Evento de Alianza",
            description=f"**{event.name}**\n\n{message}",
            color=discord.Color.orange()
        )

        if event.assigned_roles:
            embed.add_field(
                name="👥 Responsables",
                value=", ".join(event.assigned_roles),
                inline=False
            )

        await channel.send(embed=embed)

    # -------------------------
    # CANAL AUTOMÁTICO
    # -------------------------
    def get_channel(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    return channel
        return None


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
