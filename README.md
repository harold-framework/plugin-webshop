# Web Shop

The webshop is a shop/store system that supports a modular item system with direct handling for automatic item expiry and set purchase limits. Items
are constructed with the `Item` class and then pushed to the shop using the `addItem`

## Web framework

This plugin was originally created to work on my personal and very custom PHP framework. For this reason, the provided `index.php` file will not work if not loaded
by the framework (which chances are you don't). In this case, re-writing the index file shouldn't be too hard, all you'd need is to rewrite the request logic with
a curl handler etc.

## Screenshots

The following are a series of screenshots from a real production server environment. There is also one screenshot of the light mode option,
because I could not bare to get any more screenshots without my eyes burning.

![Desktop Dark View #1](https://cdn.morgverd.com/static/github/harold/NsannwMI1Tvj5gwHVF48GDUtL.png)
![Desktop Dark View #2](https://cdn.morgverd.com/static/github/harold/cL7cyMaWhyWEi0dIYbpXTwhId.png)
![Desktop Dark View #3](https://cdn.morgverd.com/static/github/harold/tFfKcqs9q90NltE56bvKi2LJr.png)
![Desktop Dark View #4](https://cdn.morgverd.com/static/github/harold/klZFPUFyyE6ZxyQaVoM1JBfxi.png)

![Desktop Light View #1](https://cdn.morgverd.com/static/github/harold/v71kWNzPmkxRGlzPQ3zyHI1ta.png)

## Example Item

```py

import discord
from plugins.webshop.shopManager import Item, GenericItemCallbacks

async def purchased(bot, buyer: discord.User, item: Item) -> None:

    # Here we can preform additional logic when the item is purchased,
    # such as giving the user a role or creating a role etc.

    # Finally, we just use the default item callback to send the buyer
    # a DM with the item they purchased.
    await GenericItemCallbacks.purchased(bot, buyer, item)

# The setup function is called by the shopManager when a file is loaded.
# The items can be created in standard plugins/cogs, this is just a dedicated
# entry method.
def setup(bot) -> None:

    # Here, we can add a description for the Testing category.
    bot.utils.managers.shopManager.setCategorySubtitle("Testing", "These items are purely for example purposes!")

    # Create the item with its basic information.
    testItem = bot.utils.managers.shopManager.createItem("custom_channel",
        category="Testing",
        title="Example Item",
        description="This is an example item that can be purchased.",
        image="https://my.website/example.png",
        price=100
    )
    
    # Events are a system to allow for functional modification of data and to allow
    # for easily modular flow from purchase to expiration.
    testItem.addEventCallback("purchased", purchased)
    
    # This marks the item as only being able to be purchased once by each user. This is
    # useful for permanent passes etc such as a VIP role.
    testItem.setPurchaseLimit(1)

    # This sets the item to automatically expire after two hours. When the item expires, the
    # 'expired' event is called which can be intercepted using a callback (as shown above) to
    # implement custom logic such as removing a role etc.
    testItem.setExpiry(3600 * 2)

    # Finally, we add the items to the shop.
    bot.utils.managers.shopManager.addItem(testItem)
    

```
