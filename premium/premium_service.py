from flask import Flask,jsonify,request,redirect,Response
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import time
import json
from crypt import validate_token,create_token
import requests

credentials = ServiceAccountCredentials.from_json_keyfile_name('isee.json')
service = build('androidpublisher','v3',credentials=credentials)
app = Flask(__name__)


@app.route('/isee/healthcheck', methods=['GET'])
def say_healthy():
    return jsonify({'status':'isee gateway is healthy'})

@app.route('/isee/create_token', methods=['POST']) #This endpoint is valid only for Android
def create_token():
    user_data = request.get_json(force = True)
    purchase_token = user_data['purchase_token']
    subscription_id = user_data['subscriptionId']
    google_request = service.purchases().subscriptions().get(packageName='com.voiladating.FaceAnalyzer',subscriptionId=subscription_id, token=purchase_token)
    response = google_request.execute()
    #TODO in the future: save the response, which is just the user data
    #TODO should we acknoledge the purchase here?! https://developer.android.com/google/play/billing/integrate

    #validate the token
    #TODO refer to paymentState see the colab here https://codelabs.developers.google.com/codelabs/flutter-in-app-purchases#9
    if response.get('expiryTimeMillis', None) is None:
        return jsonify({'token_status':'invalid'})
    expiry_time = int(response['expiryTimeMillis'])
    token_expired = (time.time()-expiry_time/1000 > 0)
    if response.get('cancelReason',None) is not None and token_expired:
        return jsonify({'token_status': 'invalid','reason':'cancelled or updated'})
    if token_expired:
        return jsonify({'token_status':'expired'})

    expire_token_time = time.time()+60*2 #60*60*24
    #Create and return iSee token

    iSee_token = create_token(subscription_id=subscription_id,purchase_token=purchase_token)
    return jsonify({'token_status':'valid','iSee_token':iSee_token,'expire_timestamp':expire_token_time*1000})


@app.route('/', defaults={'path': ''},methods=['POST','GET'])
@app.route('/<path:path>',methods=['POST','GET'])
def catch_all(path):
    token = request.headers.get('premium_token_header','')
    if(token is not None and len(token)>0):
        print('Got some token, Going to verify it just for fun')
        valid = validate_token(token)
        print(f'token valid is {valid}')

    url = request.url.replace(request.host, 'services.voilaserver.com')
    if 'https' not in url:
        url = url.replace('http','https')
    print(f"url is going to be {url}")
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    excluded_headers += [x.lower() for x in ["Connection","Keep - Alive","Proxy - Authenticate","Proxy - Authorization","TE",
    "Trailers","Transfer - Encoding","Upgrade"]
                         ]
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response






if __name__ == '__main__':
   app.run(threaded=True,port=20010,host="0.0.0.0",debug=False)#,ssl_context=('/home/premium_service/keys/selfsigned.crt', '/home/premium_service/keys/selfsigned.key'))#('/home/premium_service/keys/dordating.crt', '/home/premium_service/keys/dordating.key'))