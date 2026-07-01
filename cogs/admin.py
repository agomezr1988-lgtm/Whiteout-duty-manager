import discord
from discord.ext import commands

from cogs.events import day_label


DAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
]


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------
    # Comprobación de permisos
    # --------------------------------------------------

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.manage_guild

    # --------------------------------------------------
    # Asignar responsable
    # --------------------------------------------------

    @commands.command(name="assign_role")
    async def assign_role(self, ctx, event_id: str, *, role: str):

        event = self.bot.event_manager.get_event(event_id)

        if event is None:
            return await ctx.send("❌ Evento no encontrado.")

        if role in event.assigned_roles:
            return await ctx.send("⚠️ Ese rol ya está asignado.")

        event.assigned_roles.append(role)

        self.bot.event_manager.save()

        await ctx.send(
            f"✅ Rol **{role}** asignado correctamente a **{event.name}**."
        )

    # --------------------------------------------------
    # Quitar responsable
    # --------------------------------------------------

    @commands.command(name="unassign_role")
    async def unassign_role(self, ctx, event_id: str, *, role: str):

        event = self.bot.event_manager.get_event(event_id)

        if event is None:
            return await ctx.send("❌ Evento no encontrado.")

        if role not in event.assigned_roles:
            return await ctx.send("⚠️ Ese rol no estaba asignado.")

        event.assigned_roles.remove(role)

        self.bot.event_manager.save()

        await ctx.send(
            f"🗑️ Rol **{role}** eliminado de **{event.name}**."
        )

    # --------------------------------------------------
    # Activar / Desactivar
    # --------------------------------------------------

    @commands.command(name="toggle_event")
    async def toggle_event(self, ctx, event_id: str):

        event = self.bot.event_manager.get_event(event_id)

        if event is None:
            return await ctx.send("❌ Evento no encontrado.")

        event.active = not event.active

        self.bot.event_manager.save()

        estado = "🟢 Activo" if event.active else "🔴 Inactivo"

        await ctx.send(
            f"Estado actualizado.\n\n**{event.name}** → {estado}"
        )

    # --------------------------------------------------
    # Ajustar hora
    # --------------------------------------------------

    @commands.command(name="set_time")
    async def set_time(self, ctx, event_id: str, time: str):
        from utils.time_utils import parse_time_utc

        event = self.bot.event_manager.get_event(event_id)

        if event is None:
            return await ctx.send("❌ Evento no encontrado.")

        try:
            parse_time_utc(time)
        except ValueError as e:
            return await ctx.send(str(e))

        event.time = time
        self.bot.event_manager.save()

        await ctx.send(f"✅ Hora de **{event.name}** actualizada a {time} UTC.")

    # --------------------------------------------------
    # Cargar eventos desde data/seed_events.py
    # --------------------------------------------------

    @commands.command(name="seed_events")
    async def seed_events(self, ctx):
        """
        Carga los eventos definidos en data/seed_events.py.
        Solo AÑADE los que todavía no existan (por id); nunca
        sobreescribe uno que ya esté creado.
        """

        try:
            from data.seed_events import SEED_EVENTS
        except ImportError:
            return await ctx.send(
                "❌ No se encontró `data/seed_events.py`."
            )

        from utils.event_model import Event

        creados = []
        ya_existian = []

        for data in SEED_EVENTS:
            if self.bot.event_manager.event_exists(data["id"]):
                ya_existian.append(data["id"])
                continue

            event = Event(
                id=data["id"],
                name=data["name"],
                description=data.get("description", ""),
                weekday=data.get("weekday"),
                time=data.get("time", "00:00"),
                tasks=data.get("tasks", []),
                notes=data.get("notes", ""),
            )

            self.bot.event_manager.add_event(event)
            creados.append(data["id"])

        resumen = f"✅ {len(creados)} eventos nuevos creados."

        if ya_existian:
            resumen += f"\n⏭️ {len(ya_existian)} ya existían y no se han tocado."

        await ctx.send(resumen)

    # --------------------------------------------------
    # Definir tareas apuntables del evento
    # --------------------------------------------------

    @commands.command(name="set_tasks")
    async def set_tasks(self, ctx, event_id: str, *, tasks: str):
        """
        Define las tareas internas de un evento, separadas por comas.
        Ejemplo: !set_tasks foundry Messages & teams, Battle coordination
        Para quitar todas las tareas: !set_tasks foundry -
        """

        event = self.bot.event_manager.get_event(event_id)

        if event is None:
            return await ctx.send("❌ Evento no encontrado.")

        if tasks.strip() == "-":
            event.tasks = []
        else:
            event.tasks = [t.strip() for t in tasks.split(",") if t.strip()]

        self.bot.event_manager.save()

        if event.tasks:
            lista = "\n".join(f"• {t}" for t in event.tasks)
            await ctx.send(
                f"✅ Tareas de **{event.name}** actualizadas:\n{lista}"
            )
        else:
            await ctx.send(
                f"✅ **{event.name}** ya no tiene tareas apuntables definidas."
            )

    # --------------------------------------------------
    # Información
    # --------------------------------------------------

    @commands.command(name="event_info")
    async def event_info(self, ctx, event_id: str):

        event = self.bot.event_manager.get_event(event_id)

        if event is None:
            return await ctx.send("❌ Evento no encontrado.")

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
            name="Día",
            value=day_label(event),
            inline=True
        )

        embed.add_field(
            name="Hora",
            value=f"{event.time} UTC",
            inline=True
        )

        embed.add_field(
            name="Estado",
            value="🟢 Activo" if event.active else "🔴 Inactivo",
            inline=True
        )

        embed.add_field(
            name="Duración",
            value=str(event.duration) if event.duration else "No definida",
            inline=True
        )

        embed.add_field(
            name="Recordatorios",
            value=", ".join(f"{m} min" for m in event.reminders),
            inline=False
        )

        embed.add_field(
            name="Tareas apuntables",
            value=", ".join(event.tasks) if event.tasks else "Este evento no tiene tareas definidas",
            inline=False
        )

        embed.add_field(
            name="Responsables",
            value=", ".join(event.assigned_roles) if event.assigned_roles else "Sin asignar",
            inline=False
        )

        if event.notes:
            embed.add_field(
                name="Notas",
                value=event.notes,
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
