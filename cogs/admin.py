import discord
from discord.ext import commands


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
            value=DAYS[event.weekday],
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
