import discord, asyncio, glob
from discord.ext import commands
from utils.models.plugin import Plugin
from utils.models.interactions import Interactions

class WebShop(Plugin):
    def __init__(self, bot):
        self.bot = bot

    @Interactions.slash(
        name="shop",
        description="Generate a link to the Discord Server point shop!",
        permission="webshop.use"
    )
    async def _shop(self, ctx) -> None:

        generatedLink = self.bot.utils.managers.shopManager.generateLink(ctx.author.id)
        embed = discord.Embed(
            title="Point Shop",
            description="You can click [__here__](" + str(generatedLink) + ") to visit the shop. Please note that this link is directly assosiated with your account, giving this link to other people will allow them to make purchases with your account!"
        )
        embed.set_image(url=self.bot.config.json["cdn_link"] + "web_shop.jpg")

        return await ctx.send(embed=embed, hidden=True)


def setup(bot):

    from plugins.webshop.api import routes
    bot.data["api_routes"].append(["webshop", routes])

    # Add the shared manager utility.
    bot.utils.add("managers", "shopManager", "plugins.webshop.shopManager")

    # Load all of the default items.
    for itemFilepath in glob.glob(bot.config.json["rootpath"] + "/plugins/webshop/items/*.py"):
        bot.utils.managers.shopManager.loadFile(itemFilepath)
    
    bot.add_cog(WebShop(bot))