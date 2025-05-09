import discord
from redbot.core import commands, Config
from redbot.core.commands import FlagConverter
from discord.ui import Button, View

class ButtonFlags(FlagConverter):
    label: str = None
    emoji: str = None
    style: str = "blurple"

    async def convert_emoji(self, argument: str):
        try:
            return discord.PartialEmoji.from_str(argument)
        except Exception:
            return argument  # fallback to unicode emoji or invalid

class EphemeralButtons(commands.Cog):
    """Send custom ephemeral buttons"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(buttons={})  # Store buttons globally

    @commands.command(name="createbutton")
    async def create_button(
        self,
        ctx: commands.Context,
        name: str,
        role: discord.Role,
        *,
        extras: ButtonFlags
    ):
        """Create a button with emoji support."""
        if " " in name:
            await ctx.send("Button names cannot contain spaces.")
            return

        label = extras.label or role.name
        style = getattr(discord.ButtonStyle, extras.style.lower(), discord.ButtonStyle.blurple)

        # Convert emoji safely
        emoji = None
        if extras.emoji:
            emoji = await extras.convert_emoji(extras.emoji)

        button = discord.ui.Button(
            label=label,
            style=style,
            emoji=emoji,
            custom_id=f"{name.lower()}-{role.id}"
        )

        view = discord.ui.View()
        view.add_item(button)

        await ctx.send("Here is how your button will look:", view=view)

    @commands.command()
    async def removebutton(self, ctx, channel_id: int, message_id: int, label: str):
        """Remove a button from an existing message."""
        try:
            buttons = await self.config.buttons()
            button_data = buttons.get(str(message_id), {}).get(f"btn_{label}_{ctx.message.id}")
            if not button_data:
                return await ctx.send(f"Button `{label}` not found on this message.")

            channel = ctx.guild.get_channel(channel_id)
            msg = await channel.fetch_message(message_id)
            if not msg:
                return await ctx.send("Message not found.")

            view = View()
            for item in view.children:
                if item.custom_id == f"btn_{label}_{ctx.message.id}":
                    view.remove_item(item)

            await msg.edit(view=view)

            del buttons[str(message_id)][f"btn_{label}_{ctx.message.id}"]
            await self.config.buttons.set(buttons)

            await ctx.send(f"✅ Button `{label}` removed from the message.")
        except Exception as e:
            await ctx.send(f"Error removing button: {e}")

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
