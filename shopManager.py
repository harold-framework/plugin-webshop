from ast import mod
import discord, inspect, traceback, time, datetime, asyncio
from types import ModuleType
from typing import Union, Optional, Callable, Any, Tuple

# These are a collection of generic callbacks that can be used for items that
# are generic enough to share callbacks.
class GenericItemCallbacks:
    async def purchased(bot, buyer: discord.User, item) -> None:
        itemData = item.getData(buyer.id); ecoUser = await bot.utils.managers.economyManager.getUser(buyer.id)
        embed = discord.Embed(title="Purchase Successful", description="You brought **" + itemData["title"] + "** for ``" + bot.utils.managers.economyManager.formatMoney(itemData["price"]) + "``. You now have ``" + bot.utils.managers.economyManager.formatMoney(int(ecoUser)) + "``.", timestamp=datetime.datetime.utcnow())
        if item._expiry: embed.add_field(name="Expiry", value="This item automatically expires in: ``" + str(datetime.timedelta(seconds=item._expiry)) + "``", inline=False)
        embed.set_image(url=itemData["image"] if "image" in itemData else "https://t3.ftcdn.net/jpg/02/26/34/20/360_F_226342059_IYzkHaiDJB2B179CvxfhnDWlVMwlBcVK.jpg")
        try: await buyer.send(embed=embed)
        except Exception: pass
    
    async def expired(bot, buyer: discord.User, item) -> None:
        itemData = item.getData(buyer.id)
        embed = discord.Embed(title="Item Expired", description="The item **" + itemData["title"] + "** has expired.", timestamp=datetime.datetime.utcnow())
        embed.set_image(url=itemData["image"] if "image" in itemData else "https://t3.ftcdn.net/jpg/02/26/34/20/360_F_226342059_IYzkHaiDJB2B179CvxfhnDWlVMwlBcVK.jpg")
        try: await buyer.send(embed=embed)
        except Exception: pass


