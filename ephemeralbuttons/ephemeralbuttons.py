import discord
import json
from redbot.core import commands, Config
from redbotcore.utils.chat_formatting import box
from discord.ui import Button, View


class ephemeralbuttons(commands.Cog):
    """Send custom ephemeral buttons"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(buttons={})

    @commands.command()
    async def ephemeraltest(self, ctx):
        """Sends a test ephemeral button."""
        view = View()
        button = Button(label="Click Me", style=discord.ButtonStyle.primary)

        async def buttoncallback(interaction: discord.Interaction):
            await interaction.response.send_message("You clicked the button!", ephemeral=True)

        button.callback = buttoncallback
        view.add_item(button)

        await ctx.send("Here's your ephemeral button:", view=view)

    @commands.command()
    async def addbutton(
        self,
        ctx,
        channel_id: int,
        message_id: int,
        label: str,
        *,
        options: str = ""
    ):
        """Attach a button to an existing message. Supports --text or --embedjson and --ephemeral"""

        ephemeral = "--ephemeral" in options
        text_flag = "--text"
        embed_flag = "--embedjson"

        if text_flag in options:
            content = options.split(text_flag)[1].split("--")[0].strip()
            response_type = "text"
        elif embed_flag in options:
            try:
                raw = options.split(embed_flag)[1].split("--")[0].strip()
                embed_data = json.loads(raw)
                content = embed_data
                response_type = "embed"
            except Exception as e:
                return await ctx.send(f"Invalid JSON: {e}")
        else:
            return await ctx.send("You must use either --text or --embedjson")

        try:
            channel = ctx.guild.get_channel(channel_id)
            msg = await channel.fetch_message(message_id)
        except Exception as e:
            return await ctx.send(f"Couldn't fetch the message: {e}")

        custom_id = f"btn_{label}_{ctx.message.id}"

        buttons = await self.config.buttons()
        buttons[str(message_id)] = buttons.get(str(message_id), {})
        buttons[str(message_id)][custom_id] = {
            "label": label,
            "ephemeral": ephemeral,
            "response_type": response_type,
            "content": content
        }
        await self.config.buttons.set(buttons)

        view = View()
        view.add_item(Button(label=label, custom_id=custom_id))

        try:
            await msg.edit(view=view)
        except discord.HTTPException:
            return await ctx.send("Failed to edit message with button.")

        await ctx.send("✅ Button added!")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id")
        msg_id = str(interaction.message.id)
        buttons = await self.config.buttons()

        data = buttons.get(msg_id, {}).get(custom_id)
        if not data:
            return

        if data["response_type"] == "text":
            await interaction.response.send_message(data["content"], ephemeral=data["ephemeral"])
        elif data["response_type"] == "embed":
            try:
                embed = discord.Embed.from_dict(data["content"])
                await interaction.response.send_message(embed=embed, ephemeral=data["ephemeral"])
            except Exception as e:
                await interaction.response.send_message(f"Failed to send embed: {e}", ephemeral=True)

