from flask import Flask,jsonify,request,redirect
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import time
import json
from crypt import validate_token,encrypt

credentials = ServiceAccountCredentials.from_json_keyfile_name('isee.json')
service = build('androidpublisher','v3',credentials=credentials)
app = Flask(__name__)


@app.route('/create_token', methods=['POST']) #This endpoint is valid only for Android
def create_token():
    user_data = request.get_json(force = True)
    purchase_token = user_data['purchase_token']
    google_request = service.purchases().subscriptions().get(packageName='com.voiladating.FaceAnalyzer',subscriptionId='isee_monthly_17_sep_2022', token=purchase_token)
    response = google_request.execute()
    #TODO in the future: save the response, which is just the user data
    #TODO should we acknoledge the purchase here?! https://developer.android.com/google/play/billing/integrate

    #validate the token
    if response.get('cancelReason',None) is not None:
        return jsonify({'token_status': 'invalid','reason':'cancelled or updated'})
    if response.get('expiryTimeMillis', None) is None:
        return jsonify({'token_status':'invalid'})
    expiry_time = int(response['expiryTimeMillis'])
    if time.time()-expiry_time/1000 > 0:
        return jsonify({'token_status':'expired'})

    expire_token_time = time.time()+60*2 #60*60*24
    #Create and return iSee token
    iSee_data = {
        'expiry':expire_token_time, #expire in 24 hours
        'premium':True,
        'purchase_token':purchase_token
    }
    iSee_token = encrypt(iSee_data)
    return jsonify({'token_status':'valid','iSee_token':iSee_token,'expire_timestamp':expire_token_time*1000})




if __name__ == '__main__':
   app.run(threaded=True,port=20009,host="0.0.0.0",debug=False,ssl_context=('/home/premium_service/keys/dordating.crt', '/home/premium_service/keys/dordating.key'))