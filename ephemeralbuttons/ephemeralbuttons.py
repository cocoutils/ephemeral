import discord
import json
from redbot.core import commands, Config
from discord.ui import Button, View

class EphemeralButtons(commands.Cog):
    """Send custom ephemeral buttons"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(buttons={})

    @commands.command()
    async def addbutton(
        self, ctx, channel_id: int, message_id: int, label: str, *, options: str = ""
    ):
        """Attach a button to an existing message with a custom emoji and ephemeral response."""
        
        # Parse flags
        ephemeral = "--ephemeral" in options
        emoji = None

        # Extract emoji (server emoji or Unicode)
        if "--emoji" in options:
            try:
                emoji_str = options.split("--emoji")[1].split("--")[0].strip()
                emoji = discord.PartialEmoji.from_str(emoji_str)
            except:
                emoji = emoji_str  # Unicode fallback
        
        # Determine response type and content
        content, resp_type = None, None
        if "--text" in options:
            content = options.split("--text")[1].split("--")[0].strip()
            resp_type = "text"
        elif "--embedjson" in options:
            try:
                raw_json = options.split("--embedjson")[1].split("--")[0].strip()
                content = json.loads(raw_json)
                resp_type = "embed"
            except json.JSONDecodeError as e:
                return await ctx.send(f"Invalid embed JSON: {e}")
        else:
            return await ctx.send("Include either `--text` or `--embedjson`.")

        # Fetch the message
        try:
            channel = ctx.guild.get_channel(channel_id)
            msg = await channel.fetch_message(message_id)
        except Exception as e:
            return await ctx.send(f"Could not fetch message: {e}")

        # Store config
        custom_id = f"btn_{label}_{ctx.message.id}"
        buttons_data = await self.config.buttons()
        buttons_data.setdefault(str(message_id), {})[custom_id] = {
            "label": label,
            "emoji": str(emoji) if emoji else None,
            "response_type": resp_type,
            "content": content,
            "ephemeral": ephemeral,
        }
        await self.config.buttons.set(buttons_data)

        # Build view
        view = View()
        for cid, info in buttons_data[str(message_id)].items():
            e = discord.PartialEmoji.from_str(info["emoji"]) if info["emoji"] else None
            view.add_item(Button(label=info["label"], custom_id=cid, emoji=e))

        # Update the message
        try:
            await msg.edit(view=view)
        except discord.HTTPException:
            return await ctx.send("Failed to edit message with button.")

        await ctx.send("✅ Button added!")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions."""
        if not interaction.data["custom_id"].startswith("btn_"):
            return

        # Retrieve button config
        buttons_data = await self.config.buttons()
        message_id = str(interaction.message.id)
        button_config = buttons_data.get(message_id, {}).get(interaction.data["custom_id"])

        if not button_config:
            return await interaction.response.send_message("❌ Button config not found.", ephemeral=True)

        # Respond with either text or embed
        if button_config["response_type"] == "text":
            await interaction.response.send_message(button_config["content"], ephemeral=button_config["ephemeral"])
        elif button_config["response_type"] == "embed":
            embed = discord.Embed.from_dict(button_config["content"])
            await interaction.response.send_message(embed=embed, ephemeral=button_config["ephemeral"])


