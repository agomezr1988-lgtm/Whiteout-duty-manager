const weeklyCalendar = {
  monday: [],
  tuesday: [],
  wednesday: [],
  thursday: [],
  friday: [],
  saturday: [],
  sunday: []
};
const {
  Client,
  const eventRegistrations = {};
  GatewayIntentBits,
  ActionRowBuilder,
  StringSelectMenuBuilder
} = require("discord.js");

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});
client.on("messageCreate", async (message) => {
  if (message.author.bot) return;

  // COMANDO EVENTO
  if (message.content === "!event") {
    const menu = require("./tu_menu_o_lo_que_tengas"); // ignorar si ya lo tienes
  }

  // CALENDARIO - AÑADIR
  if (message.content.startsWith("!calendar add")) {

    const args = message.content.split(" ");
    const day = args[2];
    const event = args.slice(3).join(" ");

    if (!weeklyCalendar[day]) {
      return message.reply("Día inválido. Usa monday, tuesday, etc.");
    }

    weeklyCalendar[day].push(event);

    return message.reply(`📅 Evento añadido a **${day}**: ${event}`);
  }

  // CALENDARIO - VER
  if (message.content === "!calendar") {

    let text = "📅 **Calendario Semanal de la Alianza**\n\n";

    for (const day in weeklyCalendar) {
      text += `**${day.toUpperCase()}**\n`;

      if (weeklyCalendar[day].length === 0) {
        text += "- Sin eventos\n\n";
      } else {
        weeklyCalendar[day].forEach(e => {
          text += `- ${e}\n`;
        });
        text += "\n";
      }
    }

    return message.reply(text);
  }
});

client.once("ready", () => {
  console.log(`Bot conectado como ${client.user.tag}`);
});

if (message.content.startsWith("!list ")) {

  const event = message.content.split(" ")[1];

  const list = eventRegistrations[event];

  if (!list || list.length === 0) {
    return message.reply("No hay jugadores registrados en este evento.");
  }

  const mentions = list.map(id => `<@${id}>`).join("\n");

  message.reply(`📋 Jugadores en **${event}**:\n\n${mentions}`);
}

    const menu = new StringSelectMenuBuilder()
      .setCustomId("event_menu")
      .setPlaceholder("Selecciona un evento de Whiteout Survival")
      .addOptions([
        { label: "SvS Preparation Phase", value: "svs_preparation_phase" },
        { label: "SvS Battle", value: "svs_battle" },
        { label: "Sunfire Castle (Normal)", value: "sunfire_castle_normal" },
        { label: "Sunfire Castle (SvS)", value: "sunfire_castle_svs" },
        { label: "King of Icefield (KoI)", value: "king_of_icefield_koi" },
        { label: "Alliance Showdown", value: "alliance_showdown" },
        { label: "Alliance Mobilization", value: "alliance_mobilization" },
        { label: "Foundry Battle", value: "foundry_battle" },
        { label: "Frostfire Mine", value: "frostfire_mine" },
        { label: "Canyon Clash", value: "canyon_clash" },
        { label: "Crazy Joe", value: "crazy_joe" },
        { label: "Fortress Battle", value: "fortress_battle" },
        { label: "Stronghold Battle", value: "stronghold_battle" },
        { label: "Bear Trap", value: "bear_trap" },
        { label: "Daily Messages", value: "daily_messages" },
        { label: "Alliance Gifts", value: "alliance_gifts" },
        { label: "Alliance Tech Donations", value: "alliance_tech_donations" },
        { label: "Alliance Help", value: "alliance_help" },
        { label: "Rally Organization", value: "rally_organization" },
        { label: "Event Registration", value: "event_registration" },
        { label: "Battle Sign-ups", value: "battle_signups" },
        { label: "Reward Distribution", value: "reward_distribution" },
        { label: "Alliance Championship", value: "alliance_championship" }
      ]);

    const row = new ActionRowBuilder().addComponents(menu);

    await message.reply({
      content: "🎯 Selecciona un evento:",
      components: [row]
    });
  }
});

client.on("interactionCreate", async (interaction) => {

  if (!interaction.isStringSelectMenu()) return;

  if (interaction.customId === "event_menu") {

    const event = interaction.values[0];

    // Crear array si no existe
    if (!eventRegistrations[event]) {
      eventRegistrations[event] = [];
    }

    // Si usuario no está registrado → lo añadimos
    if (!eventRegistrations[event].includes(interaction.user.id)) {
      eventRegistrations[event].push(interaction.user.id);
    }

    const count = eventRegistrations[event].length;

    await interaction.reply({
      content: `✅ Te has registrado en **${event}**\n👥 Total inscritos: **${count}**`,
      ephemeral: true
    });
  }
});

  if (interaction.customId === "event_menu") {
    const value = interaction.values[0];

    const eventInfo = {
  svs_preparation_phase: "📊 Preparación para SvS: organización de rallys y asignación de roles.",
  svs_battle: "⚔️ Batalla SvS: guerra entre reinos, máxima coordinación requerida.",
  sunfire_castle_normal: "🏰 Sunfire Castle (Normal): evento de control del castillo.",
  sunfire_castle_svs: "🔥 Sunfire Castle (SvS): versión de SvS con recompensa especial.",
  king_of_icefield_koi: "❄️ King of Icefield: control del mapa de hielo.",
  alliance_showdown: "⚔️ Alliance Showdown: enfrentamiento entre alianzas.",
  alliance_mobilization: "📢 Movilización de alianza: preparación de tropas.",
  foundry_battle: "⚙️ Foundry Battle: combate por puntos de alianza.",
  frostfire_mine: "⛏️ Frostfire Mine: minería PvP por recursos.",
  canyon_clash: "🏹 Canyon Clash: combate táctico por equipos.",
  crazy_joe: "🤪 Crazy Joe: defensa contra oleadas de enemigos.",
  fortress_battle: "🏯 Fortress Battle: conquista de fortalezas.",
  stronghold_battle: "🛡️ Stronghold Battle: control de puntos estratégicos.",
  bear_trap: "🐻 Bear Trap: caza cooperativa de jefes.",
  daily_messages: "💬 Mensajes diarios de organización.",
  alliance_gifts: "🎁 Gestión de regalos de alianza.",
  alliance_tech_donations: "🔬 Donaciones de tecnología de alianza.",
  alliance_help: "🤝 Ayuda entre miembros de la alianza.",
  rally_organization: "📣 Organización de rallys.",
  event_registration: "📝 Registro de eventos.",
  battle_signups: "⚔️ Inscripción a batallas.",
  reward_distribution: "🏆 Distribución de recompensas.",
  alliance_championship: "👑 Campeonato de alianza."
};

await interaction.reply(eventInfo[value] || "Evento no definido.");
  }
});

client.login(process.env.TOKEN);