class Item():
    def __init__(self, bot, item_id: str, category: str, data: dict):
        self.bot = bot
        self.id: str = item_id
        self.category: str = category
        self._data: dict = data
        
        # UPDATE 24/01/2022:
        #   We now supply default callbacks. These are from the GenericItemCallbacks
        #   class that provides a set of generic responses to events. Setting the default
        #   callbacks still allow for the events to be overwritten using the addEventCallback
        #   function.
        self._callbacks: dict = {
            "purchased": GenericItemCallbacks.purchased,
            "expired": GenericItemCallbacks.expired
        }
        
        # These are optional options that modify the availablity of the item for
        # a given user. If set they should be respected over the is_available
        # event response since the item developer has explicitly imposed the limits.
        self._expiry: Optional[int] = None
        self._limit: Optional[int] = None
    
    # This option defines the maximum amount of this item that a user is able to purchase.
    # Setting it to one would mean that the user is only allowed to purchase the given item
    # once. Note that setting the value to zero would result in the item always being unavaiable
    # to every user.
    def setPurchaseLimit(self, amount: int = 1) -> None:
        self._limit = amount

    # This option sets how long the item should remain active for. Once the expiry time has been
    # met the "expired" event is called on the Item with the given member_id. The value should be
    # the amount of seconds, with the end expiry time calculated as (current_time + seconds). Any
    # users that have purchased the item and are waiting for it to expire will not be able to
    # purchase the item as it will be marked unavaiable during expiry wait. 
    def setExpiry(self, seconds: int) -> None:
        self._expiry = seconds

    # This is used to cause a pre-mature expiry for a given user if they have the
    # item currently and it hasn't yet expired. The second argument determines if
    # we should still call the "expired" event once we've manually expired the user's
    # item. This is useful for single use items which are purchased with an expiry and
    # then activate on a different event such as a user being robbed. The value returned
    # determines if the action was successful or not.
    def manuallyExpireMemberID(self, member_id: int, executeCallback: bool = True) -> bool:
        userExpiry = self.bot.utils.managers.stateManager.get("shop-expiry-" + str(member_id))
        if userExpiry is None: return False
        if self.id not in list(userExpiry.keys()): return False

        # In this case the given member_id does have an outstanding expiry for this item set.
        # If the executeCallback argument is set we cannot do much other than marking the expiry
        # zero so the shopManager handles it instead (since the event to call is async).
        if executeCallback:
            userExpiry[self.id] = 0    

        else:
            # If we're not executing the callback, we can just pop the expiry key from the users
            # data and then overwrite the current user expiries. Then we don't have to wait for
            # the shopManager task to catch up.
            userExpiry.pop(self.id, None)
        
        self.bot.utils.managers.stateManager.set("shop-expiry-" + str(member_id), userExpiry)
        return True

    def getData(self, member_id: Optional[int] = None) -> dict:
        
        # We also now iterate through all the data given to check if there are
        # any events registered to modify the given value before its sent out.
        itemData = {"id": self.id}
        for k in list(self._data.keys()):
            v = self._invokeEvent("get_" + k, self)
            if v is None: v = self._data[k]
            itemData[k] = v

        # This is the default value which marks that the item has not yet determined
        # is availability. Before the JSON is returned this value will become boolean.
        isAvailable: Optional[bool] = None

        # First check to see if the user has already reached the limit of this item
        # that can be purchased. (If the limiter is enabled).
        if self._limit is not None:
            userPurchaseCounter = self.bot.utils.managers.stateManager.get("shop-purchases-" + str(member_id))
            if userPurchaseCounter is None: userPurchaseCounter = {}
            if self.id not in list(userPurchaseCounter.keys()): userPurchaseCounter[self.id] = 0
            if userPurchaseCounter[self.id] >= self._limit: isAvailable = False

        # Next, if this item has a set expiry we should check to see if the given
        # member_id is assosiated with any existing expiry for this item ID.
        if self._expiry is not None:
            userExpiries = self.bot.utils.managers.stateManager.get("shop-expiry-" + str(member_id))
            if userExpiries is None: userExpiries = {}
            if self.id in list(userExpiries.keys()): isAvailable = False

        # If we have not yet determined a value for the avaiable key, we should try
        # to invoke the is_available event on the item to get the value that way. If
        # that fails and there is still no available key, we should just default the
        # item to being unavailable.
        if isAvailable is None:
            isAvailable = self._invokeEvent("is_available", member_id, self)
            if isAvailable in [True, False]: itemData["available"] = isAvailable
            if "available" not in itemData: itemData["available"] = False
        
        else:
            # If we've already determined an availability state for the item just use
            # that value instead.
            itemData["available"] = isAvailable

        # If the badges key is None then it was set during the createItem function.
        # The website does not like when this key is null, and instead checks if the
        # key even exists. For this reason if the badges key is None we should delete it.
        if itemData["badges"] is None: del itemData["badges"]

        return itemData

    # This is used to attach an event string to a callable function. The Item does not support
    # multiple callbacks assigned to a single event, instead the callback may call further callbacks
    # if needed. Events can be found in the events.txt file.
    def addEventCallback(self, event: str, callback: Callable) -> None:
        self._callbacks[event] = callback

    # This is a primarily internal function to invoke a given event on an item, calling any assosiated
    # callbacks with it. This function does NOT support async callbacks, so None will be returned in place
    # of a failed execution. For async callbacks use _asyncInvokeEvent.
    def _invokeEvent(self, event: str, *args) -> Any:
        if event not in list(self._callbacks.keys()): return None
        if inspect.iscoroutinefunction(self._callbacks[event]): return None
        return self._callbacks[event](self.bot, *args) 

    # This is simply the _invokeEvent function however async functions are supported. This function therefore
    # supports any form of callback function type, making it best for API internal calls.
    async def _asyncInvokeEvent(self, event: str, *args) -> Any:
        if event not in list(self._callbacks.keys()): return None
        if inspect.iscoroutinefunction(self._callbacks[event]): return await self._callbacks[event](self.bot, *args)
        return self._callbacks[event](self.bot, *args)

    # This function is a direct function to attempt to make a given member_id purchase the given item. If the
    # purchase was successful the return values will be: True, None. This represents a successful execution
    # without error. If the purchase fails for any reason, then the return values will be: False, "Error Reason".
    async def purchase(self, member_id: int) -> Tuple[bool, Optional[str]]:
        
        # First when a user attempts to purchase an item we should make sure that it is still available to them.
        member_data = self.getData(member_id)
        if not member_data["available"]:
            return False, "Item is unavailable."
        
        # Next, we should get a reference to the given member's economyUser. This allows us to then check the
        # users balance to ensure that they can actually afford the item currently.
        ecoUser = await self.bot.utils.managers.economyManager.getUser(member_id)
        if ecoUser is None: return False, "Failed to find member in Discord Server."
        if member_data["price"] > int(ecoUser): return False, "Member cannot afford item."

        # Finally, we actually complete the transaction and then add the purchase to the member ID's purchase
        # counter for the limiter system to work correctly.
        ecoUser.transaction(-member_data["price"], "Purchased '" + member_data["title"] + "' from shop.")
        userPurchaseCounter = self.bot.utils.managers.stateManager.get("shop-purchases-" + str(member_id))
        if userPurchaseCounter is None: userPurchaseCounter = {}
        if self.id not in list(userPurchaseCounter.keys()): userPurchaseCounter[self.id] = 0
        userPurchaseCounter[self.id] = userPurchaseCounter[self.id] + 1
        self.bot.utils.managers.stateManager.set("shop-purchases-" + str(member_id), userPurchaseCounter)

        # Invoke the purchased event on the item with the given user, gathered from the economyUser's internal
        # userObject reference, so the item can execute any callbacks such as sending a message to the user etc.
        await self._asyncInvokeEvent("purchased", ecoUser.userObject, self)

        # If the item expires over time add the expiry data to the members shop data.
        if self._expiry is not None:
            userExpiry = self.bot.utils.managers.stateManager.get("shop-expiry-" + str(member_id))
            if userExpiry is None: userExpiry = {}
            userExpiry[self.id] = int(time.time()) + self._expiry
            self.bot.utils.managers.stateManager.set("shop-expiry-" + str(member_id), userExpiry)
        
        return True, None

