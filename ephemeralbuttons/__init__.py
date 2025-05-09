from .ephemeralbuttons import ephemeralbuttons

async def setup(bot):
    await bot.add_cog(ephemeralbuttons(bot))
