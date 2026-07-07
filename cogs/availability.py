import logging
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils import cycle_manager, guild_config
from utils.time_utils import get_week_dates, parse_date_ddmmyyyy, now_utc

logger = logging.getLogger(__name__)

DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Events tied to the monthly cycle (id -> key used in cycle_manager)
CYCLE_EVENTS = {
    "svs_prep": "SvS Preparation Phase",
    "svs_battle": "SvS Battle",
    "alliance_mobilization": "Alliance Mobilization",
    "koi": "King of Icefield (KoI)",
    "sunfire_castle": "Sunfire Castle (Normal)",
    "crazy_joe": "Crazy Joe",
    "bia": "BIA",
}


def day_label(event) -> str:
    if event.daily:
        return "Daily"
    if event.weekday is None:
        return "Variable date"
    return DAYS[event.weekday]


class AvailabilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # One board (self-updating message) per server
        self.board_message_ids: dict[int, int] = {}

    # ==================================================
    # EVENT AUTOCOMPLETE
    # ==================================================
    async def event_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        event_manager = self.bot.get_event_manager(interaction.guild_id)
        events = event_manager.get_all_events()
        choices = []

        for event in events:

            if not event.active:
                continue

            label = f"{event.name} ({day_label(event)} {event.time} UTC)"

            if current.lower() in label.lower() or current.lower() in event.id.lower():
                choices.append(
                    app_commands.Choice(name=label[:100], value=event.id)
                )

        return choices[:25]

    # ==================================================
    # DATE AUTOCOMPLETE (depends on the chosen event)
    # Suggests real dates instead of requiring manual typing.
    # ==================================================
    async def date_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        event_id = interaction.namespace.event

        if not event_id:
            return []

        event_manager = self.bot.get_event_manager(interaction.guild_id)
        event = event_manager.get_event(event_id)

        if event is None:
            return []

        choices = []

        # Event tied to the monthly cycle: suggest the calculated dates
        if event.id in CYCLE_EVENTS:
            anchor = cycle_manager.get_svs_battle_date(interaction.guild_id)

            if anchor:
                cycle_data = cycle_manager.compute_cycle(anchor)
                dates = cycle_data.get(CYCLE_EVENTS[event.id], [])

                for d in dates:
                    label = f"{DAYS[d.weekday()]} {d.strftime('%d/%m')}"
                    value = d.strftime("%d/%m/%Y")
                    if current.lower() in label.lower():
                        choices.append(app_commands.Choice(name=label, value=value))

                if choices:
                    return choices[:25]

            # No SvS date set yet: warn instead of leaving it empty
            return [app_commands.Choice(
                name="No SvS date set yet - use !set_svs_date or type DD/MM",
                value=""
            )]

        # Daily event: only "recurring" makes sense
        if event.daily:
            return [app_commands.Choice(name="Every day (recurring)", value="")]

        # Fixed weekly event: recurring + the next specific occurrence
        if event.weekday is not None:
            today = now_utc().date()
            days_ahead = (event.weekday - today.weekday()) % 7
            next_date = today + timedelta(days=days_ahead)

            choices.append(app_commands.Choice(
                name="Every week (recurring)", value=""
            ))
            choices.append(app_commands.Choice(
                name=f"Only {DAYS[event.weekday]} {next_date.strftime('%d/%m')}",
                value=next_date.strftime("%d/%m/%Y")
            ))
            return choices

        # Variable-date event with no known cycle: suggest the next 14 days
        today = now_utc().date()
        for i in range(14):
            d = today + timedelta(days=i)
            label = f"{DAYS[d.weekday()]} {d.strftime('%d/%m')}"
            if current.lower() in label.lower() or not current:
                choices.append(app_commands.Choice(name=label, value=d.strftime("%d/%m/%Y")))

        return choices[:25]

    # ==================================================
    # TASK AUTOCOMPLETE (depends on the chosen event)
    # ==================================================
    async def task_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        event_id = interaction.namespace.event

        if not event_id:
            return []

        event_manager = self.bot.get_event_manager(interaction.guild_id)
        event = event_manager.get_event(event_id)

        if event is None or not event.tasks:
            return []

        return [
            app_commands.Choice(name=t[:100], value=t)
            for t in event.tasks
            if current.lower() in t.lower()
        ][:25]

    # ==================================================
    # /available
    # ==================================================
    @app_commands.command(
        name="available",
        description="Mark yourself as available for an event"
    )
    @app_commands.describe(
        event="Pick the event from the list",
        date="Pick a date from the suggested list (or leave empty if the event allows it)",
        task="Optional: the specific task you're signing up for within the event",
    )
    @app_commands.autocomplete(
        event=event_autocomplete,
        date=date_autocomplete,
        task=task_autocomplete,
    )
    async def available(
        self,
        interaction: discord.Interaction,
        event: str,
        date: str = None,
        task: str = None,
    ):

        event_manager = self.bot.get_event_manager(interaction.guild_id)
        event_obj = event_manager.get_event(event)

        if event_obj is None:
            return await interaction.response.send_message(
                "Event not found. Please pick one from the suggested list.",
                ephemeral=True
            )

        # Variable-date events (no cycle, no fixed day) always need a
        # specific date.
        if event_obj.weekday is None and not event_obj.daily and not date:
            return await interaction.response.send_message(
                f"**{event_obj.name}** is a variable-date event. "
                "Pick a date from the suggested list in the `date` field.",
                ephemeral=True
            )

        date_iso = None

        if date:
            try:
                date_iso = parse_date_ddmmyyyy(date)
            except ValueError as e:
                return await interaction.response.send_message(
                    str(e), ephemeral=True
                )

        if task and event_obj.tasks and task not in event_obj.tasks:
            return await interaction.response.send_message(
                f"That task doesn't exist for **{event_obj.name}**. "
                f"Pick it from the suggested list.",
                ephemeral=True
            )

        rank = self._get_rank(interaction.guild_id, interaction.user)

        availability_manager = self.bot.get_availability_manager(interaction.guild_id)

        availability_manager.set_available(
            event_id=event_obj.id,
            user_id=str(interaction.user.id),
            user_name=interaction.user.display_name,
            rank=rank,
            date=date_iso,
            task=task,
        )

        if date_iso:
            when = f"on {date_iso}"
        elif event_obj.daily:
            when = "every day"
        else:
            when = f"every {day_label(event_obj)}"

        task_txt = f" - task: **{task}**" if task else ""

        await interaction.response.send_message(
            f"Signed up for **{event_obj.name}** ({when}){task_txt}.",
            ephemeral=True
        )

        await self.refresh_board(interaction.guild_id)

    # ==================================================
    # /unavailable
    # ==================================================
    @app_commands.command(
        name="unavailable",
        description="Remove your availability for an event"
    )
    @app_commands.describe(
        event="Pick the event from the list",
        date="Only needed if you signed up for a specific date",
        task="Only needed if you signed up for a specific task",
    )
    @app_commands.autocomplete(
        event=event_autocomplete,
        date=date_autocomplete,
        task=task_autocomplete,
    )
    async def unavailable(
        self,
        interaction: discord.Interaction,
        event: str,
        date: str = None,
        task: str = None,
    ):

        event_manager = self.bot.get_event_manager(interaction.guild_id)
        event_obj = event_manager.get_event(event)

        if event_obj is None:
            return await interaction.response.send_message(
                "Event not found.", ephemeral=True
            )

        date_iso = None

        if date:
            try:
                date_iso = parse_date_ddmmyyyy(date)
            except ValueError as e:
                return await interaction.response.send_message(
                    str(e), ephemeral=True
                )

        availability_manager = self.bot.get_availability_manager(interaction.guild_id)

        removed = availability_manager.remove_available(
            event_id=event_obj.id,
            user_id=str(interaction.user.id),
            date=date_iso,
            task=task,
        )

        if removed:
            await interaction.response.send_message(
                f"Removed from **{event_obj.name}**.",
                ephemeral=True
            )
            await self.refresh_board(interaction.guild_id)
        else:
            await interaction.response.send_message(
                "You weren't signed up there (check if you set the same date/task as when you signed up).",
                ephemeral=True
            )

    # ==================================================
    # /calendar
    # ==================================================
    @app_commands.command(
        name="calendar",
        description="Shows the weekly availability calendar"
    )
    @app_commands.describe(week="Which week do you want to see")
    @app_commands.choices(week=[
        app_commands.Choice(name="This week", value="current"),
        app_commands.Choice(name="Next week", value="next"),
    ])
    async def calendar(
        self,
        interaction: discord.Interaction,
        week: app_commands.Choice[str] = None,
    ):
        weeks_ahead = 1 if week and week.value == "next" else 0
        embed = self.build_calendar_embed(interaction.guild_id, weeks_ahead=weeks_ahead)
        await interaction.response.send_message(embed=embed)

    # ==================================================
    # BUILD THE CALENDAR EMBED
    # ==================================================
    def build_calendar_embed(self, guild_id: int, weeks_ahead: int = 0) -> discord.Embed:

        event_manager = self.bot.get_event_manager(guild_id)
        availability_manager = self.bot.get_availability_manager(guild_id)

        today = now_utc().date()
        reference = today + timedelta(weeks=weeks_ahead)
        week_dates = get_week_dates(reference=reference)

        week_title = "this week" if weeks_ahead == 0 else "next week"

        embed = discord.Embed(
            title="Weekly Calendar - Whiteout Duty Manager",
            color=discord.Color.from_rgb(79, 195, 247),
            description=(
                f"Week of **{week_dates[0].strftime('%d/%m')}** "
                f"to **{week_dates[6].strftime('%d/%m')}** ({week_title})  -  Times in UTC\n"
                f"------------------------------"
            )
        )

        events = event_manager.get_all_events()

        # --- Daily events: shown once, at the top ---
        daily_events = [e for e in events if e.daily and e.active]

        if daily_events:
            lines = [
                self._format_event_signups(availability_manager, e, date=None)
                for e in daily_events
            ]
            embed.add_field(
                name="EVERY DAY",
                value="\n\n".join(lines),
                inline=False
            )

        # --- Fixed-day events, grouped by weekday ---
        for weekday in range(7):

            day_events = [
                e for e in events
                if e.weekday == weekday and e.active and not e.daily
            ]

            if not day_events:
                continue

            day_date = week_dates[weekday]
            date_iso = day_date.isoformat()
            is_today = day_date == today

            lines = [
                self._format_event_signups(availability_manager, e, date=date_iso)
                for e in day_events
            ]

            field_name = f"{DAYS[weekday]} {day_date.strftime('%d/%m')}"
            if is_today:
                field_name = f">> {field_name} - TODAY"

            embed.add_field(
                name=field_name,
                value="\n\n".join(lines),
                inline=False
            )

        # --- Variable-date events with signups this week ---
        variable_events = [e for e in events if e.weekday is None and not e.daily and e.active]
        variable_lines = []

        for event in variable_events:
            entries_with_date = availability_manager.get_dated_for_event(event.id)

            if not entries_with_date:
                continue

            by_date = {}
            for a in entries_with_date:
                by_date.setdefault(a.date, []).append(a)

            for date_str, entries in sorted(by_date.items()):
                names = ", ".join(
                    a.user_name + (f" ({a.rank})" if a.rank else "") +
                    (f" [{a.task}]" if a.task else "")
                    for a in entries
                )
                variable_lines.append(f"**{event.name}** - {date_str}\n{names}")

        if variable_lines:
            embed.add_field(
                name="VARIABLE-DATE EVENTS",
                value="\n\n".join(variable_lines),
                inline=False
            )

        if not embed.fields:
            embed.description += "\n\nNo active events configured."

        embed.set_footer(text="Use /available to sign up for an event")

        return embed

    def _format_event_signups(self, availability_manager, event, date: str = None) -> str:
        signups = availability_manager.get_for_event(event.id, date=date)
        total = len(signups)
        counter = f" ({total} signed up)" if total else ""

        if not event.tasks:
            if signups:
                names = " | ".join(
                    a.user_name + (f" [{a.rank}]" if a.rank else "")
                    for a in signups
                )
            else:
                names = "Nobody signed up yet"
            return f"**{event.name}**  ({event.time} UTC){counter}\n{names}"

        # Event with tasks: group by task
        lines = [f"**{event.name}**  ({event.time} UTC){counter}"]

        no_task = [a for a in signups if not a.task]
        if no_task:
            names = ", ".join(a.user_name for a in no_task)
            lines.append(f"  General: {names}")

        for task in event.tasks:
            assigned = [a for a in signups if a.task == task]
            names = ", ".join(a.user_name for a in assigned) if assigned else "open"
            lines.append(f"  {task}: {names}")

        return "\n".join(lines)

    # ==================================================
    # SELF-UPDATING BOARD (one per server)
    # ==================================================
    async def refresh_board(self, guild_id: int):

        channel_id = guild_config.get_calendar_channel(guild_id)

        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)

        if channel is None:
            logger.warning(f"[{guild_id}] Calendar board channel not found.")
            return

        embed = self.build_calendar_embed(guild_id)

        board_message_id = self.board_message_ids.get(guild_id)

        if board_message_id:
            try:
                message = await channel.fetch_message(board_message_id)
                await message.edit(embed=embed)
                return
            except discord.NotFound:
                self.board_message_ids.pop(guild_id, None)
            except discord.Forbidden:
                logger.warning(f"[{guild_id}] No permission to edit the board message.")
                return

        message = await channel.send(embed=embed)
        self.board_message_ids[guild_id] = message.id

    # ==================================================
    # UTILITY: user's R4/R5 rank (role names are per-server)
    # ==================================================
    def _get_rank(self, guild_id: int, member) -> str:
        role_names = [r.name for r in getattr(member, "roles", [])]

        if guild_config.get_role_r5(guild_id) in role_names:
            return "R5"

        if guild_config.get_role_r4(guild_id) in role_names:
            return "R4"

        return ""


async def setup(bot):
    await bot.add_cog(AvailabilityCog(bot))
