import discord
from discord import app_commands
from discord.ext import commands
from datetime import date

from utils import cycle_manager, guild_config
from utils.seed_loader import load_seed_events
from utils.event_model import Event
from utils.time_utils import parse_time_utc

DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


def day_label(event) -> str:
    if event.daily:
        return "Daily"
    if event.weekday is None:
        return "Variable"
    return DAYS[event.weekday]


def has_management_access(guild_id: int, user) -> bool:
    # Grants access if the user can manage the server, or has the
    # R4 or R5 role configured for THIS server.

    perms = getattr(user, "guild_permissions", None)
    if perms and perms.manage_guild:
        return True

    role_names = [r.name for r in getattr(user, "roles", [])]
    return (
        guild_config.get_role_r4(guild_id) in role_names
        or guild_config.get_role_r5(guild_id) in role_names
    )


# ==========================================================
# View all events (normal panel, for everyone)
# ==========================================================
class ViewEventsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="View all events", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        event_manager = interaction.client.get_event_manager(interaction.guild_id)
        events = event_manager.get_all_events()

        if not events:
            return await interaction.response.send_message(
                "No events registered.", ephemeral=True
            )

        lines = []
        for event in events:
            status = "[ON] " if event.active else "[OFF]"
            lines.append(
                f"{status} **{event.name}** - ID `{event.id}` - "
                f"{day_label(event)} {event.time} UTC"
            )

        chunks, current = [], ""
        for line in lines:
            if len(current) + len(line) + 1 > 4000:
                chunks.append(current)
                current = ""
            current += line + "\n"
        if current:
            chunks.append(current)

        embeds = [
            discord.Embed(
                title="Configured Events" if i == 0 else "\u200b",
                description=chunk,
                color=discord.Color.blurple()
            )
            for i, chunk in enumerate(chunks)
        ]

        await interaction.response.send_message(embeds=embeds[:10], ephemeral=True)


# ==========================================================
# Signup status: events with people signed up vs no one
# ==========================================================
class SignupStatusButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Signup status", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        event_manager = interaction.client.get_event_manager(interaction.guild_id)
        availability_manager = interaction.client.get_availability_manager(interaction.guild_id)

        events = [e for e in event_manager.get_all_events() if e.active]

        if not events:
            return await interaction.response.send_message(
                "No events registered.", ephemeral=True
            )

        with_signups = []
        without_signups = []

        for event in events:
            if availability_manager.has_any_signups(event.id):
                count = availability_manager.count_signups(event.id)
                with_signups.append(
                    f"**{event.name}** - ID `{event.id}` - {count} signup{'s' if count != 1 else ''}"
                )
            else:
                without_signups.append(
                    f"**{event.name}** - ID `{event.id}`"
                )

        embeds = []

        if with_signups:
            embeds.append(discord.Embed(
                title="Events WITH people signed up",
                description="\n".join(with_signups)[:4000],
                color=discord.Color.green()
            ))

        if without_signups:
            embeds.append(discord.Embed(
                title="Events with NO ONE signed up",
                description="\n".join(without_signups)[:4000],
                color=discord.Color.red()
            ))

        await interaction.response.send_message(embeds=embeds[:10], ephemeral=True)


class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(ViewEventsButton())
        self.add_item(SignupStatusButton())


