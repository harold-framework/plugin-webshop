<?php

// These are the configuration values for the API. There should be no trailing slash for the
// DISCORD_BOT_API_URL key.

define("DISCORD_BOT_API_URL", "https://api.my.website/plugins/webshop");
define("DISCORD_BOT_API_KEY", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX");
define("DISCORD_SHOP_COOKIE_NAME", "_DISCORD_SHOP_ID");
$path = str_replace(APP_PATH."/pages", "", __DIR__);

// This function simply takes in any API response and checks its success status. If the response
// was unsuccessful it will then attempt to gather the "status_code" key from the response. If this
// key is 401, then we know that the API is telling us that the provided ID is invalid, so we should
// destroy the stored cookie on the users system to prevent them from constantly experiencing the issue.
function destroyIncorrectID(array $response): void {
    if ($response["success"]) { return; }
    if (!array_key_exists("status_code", $response)) { return; }
    if ($response["status_code"] == 401) {

        // If the status_code is 401, then we should discard the users ID cookie.
        CookieController::delete(DISCORD_SHOP_COOKIE_NAME);

    }
}

// If there is an 'id' argument set, we should set the users cookie value and then refresh.
if (isset($_GET["id"]) || !empty($_GET["id"])) {

    // Check to see if we actually successfully set the cookie value.
    // We also now explicitly set it to disable the allow_unregistered_discard option. This means that the
    // cookie will not automatically be discarded when the user goes on a different page due to the fact that
    // this cookie is not always registered internally. (Since the page only executes on request.)
    if (!CookieController::set(DISCORD_SHOP_COOKIE_NAME, $_GET["id"], allow_unregistered_discard: false)) {
        raise(500, "Failed to set your ID cookie!", false);
    }

    // Refresh the page by setting the location back to this current page.
    HeaderController::location($path);
    die();

}

// Check to see what the stored ID cookie value is. If it is not set, then we should
// display an error, since the request does not have any sent ID cookie value, and
// does not supply any ID in the URL GET arguments.
$user_id = CookieController::get(DISCORD_SHOP_COOKIE_NAME);
if (is_null($user_id)) {

    // If the cookie null, the user either does not have the cookie value stored or
    // it is nolonger valid (eg: Integrity was breached.)
    raise(400, "Missing valid identification. Try using /shop again in the Discord Server!");

}

// These are the buttons that are shown to the user when there is an error.
$errorButtons = [
    "Retry" => $path,
    "Go Home" => "/"
];

// Here, we should actually handle purchases. If the method is POST and there is an "item_id"
// key set in the POST body then we should assume its a purchase request. Note that at this
// point the given ID has not been verified as the purchase call proceeds the view request.
// This is so the view request can return the newly modified data such as the balance and
// any single use items can mark themselves as unavailable to the user.
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST["item_id"])) {
    
    // Once we recieve the purchase request we do not have to preform any additional validation
    // on the website side, all ID verification, item availability, price checks etc are preformed
    // on the API.
    $purchaseResponse = RequestController::api(
        DISCORD_BOT_API_URL . "/purchase/" . urlencode($user_id) . "/" . urlencode($_POST["item_id"]),
        [
            "key" => DISCORD_BOT_API_KEY
        ]
    );
    if (is_null($purchaseResponse)) { raise(503, "Failed to connect to Discord Purchase API.", false, $errorButtons); }
    if (!$purchaseResponse["success"]) { destroyIncorrectID($purchaseResponse); raise((array_key_exists("status_code", $purchaseResponse) ? $purchaseResponse["status_code"] : 500), $purchaseResponse["error_message"], false, $errorButtons); }    

    // In this case we have recieved a successful response, however this simply means that there were
    // no errors in the request. It does not mean that the purchase was successful. For that, we must
    // check the purchase->success value. If it is false, the error will be stored in purchase->reason
    if (!$purchaseResponse["purchase"]["success"]) {
        raise(400, $purchaseResponse["purchase"]["reason"], false, $errorButtons);
    }

    // If we get to this point, the purchase was a success.
    $purchaseSuccess = $purchaseResponse["purchase"]["item"]["title"];

} else {

    // Default value to mark the page as having no purchases.
    $purchaseSuccess = null;

}

