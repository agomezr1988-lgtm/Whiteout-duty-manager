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


def day_label(event) -> str:
    if event.weekday is None:
        return "Fecha variable"
    return DAYS[event.weekday]


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

            label = f"{event.name} ({day_label(event)} {event.time} UTC)"

            if current.lower() in label.lower() or current.lower() in event.id.lower():
                choices.append(
                    app_commands.Choice(name=label[:100], value=event.id)
                )

        return choices[:25]

    # ==================================================
    # AUTOCOMPLETADO DE TAREA (depende del evento ya elegido)
    # ==================================================
    async def tarea_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        evento_id = interaction.namespace.evento

        if not evento_id:
            return []

        event = self.bot.event_manager.get_event(evento_id)

        if event is None or not event.tasks:
            return []

        return [
            app_commands.Choice(name=t[:100], value=t)
            for t in event.tasks
            if current.lower() in t.lower()
        ][:25]

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
            "DD/MM o DD/MM/AAAA para una fecha concreta. Obligatorio en "
            "eventos de fecha variable; opcional en el resto (vacío = todas las semanas)."
        ),
        tarea="Opcional: la tarea concreta a la que te apuntas dentro del evento",
    )
    @app_commands.autocomplete(evento=event_autocomplete, tarea=tarea_autocomplete)
    async def disponible(
        self,
        interaction: discord.Interaction,
        evento: str,
        fecha: str = None,
        tarea: str = None,
    ):

        event = self.bot.event_manager.get_event(evento)

        if event is None:
            return await interaction.response.send_message(
                "❌ Evento no encontrado. Selecciónalo de la lista que te sugiere Discord.",
                ephemeral=True
            )

        # Los eventos de fecha variable no tienen recurrencia semanal:
        # hace falta indicar una fecha sí o sí.
        if event.weekday is None and not fecha:
            return await interaction.response.send_message(
                f"❌ **{event.name}** es un evento de fecha variable. "
                "Indica una fecha con el parámetro `fecha` (DD/MM o DD/MM/AAAA).",
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

        if tarea and event.tasks and tarea not in event.tasks:
            return await interaction.response.send_message(
                f"❌ Esa tarea no existe en **{event.name}**. "
                f"Elígela de la lista sugerida.",
                ephemeral=True
            )

        rank = self._get_rank(interaction.user)

        self.availability_manager.set_available(
            event_id=event.id,
            user_id=str(interaction.user.id),
            user_name=interaction.user.display_name,
            rank=rank,
            date=date_iso,
            task=tarea,
        )

        cuando = f"el {date_iso}" if date_iso else f"todos los {day_label(event)}"
        tarea_txt = f" — tarea: **{tarea}**" if tarea else ""

        await interaction.response.send_message(
            f"✅ Apuntado a **{event.name}** ({cuando}){tarea_txt}.",
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
        fecha="Indícala solo si te apuntaste a una fecha concreta (DD/MM o DD/MM/AAAA)",
        tarea="Indícala solo si te apuntaste a una tarea concreta",
    )
    @app_commands.autocomplete(evento=event_autocomplete, tarea=tarea_autocomplete)
    async def no_disponible(
        self,
        interaction: discord.Interaction,
        evento: str,
        fecha: str = None,
        tarea: str = None,
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
            task=tarea,
        )

        if removed:
            await interaction.response.send_message(
                f"🗑️ Te has quitado de **{event.name}**.",
                ephemeral=True
            )
            await self.refresh_board()
        else:
            await interaction.response.send_message(
                "⚠️ No estabas apuntado ahí (revisa si pusiste fecha/tarea igual que al apuntarte).",
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

        # --- Eventos con día fijo, agrupados por día de la semana ---
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
                lines.append(self._format_event_signups(event, fecha_dia))

            embed.add_field(
                name=f"{DAYS[weekday]} {week_dates[weekday].strftime('%d/%m')}",
                value="\n\n".join(lines),
                inline=False
            )

        # --- Eventos de fecha variable con apuntados esta semana ---
        variable_events = [e for e in events if e.weekday is None and e.active]
        variable_lines = []

        for event in variable_events:
            signups = self.availability_manager.get_for_event(event.id)
            entries_with_date = [a for a in signups if a.date]

            if not entries_with_date:
                continue

            por_fecha = {}
            for a in entries_with_date:
                por_fecha.setdefault(a.date, []).append(a)

            for fecha, entries in sorted(por_fecha.items()):
                nombres = ", ".join(
                    a.user_name + (f" ({a.rank})" if a.rank else "") +
                    (f" [{a.task}]" if a.task else "")
                    for a in entries
                )
                variable_lines.append(f"**{event.name}** — {fecha}\n👥 {nombres}")

        if variable_lines:
            embed.add_field(
                name="📌 Eventos de fecha variable",
                value="\n\n".join(variable_lines),
                inline=False
            )

        if not embed.fields:
            embed.description += "\n\n📭 No hay eventos activos configurados."

        return embed

    def _format_event_signups(self, event, fecha_dia: str) -> str:
        signups = self.availability_manager.get_for_event(event.id, date=fecha_dia)

        if not event.tasks:
            if signups:
                nombres = ", ".join(
                    a.user_name + (f" ({a.rank})" if a.rank else "")
                    for a in signups
                )
            else:
                nombres = "Sin apuntados"
            return f"**{event.name}** ({event.time} UTC)\n👥 {nombres}"

        # Evento con tareas: agrupar por tarea
        lines = [f"**{event.name}** ({event.time} UTC)"]

        sin_tarea = [a for a in signups if not a.task]
        if sin_tarea:
            nombres = ", ".join(a.user_name for a in sin_tarea)
            lines.append(f"👥 General: {nombres}")

        for tarea in event.tasks:
            asignados = [a for a in signups if a.task == tarea]
            nombres = ", ".join(a.user_name for a in asignados) if asignados else "—"
            lines.append(f"▫️ {tarea}: {nombres}")

        return "\n".join(lines)

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
    # UTILIDAD: rango R4/R5 del usuario
    # ==================================================
    def _get_rank(self, member) -> str:
        role_names = [r.name for r in getattr(member, "roles", [])]

        if config.ROLE_R5_NAME in role_names:
            return "R5"

        if config.ROLE_R4_NAME in role_names:
            return "R4"

        return ""


async def setup(bot):
    await bot.add_cog(AvailabilityCog(bot))
