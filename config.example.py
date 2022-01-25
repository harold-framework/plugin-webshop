# ------------------------------------------------------------------------------------------------

if __name__ == "__main__": quit("You may not run this file directly.")
CONFIG = {}; CONFIG["IDs"] = {}; CONFIG["channels"] = {}; CONFIG["channels"]["voice"] = {}; CONFIG["channels"]["text"] = {}; CONFIG["roles"] = [] # DO NOT TOUCH
def VoiceChannel(cid=None,cname=None): return {"type":"channel.voice","cid":cid,"cname":cname} # DO NOT TOUCH
def TextChannel(cid=None,cname=None): return {"type":"channel.text","cid":cid,"cname":cname} # DO NOT TOUCH
def Role(permissions=None,weight=None,cname=None,cid=None,use_inheritance=False,inherit_from=None): return {"type":"role","weight":weight,"cid":cid,"cname":cname,"permissions":permissions,"use_inheritance":use_inheritance,"inherit_from":inherit_from} # DO NOT TOUCH
def RoleInheritance(cname=None,cid=None): return {"type":"role.inheritance","cname":cname,"cid":cid} # DO NOT TOUCH
def TimeRange(minimum,maximum): return {"type":"time.range","min":minimum,"max":maximum} # DO NOT TOUCH

# ------------------------------------------------------------------------------------------------

# The base URL of the shop page. This should include no trailing slashes. 
CONFIG["shop_link"] = "https://my.website/shop"

# The website title is divided into two parts, both with different colours. You can
# preview these on the website. 
CONFIG["web_title"] = [
    "OUR SERVER",
    "POINT SHOP"
]

# This is the currency symbol that should be put infront of all prices on the shop.
CONFIG["web_currency_symbol"] = "£"

# This is a light description about the Discord Server and the shop page. It is shown
# at the very top of the page to all users.
CONFIG["web_description"] = "A place for you to spend all of your hard earned cash on items that you can use in the Discord Server!"
