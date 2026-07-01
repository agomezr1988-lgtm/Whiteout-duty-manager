import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.availability_manager import AvailabilityManager
from utils.time_utils import get_week_dates, parse_date_ddmmyyyy

logger = logging.getLogger(__name__)

DAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


class AvailabilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.availability_manager = AvailabilityManager()
        self.board_message_id: int | None = None

    # ==================================================
    # AUTOCOMPLETADO DE EVENTOS
    # ==================================================
    async def event_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        events = self.bot.event_manager.get_all_events()
        choices = []

        for event in events:

            if not event.active:
                continue

            label = f"{event.name} ({DAYS[event.weekday]} {event.time} UTC)"

            if current.lower() in label.lower() or current.lower() in event.id.lower():
                choices.append(
                    app_commands.Choice(name=label[:100], value=event.id)
                )

        return choices[:25]

    # ==================================================
    # /disponible
    # ==================================================
    @app_commands.command(
        name="disponible",
        description="Marca tu disponibilidad para un evento"
    )
    @app_commands.describe(
        evento="Elige el evento de la lista",
        fecha=(
            "Opcional: DD/MM o DD/MM/AAAA para una fecha concreta. "
            "Si lo dejas vacío, vale todas las semanas."
        )
    )
    @app_commands.autocomplete(evento=event_autocomplete)
    async def disponible(
        self,
        interaction: discord.Interaction,
        evento: str,
        fecha: str = None,
    ):

        event = self.bot.event_manager.get_event(evento)

        if event is None:
            return await interaction.response.send_message(
                "❌ Evento no encontrado. Selecciónalo de la lista que te sugiere Discord.",
                ephemeral=True
            )

        date_iso = None

        if fecha:
            try:
                date_iso = parse_date_ddmmyyyy(fecha)
            except ValueError as e:
                return await interaction.response.send_message(
                    f"❌ {e}", ephemeral=True
                )

        role = self._get_role(interaction.user)

        self.availability_manager.set_available(
            event_id=event.id,
            user_id=str(interaction.user.id),
            user_name=interaction.user.display_name,
            role=role,
            date=date_iso,
        )

        cuando = f"el {date_iso}" if date_iso else f"todos los {DAYS[event.weekday]}"

        await interaction.response.send_message(
            f"✅ Apuntado a **{event.name}** ({cuando}).",
            ephemeral=True
        )

        await self.refresh_board()

    # ==================================================
    # /no_disponible
    # ==================================================
    @app_commands.command(
        name="no_disponible",
        description="Quita tu disponibilidad para un evento"
    )
    @app_commands.describe(
        evento="Elige el evento de la lista",
        fecha="Indícala solo si te apuntaste a una fecha concreta (DD/MM o DD/MM/AAAA)"
    )
    @app_commands.autocomplete(evento=event_autocomplete)
    async def no_disponible(
        self,
        interaction: discord.Interaction,
        evento: str,
        fecha: str = None,
    ):

        event = self.bot.event_manager.get_event(evento)

        if event is None:
            return await interaction.response.send_message(
                "❌ Evento no encontrado.", ephemeral=True
            )

        date_iso = None

        if fecha:
            try:
                date_iso = parse_date_ddmmyyyy(fecha)
            except ValueError as e:
                return await interaction.response.send_message(
                    f"❌ {e}", ephemeral=True
                )

        removed = self.availability_manager.remove_available(
            event_id=event.id,
            user_id=str(interaction.user.id),
            date=date_iso,
        )

        if removed:
            await interaction.response.send_message(
                f"🗑️ Te has quitado de **{event.name}**.",
                ephemeral=True
            )
            await self.refresh_board()
        else:
            await interaction.response.send_message(
                "⚠️ No estabas apuntado ahí.",
                ephemeral=True
            )

    # ==================================================
    # /calendario
    # ==================================================
    @app_commands.command(
        name="calendario",
        description="Muestra el calendario semanal de disponibilidad"
    )
    async def calendario(self, interaction: discord.Interaction):
        embed = self.build_calendar_embed()
        await interaction.response.send_message(embed=embed)

    # ==================================================
    # CONSTRUCCIÓN DEL EMBED DE CALENDARIO
    # ==================================================
    def build_calendar_embed(self) -> discord.Embed:

        week_dates = get_week_dates()

        embed = discord.Embed(
            title="🗓️ Calendario semanal de disponibilidad",
            color=discord.Color.blurple(),
            description=(
                f"Semana del {week_dates[0].strftime('%d/%m')} "
                f"al {week_dates[6].strftime('%d/%m')} (horas en UTC)"
            )
        )

        events = self.bot.event_manager.get_all_events()

        for weekday in range(7):

            day_events = [
                e for e in events
                if e.weekday == weekday and e.active
            ]

            if not day_events:
                continue

            fecha_dia = week_dates[weekday].isoformat()
            lines = []

            for event in day_events:

                signups = self.availability_manager.get_for_event(
                    event.id, date=fecha_dia
                )

                if signups:
                    nombres = ", ".join(
                        a.user_name + (f" ({a.role})" if a.role else "")
                        for a in signups
                    )
                else:
                    nombres = "Sin apuntados"

                lines.append(
                    f"**{event.name}** ({event.time} UTC)\n👥 {nombres}"
                )

            embed.add_field(
                name=f"{DAYS[weekday]} {week_dates[weekday].strftime('%d/%m')}",
                value="\n\n".join(lines),
                inline=False
            )

        if not embed.fields:
            embed.description += "\n\n📭 No hay eventos activos configurados."

        return embed

    # ==================================================
    # TABLÓN QUE SE AUTOACTUALIZA
    # ==================================================
    async def refresh_board(self):

        channel_id = getattr(config, "CALENDAR_CHANNEL_ID", 0)

        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)

        if channel is None:
            logger.warning("No se encontró el canal del tablón de calendario.")
            return

        embed = self.build_calendar_embed()

        if self.board_message_id:
            try:
                message = await channel.fetch_message(self.board_message_id)
                await message.edit(embed=embed)
                return
            except discord.NotFound:
                self.board_message_id = None
            except discord.Forbidden:
                logger.warning("Sin permisos para editar el mensaje del tablón.")
                return

        message = await channel.send(embed=embed)
        self.board_message_id = message.id

    # ==================================================
    # UTILIDAD: rol R4/R5 del usuario
    # ==================================================
    def _get_role(self, member) -> str:
        role_names = [r.name for r in getattr(member, "roles", [])]

        if config.ROLE_R5_NAME in role_names:
            return "R5"

        if config.ROLE_R4_NAME in role_names:
            return "R4"

        return ""


async def setup(bot):
    await bot.add_cog(AvailabilityCog(bot))
