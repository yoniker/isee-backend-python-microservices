import json
import time
import firebase_admin
from firebase_admin import messaging,auth
import requests
from flask import Flask, jsonify,request
from srv_resolve import resolve_srv_addr
app = Flask(__name__)

RUNNING_ON_AWS = True
default_app = firebase_admin.initialize_app() #TODO find async way to send FCM messages
FIREBASE_PROJECT_ID = 'swiper-db2c5'



'''

a container implmenting sending a message to a phone (whether it is connected or not)

A sample message passed to the service:


{
    "user_id":"dorrr",
    "fcm_token": "d0HpVQdYK0rRjFV5i3nWPO:APA91bESMc7iqQrxtvAb2bT7Ruqh0twlGiU0ZEgISwbbUqQIe8CVCx9BMdYheVR3sffWk26p4UtuHF9ch3N9MfY8XUCyYPQwKpmqURgta3vXRGGaSOeBnC_6e_yyMHZ_HCJDbeZKQFEY",
    "notification_title":"Dor is king",
    "notification_body":"Dor is the only king",

    "data":{
        "message":"fk yese from container"
    }
}


fcm_token, notification_title and notification_body are optional.

The service will try to send a websocket message first. 

If not successful then it is going to send fcm message if fcm_token and title+body are provided






'''


def fcm_normalize_data(data:dict):
   data = dict(data) #So that it will not happen in-place
   for k in list(data.keys()):
      if type(data[k])!=str:
         data[k] = json.dumps(data[k])
   return data

def send_fcm_message(fcm_token, data, ignore_error=True,notification: messaging.Notification = None,):
   try:
    data = fcm_normalize_data(data)
    message = messaging.Message(data=data,token=fcm_token,notification=notification,apns=None)
    response = messaging.send(message)
    print(response)
    return response
   except Exception as e:
      if not ignore_error:
         raise e
       


@app.route('/messaging/send_message', methods=['POST'])
def send_user_message():
    message_sending_data  = request.get_json(force = True)
    user_id = message_sending_data.get('user_id')
    message_data = message_sending_data.get('data')
    fcm_token = message_sending_data.get('fcm_token')
    notification_title = message_sending_data.get('notification_title')
    notification_body = message_sending_data.get('notification_body')
    
    if user_id is None or len(user_id) ==0:
        return jsonify({"status":"message wasnt sent - no user_id provided"}),404
    try:
        print(f'trying to send ws message to {user_id}')
        address_correctly_resolved = False
        
        host = resolve_srv_addr("websockets.microservices.local")
        if len(host)>0:
            address = f'http://{host}/websockets/message_user/{user_id}'
            address_correctly_resolved = True
        if not address_correctly_resolved:
            print('Service address wasnt correctly resolved!')
            address = f'https://services.voilaserver.com/websockets/message_user/{user_id}'
        response = requests.post(address,json=message_data)
        print(f'response is {response}')
        message_was_sent = False
        try:
            result = response.json()
            if result['result'] == 'message_sent':
                message_was_sent = True
        except:
            pass
        
        if message_was_sent and False: #TODO remove this after sorting out websocket service 
            print('send websocket successful')
            return jsonify({'status':'ok'})
        if fcm_token is not None and len(fcm_token)>0:
            print('websocket failed and i have legit FCM data, sending fcm message..')
            if notification_title is not None and len(notification_title)>0:
                notification = messaging.Notification(title=notification_title,
                                                body=notification_body)
            else:
                notification = None
            send_fcm_message(fcm_token=fcm_token, data=message_data,
                             ignore_error=True, notification=notification)
            return jsonify({'status':'ok'})
    
    except Exception as e:
        raise e



@app.route('/messaging/healthcheck', methods=['GET'])
def say_healthy():
    return jsonify({'status':'messaging service is healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,threaded=True,debug=False)


'''
docker build . -t messaging_service

'''