# ==========================================================
# Create event - modal
# ==========================================================
class CreateEventModal(discord.ui.Modal, title="Create New Event"):
    event_id = discord.ui.TextInput(label="Event ID (no spaces)", placeholder="bear1", max_length=50)
    day = discord.ui.TextInput(label="Day (0=Mon...6=Sun) or 'variable'", placeholder="0", max_length=10)
    time = discord.ui.TextInput(label="Time HH:MM (UTC)", placeholder="20:00", max_length=5)
    name = discord.ui.TextInput(label="Event Name", placeholder="Bear Hunt", max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        event_manager = interaction.client.get_event_manager(interaction.guild_id)

        eid = self.event_id.value.strip()
        day_raw = self.day.value.strip().lower()
        time_val = self.time.value.strip()
        name_val = self.name.value.strip()

        if event_manager.event_exists(eid):
            return await interaction.response.send_message(
                f"An event with id `{eid}` already exists.", ephemeral=True
            )

        if day_raw in ("variable", "var", "-", "none"):
            weekday_value = None
        else:
            try:
                weekday_value = int(day_raw)
                if not 0 <= weekday_value <= 6:
                    raise ValueError
            except ValueError:
                return await interaction.response.send_message(
                    "Day must be a number 0-6, or the word 'variable'.", ephemeral=True
                )

        try:
            parse_time_utc(time_val)
        except ValueError as e:
            return await interaction.response.send_message(str(e), ephemeral=True)

        event = Event(
            id=eid, name=name_val, description="Created from management dashboard",
            weekday=weekday_value, time=time_val,
        )
        event_manager.add_event(event)

        await interaction.response.send_message(
            f"Event **{name_val}** created (`{eid}`).", ephemeral=True
        )


class CreateEventButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create event", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreateEventModal())


# ==========================================================
# Enable / disable event - select menu
# ==========================================================
class ToggleEventSelect(discord.ui.Select):
    def __init__(self, guild_id: int, bot):
        event_manager = bot.get_event_manager(guild_id)
        events = event_manager.get_all_events()[:25]

        options = [
            discord.SelectOption(
                label=event.name[:100],
                value=event.id,
                description=(f"{'Active' if event.active else 'Inactive'} - tap to toggle")[:100],
            )
            for event in events
        ]

        super().__init__(placeholder="Choose an event to enable/disable...", options=options)

    async def callback(self, interaction: discord.Interaction):
        event_manager = interaction.client.get_event_manager(interaction.guild_id)
        event = event_manager.get_event(self.values[0])

        if event is None:
            return await interaction.response.send_message("Event not found.", ephemeral=True)

        event.active = not event.active
        event_manager.save()

        status = "enabled" if event.active else "disabled"
        await interaction.response.send_message(f"**{event.name}** is now {status}.", ephemeral=True)


class ToggleEventView(discord.ui.View):
    def __init__(self, guild_id: int, bot):
        super().__init__(timeout=180)
        self.add_item(ToggleEventSelect(guild_id, bot))


class ToggleEventButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Enable/disable event", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        event_manager = interaction.client.get_event_manager(interaction.guild_id)

        if not event_manager.get_all_events():
            return await interaction.response.send_message("No events registered.", ephemeral=True)

        await interaction.response.send_message(
            "Pick an event:",
            view=ToggleEventView(interaction.guild_id, interaction.client),
            ephemeral=True
        )


# ==========================================================
# Set SvS Battle date - modal
# ==========================================================
class SetSvsDateModal(discord.ui.Modal, title="Set SvS Battle Date"):
    date_input = discord.ui.TextInput(
        label="Date (DD/MM/YYYY) - must be a Saturday",
        placeholder="11/07/2026",
        max_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction):
        parts = self.date_input.value.strip().split("/")

        if len(parts) != 3:
            return await interaction.response.send_message(
                "Use the DD/MM/YYYY format.", ephemeral=True
            )

        try:
            d, m, y = map(int, parts)
            anchor = date(y, m, d)
        except ValueError:
            return await interaction.response.send_message("Invalid date.", ephemeral=True)

        if anchor.weekday() != 5:
            return await interaction.response.send_message(
                f"That date falls on a {DAYS[anchor.weekday()]}, but SvS Battle is always "
                "on a Saturday. Please check the date.",
                ephemeral=True
            )

        cycle_manager.set_svs_battle_date(interaction.guild_id, anchor)

        await interaction.response.send_message(
            f"SvS Battle date set to **{DAYS[anchor.weekday()]} {anchor.strftime('%d/%m/%Y')}**.",
            ephemeral=True
        )


class SetSvsDateButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Set SvS date", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetSvsDateModal())


# ==========================================================
# View calculated monthly cycle
# ==========================================================
class ViewCycleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="View monthly cycle", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        anchor = cycle_manager.get_svs_battle_date(interaction.guild_id)

        if anchor is None:
            return await interaction.response.send_message(
                "The SvS Battle date isn't set yet. Use the 'Set SvS date' button first.",
                ephemeral=True
            )

        cycle_data = cycle_manager.compute_cycle(anchor)

        embed = discord.Embed(
            title="Monthly Cycle",
            description=f"Based on SvS Battle: **{DAYS[anchor.weekday()]} {anchor.strftime('%d/%m/%Y')}**",
            color=discord.Color.gold()
        )

        for name, dates in cycle_data.items():
            value = ", ".join(f"{DAYS[d.weekday()]} {d.strftime('%d/%m')}" for d in dates)
            embed.add_field(name=name, value=value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# Load reference events
# ==========================================================
class SeedEventsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Load reference events", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        event_manager = interaction.client.get_event_manager(interaction.guild_id)
        created, already_existed = load_seed_events(event_manager)

        msg = f"{len(created)} new events created."
        if already_existed:
            msg += f"\n{len(already_existed)} already existed and were left untouched."

        await interaction.response.send_message(msg, ephemeral=True)


# ==========================================================
# Set R4/R5 role names for this server - modal
# ==========================================================
class SetRolesModal(discord.ui.Modal, title="Set R4/R5 Role Names"):
    r4_name = discord.ui.TextInput(label="R4 role name (exact, case-sensitive)", placeholder="R4", max_length=100)
    r5_name = discord.ui.TextInput(label="R5 role name (exact, case-sensitive)", placeholder="R5", max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        r4 = self.r4_name.value.strip()
        r5 = self.r5_name.value.strip()

        guild_config.set_role_r4(interaction.guild_id, r4)
        guild_config.set_role_r5(interaction.guild_id, r5)

        await interaction.response.send_message(
            f"Roles set for this server: R4 = `{r4}`, R5 = `{r5}`.\n"
            "Make sure these match the role names exactly as they appear in this server.",
            ephemeral=True
        )


class SetRolesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Set R4/R5 role names", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetRolesModal())


# ==========================================================
# Configure channels for this server - channel selects
# ==========================================================
class AnnouncementChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Choose the announcements channel...",
            channel_types=[discord.ChannelType.text],
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        guild_config.set_announcement_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            f"Announcements channel set to {channel.mention} for this server.",
            ephemeral=True
        )


class CalendarChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Choose the calendar board channel...",
            channel_types=[discord.ChannelType.text],
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        guild_config.set_calendar_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            f"Calendar board channel set to {channel.mention} for this server.",
            ephemeral=True
        )


class ChannelConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(AnnouncementChannelSelect())
        self.add_item(CalendarChannelSelect())


class SetChannelsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Set channels", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Pick a channel from each dropdown:", view=ChannelConfigView(), ephemeral=True
        )


