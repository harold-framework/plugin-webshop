import discord, datetime
from plugins.webshop.shopManager import Item, GenericItemCallbacks

__VIP_ROLE_ID__ = 935276275382222848
__VIP_CHANNEL_ID__ = 935276598083608636

async def purchased_request_from_staff(bot, buyer: discord.User, item: Item) -> None:
    itemData = item.getData(buyer.id); ecoUser = await bot.utils.managers.economyManager.getUser(buyer.id)
    embed = discord.Embed(title="Request From Staff", description="You brought a **" + itemData["title"] + "** for ``" + bot.utils.managers.economyManager.formatMoney(itemData["price"]) + "``. You now have ``" + bot.utils.managers.economyManager.formatMoney(int(ecoUser)) + "``. To get your item, please contact an Administrator!", timestamp=datetime.datetime.utcnow())
    embed.set_image(url=itemData["image"] if "image" in itemData else "https://t3.ftcdn.net/jpg/02/26/34/20/360_F_226342059_IYzkHaiDJB2B179CvxfhnDWlVMwlBcVK.jpg")
    try: await buyer.send(embed=embed)
    except Exception: pass

async def purchased_vip_pass(bot, buyer: discord.User, item: Item) -> None:

    # Get a reference to the guild so the member can be gathered. We then also get
    # a reference to the VIP role to give to the member.
    guild = await bot.getGuild()
    member = guild.get_member(buyer.id)
    role = guild.get_role(__VIP_ROLE_ID__)
    channel = guild.get_channel(__VIP_CHANNEL_ID__)

    if member is None: bot.log("Failed to gather refrence of buyer in Discord Server.", error=True)
    if role is None: bot.log("Failed to get VIP role in server. Check the __VIP_ROLE_ID__ variable at the top of '/plugins/webshop/items/general.py'", error=True)
    if channel is None: bot.log("Failed to get VIP channel in server. Check the __VIP_CHANNEL_ID__ variable at the top of '/plugins/webshop/items/general.py'", error=True)

    if isinstance(member, discord.Member) and isinstance(role, discord.Role):
        try: await member.add_roles(role, reason="User brought the VIP pass from the Shop.")
        except Exception: bot.log("Failed to give VIP buyer '" + str(buyer.name) + "' the VIP role in the Discord Server.", error=True)
    
    if isinstance(channel, discord.TextChannel):
        try: await channel.send(":partying_face:  Welcome our latest V.I.P  <@" + str(buyer.id) + ">!")
        except Exception: bot.log("Failed to send message into VIP channel.", error=True)

    await GenericItemCallbacks.purchased(bot, buyer, item)

def setup(bot) -> None:
    
    customEmojiItem = bot.utils.managers.shopManager.createItem("custom_emoji",
        category="General",
        title="Custom Emoji",
        description="This allows you to add a custom emoji to the Discord server which anyone can use. Optionally it may be animated upon request.",
        image="https://www.dictionary.com/e/wp-content/uploads/2021/06/20210624_atw_sunglassesSmiling_1000x700.png",
        price=100000
    )
    customEmojiItem.addEventCallback("purchased", purchased_request_from_staff)
    customEmojiItem.setPurchaseLimit(1)

    VIPPassItem = bot.utils.managers.shopManager.createItem("vip_pass",
        category="General",
        title="V.I.P Pass",
        description="Get access to the secret VIP area with other VIP members. You will also get the VIP role which helps you easily show people how rich you are!",
        image="https://image.freepik.com/free-vector/vip-with-crown-composition_1284-36184.jpg",
        price=250000
    )
    VIPPassItem.addEventCallback("purchased", purchased_vip_pass)
    VIPPassItem.setPurchaseLimit(1)
    
    customChannelItem = bot.utils.managers.shopManager.createItem("custom_channel",
        category="General",
        title="Private Channel",
        description="Have a private voice or text channel in the Discord Server that only you and people you allow can join.",
        image="https://us.123rf.com/450wm/makc76/makc761606/makc76160600029/58022332-lock-and-key-lock-with-key-key-lock-icon-vector-lock-icon-key-lock-and-key-in-flat-style-padlock-wit.jpg",
        price=75000
    )
    customChannelItem.addEventCallback("purchased", purchased_request_from_staff)
    customChannelItem.setPurchaseLimit(1)

    # Finally, we add the items to the shop.
    bot.utils.managers.shopManager.addItem(customEmojiItem)
    bot.utils.managers.shopManager.addItem(VIPPassItem)
    bot.utils.managers.shopManager.addItem(customChannelItem)
    