import discord
from plugins.webshop.shopManager import Item, GenericItemCallbacks

# Here, we send a simple DM to the user who purchases the item.
async def purchased(bot, buyer: discord.User, item: Item) -> None:
    if item.id == "cooldown_reset_robbery_user":
        if str(buyer.id) in bot.getCog("economy_core").commandTimeouts["rob"]:
            del bot.getCog("economy_core").commandTimeouts["rob"][str(buyer.id)]

    else:
        bot.getCog("economy_core").commandTimeouts["charity"] = None
        guild = await bot.getGuild()
        general_channel = await bot.config.getChannel(
            bot.config.json["channels"]["text"]["general"],
            guild
        )
        if general_channel is not None:
            try: await general_channel.send(":information_source:  <@" + str(buyer.id) + "> has paid to reset the Charity Robbery Cooldown!")
            except Exception: pass
            
    # After actually resetting the users cooldown we just pass over to a generic
    # callback handler to do the rest (informing the buyer).
    return await GenericItemCallbacks.purchased(bot, buyer, item)

# This ensures that only people who actually have a robbery cooldown can pay to
# reset their robbery cooldown.
def does_user_have_rob_cooldown(bot, member_id: int, item: Item) -> bool:
    return str(member_id) in bot.getCog("economy_core").commandTimeouts["rob"]

# This ensures that the charity robbery cooldown reset can only be purchased when
# the charity robbery is on a cooldown.
def does_charity_have_cooldown(bot, member_id: int, item: Item) -> bool:
    return not bot.getCog("economy_core").commandTimeouts["charity"] is None

def setup(bot) -> None:
    
    resetUserRobbery = bot.utils.managers.shopManager.createItem("cooldown_reset_robbery_user",
        category="Cooldowns",
        title="User Robbery",
        description="This resets your robbery cooldown so you're able to try and rob another person.",
        image="https://st3.depositphotos.com/1076504/13796/i/450/depositphotos_137963564-stock-photo-burglars-breaks-into-house-at.jpg",
        price=15000
    )
    resetUserRobbery.addEventCallback("is_available", does_user_have_rob_cooldown)
    resetUserRobbery.addEventCallback("purchased", purchased)

    resetCharityRobbery = bot.utils.managers.shopManager.createItem("cooldown_reset_robbery_charity",
        category="Cooldowns",
        title="Charity Robbery",
        description="This resets the Charity Robbery cooldown for everyone in the server.",
        image="https://wallpaperaccess.com/full/2648103.jpg",
        price=75000
    )
    resetCharityRobbery.addEventCallback("is_available", does_charity_have_cooldown)
    resetCharityRobbery.addEventCallback("purchased", purchased)

    # Finally, we add the items to the shop.
    bot.utils.managers.shopManager.addItem(resetUserRobbery)
    bot.utils.managers.shopManager.addItem(resetCharityRobbery)
    