class shopManager():
    def __init__(self, bot):
        self.bot = bot
        self._requestIDs = {}
        self._allItems = []
        self._categorySubtitles = {}
        
        # Create the task to check for expired items and then assosiate it with the
        # webshop plugin incase the plugin is reloaded or unloaded alltogether.
        self.bot.create_task(self._item_expiry_task(), "webshop")
    
    def setCategorySubtitle(self, category: str, text: str) -> None:
        self._categorySubtitles[category] = text

    def getCategoriesForMemberID(self, member_id: int) -> dict:
        categories = {}
        for item in self._allItems:
            if item.category not in list(categories.keys()):
                categories[item.category] = []
            categories[item.category].append(item.getData(member_id))
        return categories

    def createItem(
        self,
        item_id: str,
        category: str,
        title: str,
        description: str,
        image: str,
        price: int,
        badges: Optional[dict] = None,
        available: bool = True
    ) -> Item:
        return Item(self.bot, item_id, category, {
            "title": title,
            "description": description,
            "image": image,
            "price": price,
            "badges": badges,
            "available": available
        })

    def addItem(self, item: Item) -> None:
        self._allItems.append(item)

    def getItemFromItemID(self, item_id: str) -> Optional[Item]:
        for item in self._allItems:
            if item.id == item_id: return item
        return None

    def getMemberIDFromRequestCode(self, request_code: str) -> Optional[int]:
        if request_code not in list(self._requestIDs.keys()): return None
        return self._requestIDs[request_code]

    def getRequestCodeFromMemberID(self, member_id: int) -> Optional[str]:
        for requestCode in list(self._requestIDs.keys()):
            if self._requestIDs[requestCode] == int(member_id): return requestCode
        return None

    def generateLink(self, member_id: int) -> str:

        # Get the members last request code if they have one. If they do not then
        # generate a random string and add that to the requestIDs pool.
        requestCode = self.getRequestCodeFromMemberID(int(member_id))
        if requestCode is None:
            requestCode = self.bot.utils.helpers.core.randomString()
            self._requestIDs[requestCode] = int(member_id)

        return self.bot.config.json["plugins"]["webshop"]["shop_link"] + "?id=" + str(requestCode)

    def loadFile(self, filepath: str) -> bool:
        filepath = filepath.replace(
            self.bot.config.json["rootpath"] + "/",
            ""
        )
        filepath = filepath.replace(".py", "")
        filepath = ".".join(filepath.split("/"))

        module = self.bot.utils.helpers.core.doImport(filepath)

        # In this case, there was an error trying to actually import the file.
        if not isinstance(module, ModuleType):
            return False

        # If the module was successfully imported, try to locate a non-async setup
        # function to pass the bot reference to. This is essentially the entrypoint
        # for the item file to actually construct and submit its item.
        if inspect.isfunction(getattr(module, "setup")):
            module.setup(self.bot)

        return True

    # This task continously checks the stateManager for any existing expiries. It then
    # waits for the expiry time to be met. Once this has happened the 'expired' event
    # is called on the item with the discord.User.
    async def _item_expiry_task(self) -> None:
        await self.bot.wait_until_ready()

        while True:
            try:
                for k in self.bot.utils.managers.stateManager.currentStateData:
                    if not k.startswith("shop-expiry-"): continue
                    member_id = int(k.replace("shop-expiry-", "")); user = None

                    # Here we get each item ID in the users expiry dictionary, because the
                    # member could hypothetically have multiple items on expiry cooldown.
                    itemsExpiryData = dict(self.bot.utils.managers.stateManager.currentStateData[k][0])

                    for item_id in self.bot.utils.managers.stateManager.currentStateData[k][0]:
                        if int(time.time()) >= self.bot.utils.managers.stateManager.currentStateData[k][0][item_id]:
                            
                            # In this case the given item_id has expired for the member. We should get a user refrence
                            # for the member and then call the expired event on the item. We also check to see if the user
                            # is already not none, which would indicate that multiple items have expired together.
                            if user is None:
                                user = self.bot.get_user(member_id)
                            
                            if user is not None:
                                item = self.getItemFromItemID(item_id)
                                if item is not None: await item._asyncInvokeEvent("expired", user, item)

                            else:
                                self.bot.log("The user ID '" + str(member_id) + "' has a finished expiry for item '" + str(item_id) + "' however we cannot get a user object. This means we cannot call the expiry function on the given member ID.", error=True)

                            # Finally, we remove the item_id from the users stateData.
                            itemsExpiryData.pop(item_id, None)
                    
                    # If the items expiry data was modified, we should set the new value.
                    if itemsExpiryData != self.bot.utils.managers.stateManager.currentStateData[k][0]:
                        self.bot.utils.managers.stateManager.set(k, itemsExpiryData)
                        
                await asyncio.sleep(1)

            except Exception:
                traceback.print_exc()