# ==========================================================
# Management dashboard (admins / R4 / R5 of THIS server only)
# ==========================================================
class ManagementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(ViewEventsButton())
        self.add_item(CreateEventButton())
        self.add_item(ToggleEventButton())
        self.add_item(SetSvsDateButton())
        self.add_item(ViewCycleButton())
        self.add_item(SeedEventsButton())
        self.add_item(SetRolesButton())
        self.add_item(SetChannelsButton())


class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # /panel - for everyone
    # -------------------------
    @app_commands.command(
        name="panel",
        description="Open the bot's panel"
    )
    async def panel(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="Panel - Whiteout Duty Manager",
            description="Use the buttons below.",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed, view=DashboardView(), ephemeral=True)

    # -------------------------
    # /management - admins / R4 / R5 of this server only
    # -------------------------
    @app_commands.command(
        name="management",
        description="Management dashboard (admins and R4/R5 only)"
    )
    async def management(self, interaction: discord.Interaction):

        if not has_management_access(interaction.guild_id, interaction.user):
            return await interaction.response.send_message(
                "You don't have permission to use this command. "
                "It's restricted to admins and R4/R5.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="Management Dashboard - Whiteout Duty Manager",
            description="Admin tools. Use the buttons below.",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed, view=ManagementView(), ephemeral=True)


async def setup(bot):
    await bot.add_cog(DashboardCog(bot))
