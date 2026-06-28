const {
  Client,
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

client.once("ready", () => {
  console.log(`Bot conectado como ${client.user.tag}`);
});

client.on("messageCreate", async (message) => {
  if (message.author.bot) return;

  if (message.content === "!event") {

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
    const value = interaction.values[0];

    await interaction.reply(`✅ Has seleccionado el evento: **${value}**`);
  }
});

client.login(process.env.TOKEN);
