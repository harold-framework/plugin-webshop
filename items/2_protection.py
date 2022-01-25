import discord, random
from typing import Optional
from plugins.webshop.shopManager import Item, GenericItemCallbacks

# This event is called each time someone gets successfully robbed.
# Instead of hooking into the 'economy_core.can_user_rob' hook we
# use the direct 'economy_core.can_user_robbery_success' which is
# only called when the robbery attempt is successful, which is when
# we should deploy/use any protection items if we have them.
async def economy_can_robbery_succeed(bot, ctx, target: discord.Member) -> Optional[bool]:

    # First we should get the targets items that have not yet expired.
    targetExpiries = bot.utils.managers.stateManager.get("shop-expiry-" + str(target.id))
    if targetExpiries is None: return

    # Next, go through all the items that the user has and check for any
    # that are protection items.
    active_item_id = None
    for item_id in targetExpiries:
        if item_id in ["protection_shield", "protection_mirror", "protection_armed_security"]:
            active_item_id = item_id
    
    # If the target does not have any protection items, just return.
    if active_item_id is None: return
    protection_item = bot.utils.managers.shopManager.getItemFromItemID(active_item_id)
    if protection_item is None: return

    # Here we create the embed that will be sent in place of the original robbery message.
    itemData = protection_item.getData(target.id)
    embed = discord.Embed(title=itemData["title"])
    embed.set_image(url=itemData["image"])

    if protection_item.id == "protection_shield":
        embed.description = "<@" + str(target.id) + ">  had a Shield which was used to block the robbery attempt!"

    elif protection_item.id == "protection_mirror":

        # Here we get the amount to rob from the user
        # just as the standard economy_core cog would.
        thiefEco = await bot.utils.managers.economyManager.getUser(ctx.author.id)
        targetEco = await bot.utils.managers.economyManager.getUser(target.id)
        amount_robbed, __ = bot.getCog("economy_core")._get_robbery_amount(int(thiefEco))
        if amount_robbed > int(thiefEco): amount_robbed = int(thiefEco)

        # Finally, actually execute the transaction against the original target.
        thiefEco.transaction(-amount_robbed, "Robbery attempt deflected using a Mirror")
        targetEco.transaction(amount_robbed, "Your mirror has deflected a robbery attempt from " + str(ctx.author.name))

        embed.description = "<@" + str(target.id) + ">  had a Mirror which has deflected the robbery attempt. <@" + str(ctx.author.id) + ">  has lost **" + bot.utils.managers.economyManager.formatMoney(amount_robbed) + "**, which has gone to  <@" + str(target.id) + ">."

    elif protection_item.id == "protection_armed_security":
        
        # We use a 50/100 (1/2) chance of the Armed Security actually shooting and hitting the
        # thief. If they don't get get shot, it just acts as a shield.
        if (random.random() < (50 / 100)):
            
            # Get references to the thief and target economyUser references.
            thiefEco = await bot.utils.managers.economyManager.getUser(ctx.author.id)
            targetEco = await bot.utils.managers.economyManager.getUser(target.id)

            # Calculate the 70% fine against the thief, And then take the fine.
            fineAmount = int((70.00*float(int(thiefEco))) / 100.0)
            thiefEco.transaction(-fineAmount, "You got shot by Armed Security during a failed robbery")

            embed.description = "<@" + str(target.id) + ">  had armed security employed to protect themselves. The security team took a shot, and it hit. <@" + str(ctx.author.id) + ">  has lost **" + bot.utils.managers.economyManager.formatMoney(fineAmount) + "**!"
        
        else:
            
            # In this case, the Armed Secturity missed their shot.
            embed.description = "<@" + str(target.id) + ">  had armed security employed to protect themselves. The security team took a shot, but missed."

    else:
        
        # I have no idea how this could happen, but just incase it does we should
        # have a backup description ready.
        embed.description = "Unknown protection item used!"

    # Once the item has been used, we should expire the item.
    protection_item.manuallyExpireMemberID(target.id)

    # Finally, send the new embed and then return false to stop the economy_core from
    # continuing with the robbery.
    await ctx.send(embed=embed)
    return False

# This function is used to add the badges 
def get_badges(bot, item: Item) -> dict:
    return {
        str(round(item._expiry / 3600)) + "hr Expiry": "btn-warning",
        "Single Use": "btn-danger"
    }

# The availability function is fairly simple. Since we do not want the user to
# be able to purchase multiple protection items, we simply check to see if they
# have any of the protection item ID's in their expiry data.
def is_available(bot, member_id: int, item: Item) -> bool:
    userExpiries = bot.utils.managers.stateManager.get("shop-expiry-" + str(member_id))
    if userExpiries is None: return True

    # If they do have some items on expiry, check to see if any of them are protection
    # items by checking their item ID.
    for item_id in userExpiries:
        if item_id.startswith("protection_"): return False

    # Finally, if they have no protection items active return True.    
    return True

def setup(bot) -> None:
    
    # First, we setup the robbery event so we can actually do stuff when the user
    # gets robbed.
    bot.utils.managers.hookManager.addListener("economy_core.can_user_robbery_success", economy_can_robbery_succeed)

    # Add a basic description for how the category works.
    bot.utils.managers.shopManager.setCategorySubtitle("Protection", "These items are used to protect yourself from robbery attempts. They are only activated if the robbery was actually successful, and expire after they're used. You cannot own more than one protection item at a time.")

    shieldItem = bot.utils.managers.shopManager.createItem("protection_shield",
        category="Protection",
        title="Shield",
        description="A shield will block the first robbery attempt against you and then break.",
        image="https://progameguides.com/wp-content/uploads/2019/08/fortnite-back-bling-banner-shield.jpg",
        price=25000
    )
    shieldItem.addEventCallback("is_available", is_available)
    shieldItem.addEventCallback("get_badges", get_badges)
    shieldItem.setExpiry(3600 * 4)
    
    mirrorItem = bot.utils.managers.shopManager.createItem("protection_mirror",
        category="Protection",
        title="Mirror",
        description="A mirror will reverse the first robbery attempt against you, instead robbing the person who tried to rob you.",
        image="https://st4.depositphotos.com/1781787/31564/i/450/depositphotos_315641368-stock-photo-dark-room-magical-antique-mirror.jpg",
        price=50000
    )
    mirrorItem.addEventCallback("is_available", is_available)
    mirrorItem.addEventCallback("get_badges", get_badges)
    mirrorItem.setExpiry(3600 * 4)
    
    armedSecurityItem = bot.utils.managers.shopManager.createItem("protection_armed_security",
        category="Protection",
        title="Armed Security",
        description="Armed Security is similar to a shield. On the first robbery attempt the security team will attempt to shoot the would-be thief. If they hit them, the thief will lose some money. Either way, the thief will be scared off.",
        image="https://www.ziprecruiter.com/svc/fotomat/public-ziprecruiter/cms/506138376ArmedPrivateSecurity.jpg",
        price=75000
    )
    armedSecurityItem.addEventCallback("is_available", is_available)
    armedSecurityItem.addEventCallback("get_badges", get_badges)
    armedSecurityItem.setExpiry(3600 * 4)

    # Finally, we add the items to the shop.
    bot.utils.managers.shopManager.addItem(shieldItem)
    bot.utils.managers.shopManager.addItem(mirrorItem)
    bot.utils.managers.shopManager.addItem(armedSecurityItem)
