from .ephemeralbuttons import EphemeralButtons

async def setup(bot):
    await bot.add_cog(EphemeralButtons(bot))
