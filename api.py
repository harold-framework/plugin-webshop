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