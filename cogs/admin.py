import discord
from discord.ext import commands


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # ASIGNAR ROL A EVENTO
    # -------------------------
    @commands.command(name="assign_role")
    async def assign_role(self, ctx, event_id: str, role: str):
        """
        Asigna un rol (R4, R5, etc.) a un evento.
        Ejemplo:
        !assign_role guerra R4
        """

        event = self.bot.event_manager.get_event(event_id)

        if not event:
            return await ctx.send("❌ Evento no encontrado.")

        if role not in event.assigned_roles:
            event.assigned_roles.append(role)

        await ctx.send(f"✅ Rol **{role}** asignado a evento **{event.name}**")

    # -------------------------
    # QUITAR ROL DE EVENTO
    # -------------------------
    @commands.command(name="unassign_role")
    async def unassign_role(self, ctx, event_id: str, role: str):
        """
        Quita un rol de un evento.
        """

        event = self.bot.event_manager.get_event(event_id)

        if not event:
            return await ctx.send("❌ Evento no encontrado.")

        if role in event.assigned_roles:
            event.assigned_roles.remove(role)
            await ctx.send(f"🗑️ Rol **{role}** eliminado de **{event.name}**")
        else:
            await ctx.send("⚠️ Ese rol no estaba asignado.")

    # -------------------------
    # ACTIVAR / DESACTIVAR EVENTO
    # -------------------------
    @commands.command(name="toggle_event")
    async def toggle_event(self, ctx, event_id: str):
        """
        Activa o desactiva un evento.
        """

        event = self.bot.event_manager.get_event(event_id)

        if not event:
            return await ctx.send("❌ Evento no encontrado.")

        event.active = not event.active

        status = "🟢 activo" if event.active else "🔴 inactivo"

        await ctx.send(f"🔁 Evento **{event.name}** ahora está {status}")

    # -------------------------
    # VER DETALLE DE EVENTO
    # -------------------------
    @commands.command(name="event_info")
    async def event_info(self, ctx, event_id: str):
        """
        Muestra información detallada de un evento.
        """

        event = self.bot.event_manager.get_event(event_id)

        if not event:
            return await ctx.send("❌ Evento no encontrado.")

        embed = discord.Embed(
            title=f"📌 {event.name}",
            color=discord.Color.purple()
        )

        embed.add_field(name="ID", value=event.id, inline=True)
        embed.add_field(name="Día semana", value=str(event.weekday), inline=True)
        embed.add_field(name="Hora", value=event.time, inline=True)
        embed.add_field(name="Estado", value="Activo" if event.active else "Inactivo", inline=True)
        embed.add_field(
            name="Roles asignados",
            value=", ".join(event.assigned_roles) if event.assigned_roles else "Ninguno",
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
