
import requests

fcm_token = 'fxBboLCYRZyOlHFtMRQZPC:APA91bHpcYnUOg7k9zVF2sSSvRunZgRgptwvOxHO648W1sCGUwX-RdInloNi7254eP1Gxf_3XSFyY3RNlF133m2jpAd9mxCBBYOagBlLoR2z9Pgf0bLzyDK2nXud8CtjqCjW2XJAen8d'
local_address = 'https://services.voilaserver.com/messaging/send_message'#'http://localhost:5000/messaging/send_message'

message = {
    "user_id":"dorrr",
    "fcm_token": fcm_token,
    "notification_title":"Avatars creation failed - we don't support training on just one image quite yet :D",
    "notification_body":"Avatars creation failed - we don't support training on just one image quite yet :D",

    "data":{
        "message":"fk yese from container"
    }
}


response = requests.post(url=local_address,json=message)