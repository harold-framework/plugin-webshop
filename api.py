from aiohttp import web
import asyncio, aiohttp, time, random, string

routes = web.RouteTableDef()

@routes.get('/plugins/webshop')
async def get_root(request): return web.json_response({"success": False, "error_message": "Root access to webshop is prohibited."}, status=200, content_type='application/json')

@routes.get('/plugins/webshop/view/{request_id}')
async def get_info(request):

    bot = request.app["bot"]
    request_id = request.match_info["request_id"]

    # Attempt to get the member ID from the request.
    member_id = bot.utils.managers.shopManager.getMemberIDFromRequestCode(request_id)
    if member_id is None: return web.json_response({"success": False, "error_message": "Unknown identification code.", "status_code": 401}, status=200, content_type='application/json')

    # Once we have the member ID, construct the response data.
    economyUser = await bot.utils.managers.economyManager.getUser(member_id)

    data = {
        "title": bot.config.json["plugins"]["webshop"]["web_title"],
        "currency_symbol": bot.config.json["plugins"]["webshop"]["web_currency_symbol"],
        "description": bot.config.json["plugins"]["webshop"]["web_description"],
        "user": {
            "balance": int(economyUser)
        },
        "categories": bot.utils.managers.shopManager.getCategoriesForMemberID(member_id),
        "category_subtitles": bot.utils.managers.shopManager._categorySubtitles
    }
    return web.json_response({"success": True, "data": data}, status=200, content_type='application/json')

@routes.get('/plugins/webshop/purchase/{request_id}/{item_id}')
async def get_purchase(request):

    bot = request.app["bot"]
    request_id = request.match_info["request_id"]
    item_id = request.match_info["item_id"]

    # Attempt to get the member ID from the request.
    member_id = bot.utils.managers.shopManager.getMemberIDFromRequestCode(request_id)
    if member_id is None: return web.json_response({"success": False, "error_message": "Unknown identification code.", "status_code": 401}, status=200, content_type='application/json')

    # Next try to get a reference to the item that was requested.
    item = bot.utils.managers.shopManager.getItemFromItemID(item_id)
    if item is None: return web.json_response({"success": False, "error_message": "Unknown item ID.", "status_code": 400}, status=200, content_type='application/json')

    # Now that we have the member_id and the item, we should actually
    # execute the purchase request and get its output.
    success, reason = await item.purchase(member_id)
    
    # Now we return the response from the item purchase request and allow for the website
    # to handle the rest.
    return web.json_response({"success": True, "purchase": {"success": success, "reason": reason, "item": item.getData(member_id)}}, status=200, content_type='application/json')


# This route is used by the Web Shop when running on a custom framework if a user is already
# logged in, so they don't have to generate a shop link directly as the website is able to
# generate and then use a request_id with the already stored Discord ID.
@routes.get('/plugins/webshop/get_request_id/{user_id}')
async def get_request_id(request):

    bot = request.app["bot"]
    user_id = request.match_info["user_id"]

    # First, check to see if the given user_id actually exists within the guild. For slight
    # optimisation, we can quickly get to see if the provided user_id is valid (is digit).
    if not user_id.isdigit(): return web.json_response({"success": False, "error_message": "Provided user_id is invalid.", "status_code": 400}, status=200, content_type='application/json')
    if (await bot.getGuild()).get_member(int(user_id)) is None: return web.json_response({"success": False, "error_message": "You are not apart of the discord server!", "status_code": 401}, status=200, content_type='application/json')

    # Now, since we know that the user_id provided is valid, we can simply use the shopManager
    # to get the request_id from the provided user_id.
    return web.json_response({"success": True, "request_id": bot.utils.managers.shopManager.generateLink(int(user_id), just_code=True)}, status=200, content_type='application/json')
