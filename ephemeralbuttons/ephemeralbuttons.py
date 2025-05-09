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
    """Attach a button to an existing message. Supports --text or --embedjson and --ephemeral and --emoji"""

    ephemeral = "--ephemeral" in options
    text_flag = "--text"
    embed_flag = "--embedjson"

    # Extract emoji
    emoji = None
    if "--emoji" in options:
        try:
            emoji_raw = options.split("--emoji")[1].split("--")[0].strip()
            emoji = self.parse_emoji(emoji_raw)
        except Exception as e:
            return await ctx.send(f"Invalid emoji: {e}")

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
        if channel is None:
            raise ValueError("Channel not found!")
        msg = await channel.fetch_message(message_id)
    except Exception as e:
        return await ctx.send(f"Couldn't fetch the message: {e}")

    custom_id = f"btn_{label}_{ctx.message.id}"

    buttons = await self.config.buttons()
    buttons[str(message_id)] = buttons.get(str(message_id), {})
    buttons[str(message_id)][custom_id] = {
        "label": label,
        "emoji": str(emoji) if emoji else None,
        "ephemeral": ephemeral,
        "response_type": response_type,
        "content": content
    }
    await self.config.buttons.set(buttons)

    view = View()
    view.add_item(Button(label=label, custom_id=custom_id, emoji=emoji))

    try:
        await msg.edit(view=view)
    except discord.HTTPException:
        return await ctx.send("Failed to edit message with button.")

    await ctx.send("✅ Button added!")