// Create a new call to the API to fetch the related user's information. Also fetches all
// of the items with their availabilty set API side.
$response = RequestController::api(
    DISCORD_BOT_API_URL . "/view/" . urlencode($user_id),
    [
        "key" => DISCORD_BOT_API_KEY
    ]
);
if (is_null($response)) { raise(503, "Failed to connect to Discord View API.", false, $errorButtons); }
if (!$response["success"]) { destroyIncorrectID($response); raise((array_key_exists("status_code", $response) ? $response["status_code"] : 500), $response["error_message"], false, $errorButtons); }

// Finally, we move inside of the data key which actually contains the important data.
$response = $response["data"];

// This model contains the default values which are added to all items if they
// lack the given key. This ensures that each item can be correctly parsed by the
// HTML handlers below.
$baseItemModel = [
    "id" => "unknown",
    "title" => "Missing Title",
    "description" => "This item has no description assosiated. You should report this issue to staff.",
    "image" => "https://icon-library.com/images/photo-placeholder-icon/photo-placeholder-icon-7.jpg",
    "price" => 0,
    "available" => false
];

?>

<!DOCTYPE html>
<html lang="en">

    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Discord Shop</title>
        <script src="https://kit.fontawesome.com/3f16fb12e4.js" crossorigin="anonymous"></script>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet"
            integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
        
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

            html,body{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow-x: hidden;
            }

            header{
                background-color: #FFF9F4;
            }
            .navbar-brand img{
                width: 291.11px;
                height: 39.27px;
            }
            h1, h4 {
                font-family: 'Bebas Neue', cursive;
                font-style: normal;
                font-weight: bold;
                font-size: 80px;
                line-height: 80px;
            }

            h5{
                color: #363958;
            }

            .title-1{
                color: #FA804C;
            }

            .title-2{
                color: #363958;
            }

            .btn-generic {
                background: linear-gradient(180deg, #3D4FF3 0%, #3543BC 100%);
            }

            .card img{
                background-color: #F1F1F1;
                border-radius: 10px;
            }
            .price{
                color: #FA804C;
            }
            .modal-open {
                padding-right: 0 !important
            }
            .title{
                color: #363958;
                font-size: 48px;
                font-weight: bold;
            }

            .feature {
                border-radius: 20px;
            }
            .user-balance {
                color: white;
                background-color: #363958;
            }

            @media only screen and (max-width: 688px){
                h1{
                    font-size: 60px;
                    line-height: 60px;
                }
                .title{
                    font-size: 36px;
                }
                .navbar-brand img{
                    width: 192.75px;
                    height: 26px;
                }
                .top-area {
                    height: 100vh;
                }
                .top-inner {
                    padding-top: 30%;
                }
                .top-inner img {
                    display: none;
                }
            }

            @media (prefers-color-scheme: dark) {
                body {
                    background-color: #1d1c1b;
                    color: #fff;
                }
                header { background-color: #171717; }
                h5 { color: #c8c3c3; }
                .title-2 { color: #6d7298; }
                .title { color: #c8c3c3; }
                .card { background-color: #313131; }
                .badge { color: #000; }
                .price { color: #ffaa85; }
                .card-title { color: #c8c3c3; }
                .user-balance { background-color: #1d1c1b !important; }
                .feature { background-color: #313131; }
                .modal-content { background-color: #262323; }
            }

        </style>
    </head>

    <body>

        <header>
            <div class="container top-area pb-5 mb-5">
                <div class="row row-cols-1 row-cols-md-2 d-flex align-items-center justify-content-between text-lg-right text-center top-inner">
                    <div class="top-image">
                        <img class="order-2 order-md-1 mt-5" src="<?=$path;?>/assets/icons/harold-money.png" alt="" style="width: 600px">
                    </div>
                    <div class="order-1 order-md-2 mt-5 col-md-5">
                        <h1 class="mx-auto">
                            <span class="title-1"><?=is_null($purchaseSuccess) ? $response["title"][0] : "PURCHASE SUCCESSFUL";?></span>
                            <br>
                            <span class="title-2"><?=is_null($purchaseSuccess) ? $response["title"][1] : $purchaseSuccess;?></span>
                        </h1>
                        <div class="text-center w-75 mx-auto">
                            <p><?=$response["description"];?></p>
                        </div>
                        <div class="pt-5 mx-auto">
                            <div class="feature user-balance py-3">
                                <h4 class="pt-2" style="font-size: 26px; line-height: 0.8">Your Balance</h4>
                                <h1 class="my-0" style="font-size: 60px">
                                    <?=$response["currency_symbol"] . number_format($response["user"]["balance"]);?>
                                </h1>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <main>

            <?php

            // Here, we process all of the items from the API response and generate categories that contain all of their
            // respective purchasable items.
            foreach($response["categories"] as $categoryName => $categoryItems) {
            ?>

            <section class="container mb-5">
                <h3 class="title mb-4"><?=$categoryName;?></h3>
                
                <?php
                if (array_key_exists($categoryName, $response["category_subtitles"])) {
                ?>

                <h5 class="mb-4"><?=$response["category_subtitles"][$categoryName];?></h5>
                
                <?php
                }
                ?>

                <div class="row row-cols-1 row-cols-md-1 row-cols-lg-3 g-4">

            <?php
            foreach($categoryItems as $itemData) {

            // Ensure that the item model has all of the required base badges.
            foreach($baseItemModel as $k => $v) {
                if (!array_key_exists($k, $itemData)) {
                    $itemData[$k] = $v;
                }
            }

            // Check to see if the user can actually afford the item, since there's no point
            // allowing them to try and purchase it if they just cannot afford it at all.
            if ($itemData["price"] > $response["user"]["balance"]) {
                $itemData["available"] = false;
            }

            ?>

                    <div class="col">
                        <div class="card h-100 p-3">
                            <img src="<?=$itemData["image"];?>" class="card-img-top w-100" style="height: 280px;">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <?=$itemData["title"];?> 
                                    
                                    <?php
                                    $badges = [];
                                    if (array_key_exists("badges", $itemData)) {
                                        foreach($itemData["badges"] as $k => $v) {
                                            array_push($badges, '<span class="badge '.$v.'">'.$k.'</span>');
                                        }
                                    }
                                    echo " " . implode(" ", $badges);
                                    ?>

                                </h5>
                                <p class="card-text"><?=$itemData["description"];?></p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <h2 class="price fw-bold mb-0">
                                        <?=$response["currency_symbol"].number_format($itemData["price"]);?>
                                    </h2>
                                    <button type="button" class="btn btn-generic rounded-3 text-white px-4 py-2 <?=$itemData["available"] ? "" : "disabled";?>" <?=$itemData["available"] ? 'type="button" data-bs-toggle="modal" data-bs-target="#confirmModal" data-bs-item_id="'.$itemData["id"].'"' : '' ?> >
                                        <i class="fas fa-shopping-cart pe-1"></i> BUY NOW
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

            <?php
            }
            ?>

                </div>
            </section>

            <?php
            }
            ?>

            <section class="container mb-5 pt-5">
                <div class="d-flex justify-content-around align-items-center row row-cols-1 row-cols-md-1 row-cols-lg-2 g-4">
                    <div class="col-lg-4 order-2 order-lg-1 mb-3">
                        <div class="feature shadow d-flex flex-column flex-lg-row justify-content-around align-items-center mb-4 px-4 py-3 mx-auto">
                            <img class="pe-lg-3 pb-2 pb-lg-0" src="<?=$path;?>/assets/icons/image 12.png" alt="" style="width: 78px; height: 82px;">
                            <div class="text-lg-start text-center">
                                <h5>Regularly Updated</h5>
                                <p>The shop is regularly updated with exclusive limited time items available so be sure to check back occasionally!</p>
                            </div>
                        </div>
                        <div
                            class="feature shadow d-flex flex-column flex-lg-row justify-content-around align-items-center mb-4 px-4 py-3 mx-auto">
                            <img class="pe-lg-3 pb-2 pb-lg-0" src="<?=$path;?>/assets/icons/image 13.png" alt="" style="width: 79px; height: 76px;">
                            <div class="text-lg-start text-center">
                                <h5>Instant Delivery</h5>
                                <p>As soon as you checkout we will get your item to your account as fast as possible.</p>
                            </div>
                        </div>
                        <div
                            class="feature shadow d-flex flex-column flex-lg-row justify-content-around align-items-center mb-4 px-4 py-3 mx-auto">
                            <img class="pe-lg-3 pb-2 pb-lg-0" src="<?=$path;?>/assets/icons/image 14.png" alt="" style="width: 71px; height: 76px;">
                            <div class="text-lg-start text-center">
                                <h5>Staff Support</h5>
                                <p>All transactions are logged for support purposes. If you encounter any issues such as not receiving your item after purchase our staff will be happy to help!</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-6 order-1 order-lg-2 mb-3">
                        <img class="w-100" src="<?=$path;?>/assets/icons/XMLID 1.png" alt="">
                    </div>
                </div>

            </section>
        </main>

        <!--

            The following is the main "Are you sure?" modal which is presented to users once
            they click a BUY button. We should display the users current balance and then ask
            them clearly if they wish to purchase the item or not. If they click No we should
            just close the modal, whereas if they click yes we should send the form back to 
            this page so the purchase request can be sent to the API.

        -->
        <div class="modal fade" id="confirmModal" tabindex="-1" role="dialog" aria-labelledby="confirmModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmModalTitle">Are you sure?</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>       
                    <div class="modal-body" id="confirmModalBody"></div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Close</button>
                        <form method="POST">
                            <input id="confirmModalItemIDInput" type="hidden" name="item_id">
                            <button type="submit" class="btn btn-success">Purchase</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <footer>
            <p class="text-center">
                <small>Copyright <i class="far fa-copyright"></i> <a class="text-muted" href="https://github.com/morgverd">MorgVerd</a> 2021</small>
            </p>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
        <script>

            const CURRENCY_SYMBOL = <?=json_encode($response["currency_symbol"]);?>;
            const USER_BALANCE = <?=json_encode($response["user"]["balance"]);?>;
            const ITEMS_DATA = <?=json_encode($response["categories"]);?>;

            // With the corresponding item ID, we need to loop through all of
            // the categories and sub items to find the individual item data.
            function getItemFromID(item_id) {
                for (let c in ITEMS_DATA) {
                    for (let i in ITEMS_DATA[c]) {
                        if (ITEMS_DATA[c][i]["id"] == item_id) {
                            return ITEMS_DATA[c][i];
                        }
                    }
                }
                return null;
            }

            // This function takes in an item dictionary and then produces a string of
            // bootstrap badges with the respective title=>class structure.
            function constructBadgesHTML(item) {
                if (item["badges"] === undefined) { return ""; }
                let badgesString = "";
                for (let badgeText in item["badges"]) {
                    badgesString += (" <span class='badge " + item["badges"][badgeText] + "'>" + badgeText + "</" + "span>");
                }
                return badgesString;
            }

            // This function takes in an integer value and then formats it with commas. It
            // also adds the default currency symbol which is gathered from the API endpoint.
            function formatNumber(num) {
                return CURRENCY_SYMBOL + num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
            }

            const confirmModal = document.getElementById("confirmModal");
            confirmModal.addEventListener("show.bs.modal", function(event) {
                let item = getItemFromID(event.relatedTarget.getAttribute("data-bs-item_id"));                
                let balanceRemaining = USER_BALANCE - item.price;

                document.getElementById("confirmModalTitle").innerHTML = item.title + constructBadgesHTML(item);
                document.getElementById("confirmModalBody").innerHTML = "Are you sure you want to purchase this item for <code>" + formatNumber(item.price) + "</" + "code>? You will have <code>" + formatNumber(balanceRemaining) + "</" + "code> left afterwards.";
                document.getElementById("confirmModalItemIDInput").setAttribute("value", item.id);

            });

            // Here, we clear the window POST state. This is to stop the purchase form from
            // resubmitting each time the user tries to reload the page.
            if (window.history.replaceState) {
                window.history.replaceState(null, null, window.location.href);
            }

        </script>
    </body>
</html>