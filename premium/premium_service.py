from flask import Flask,jsonify,request,redirect,Response
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import time
import json
from crypt import validate_token,create_token
import requests

from postgres_client import  PostgresClient
from sql_consts import SQL_CONSTS
print('json is admin!')
credentials = ServiceAccountCredentials.from_json_keyfile_name('isee2.json')
service = build('androidpublisher','v3',credentials=credentials)
app = Flask(__name__)

#The routes config.

PREMIUM_ROUTES_COLUMN_NAME = {
    'analyze-user-fr/get_free_celebs_lookalike':'celebs_lookalike',
    'analyze-user-fr/get_traits':'traits',
    '/morph/free_perform':'morph',
    '/cartoonize/create_cartoon':'cartoon',
    'generate_image_to_image':'dream_from_image',
    #'generate_image_from_text':'dream_from_prompt',
    'generate_image_mask_to_image':'image_mask_to_image',#TODO add SQL columns from here
    'generate_image_from_face_image':'image_face_to_image',
    'dreambooth/post_request':'ai_avatars'
    #'generate_outpaint':'outpaint',
    #'image_captioning':'image_caption'

}

PREMIUM_ROUTES = list(PREMIUM_ROUTES_COLUMN_NAME.keys())

HAIFA_GENERATE_ROUTES = [
'generate_image',
    'generate_image_to_image',
'get_generated_image',
'upload_custom_dream_image',
    'generate_image_mask_to_image',
    'generate_outpaint',
    'generate_image_from_text',
    'generate_image_from_face_image'

]

HAIFA_LAVIS_ROUTES = ['image_captioning','image_question']

HAIFA_LAMA_ROUTES = ['remove_by_mask']

MAX_USAGE_PER_DAY = {
    'celebs_lookalike':4,
     'traits' : 4,
    'morph':4,
     'cartoon':4,
    'dream_from_image':12,
    'dream_from_prompt':12,
    'image_mask_to_image':6,
    'image_face_to_image':6,
    'ai_avatars':1

}


aurora_writer_host = 'voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'

app.config.aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_writer_host)

def route_is_premium(route):
    if any([x in route for x in PREMIUM_ROUTES]):
        return True
    return False

def get_key_for_premium_route(route):
    for premium_route,route_description in PREMIUM_ROUTES_COLUMN_NAME.items():
        if premium_route in route:
            return route_description
    return ''

def get_actual_host(url):

    if any([x in url for x in HAIFA_GENERATE_ROUTES]):
        url = url.replace(request.host, 'dordating.com:20004')
        return url

    if any([x in url for x in HAIFA_LAVIS_ROUTES]):
        url = url.replace(request.host, 'dordating.com:20005')
        return url
    if any([x in url for x in HAIFA_LAMA_ROUTES]):
        url = url.replace(request.host, 'dordating.com:20006')
        return url
    url = url.replace(request.host, 'services.voilaserver.com')
    return url

def should_allow(route_description,is_premium,user_history_in_route):
    '''

    :param route_description: The route's description
    :param is_premium:
    :param user_history_in_route: a list of times when the user used the route
    :return: a tuple (allow,data),allow being a boolean - whether to allow access, data is a dictionary of data to give the client (when was the last time, how many times per 24 hours etc)
    '''
    if is_premium: return True,{}
    last_24_hours = time.time() - 60*60*24
    user_history_in_route = [x for x in user_history_in_route if x>last_24_hours]
    user_history_in_route.sort()
    limits_current_route = MAX_USAGE_PER_DAY.get(route_description, 10)
    if len(user_history_in_route)<limits_current_route:
        allow = True
        next_usage = None
    else:
        allow = False
        next_usage = user_history_in_route[-limits_current_route] + 60*60*24
    return allow, {'next_usage':next_usage,'max_in_24_hours':limits_current_route,'actual_usage_24_hours':len(user_history_in_route)}


def verify_valid_apple_receipt(receipt_data):
    ISEE_APPLE_SHARED_SECRET = '24983c6c10194448ac590a7de4b2533a'

    APPLE_SANDBOX_VERIFICATION_URL = 'https://sandbox.itunes.apple.com/verifyReceipt'

    APPLE_PRODUCTION_VERIFICATION_URL = 'https://buy.itunes.apple.com/verifyReceipt'
    request_body = {

        'password': ISEE_APPLE_SHARED_SECRET,
        'receipt-data': receipt_data,
        'exclude-old-transactions': True

    }
    for apple_verify_url in [APPLE_SANDBOX_VERIFICATION_URL,APPLE_PRODUCTION_VERIFICATION_URL]:
        try:
            response = requests.post(url=apple_verify_url, json=request_body) #TODO there's a ton of information that can and should be saved from the response.
            if json.loads(response.content)['status']==0: #See https://developer.apple.com/documentation/appstorereceipts/responsebody - status ==0 is "ok and not expired", decide what information to take from response
                return True
        except:
            pass
    return False


@app.route('/isee/healthcheck', methods=['GET'])
def say_healthy():
    return jsonify({'status':'isee gateway is healthy'})


@app.route('/isee/delete_history')
def remove_user_history():
    user_id = request.headers.get('isee_user_id', 'no_user_id')
    new_user_data = {
        SQL_CONSTS.UsageColumns.USER_ID.value: user_id,
        SQL_CONSTS.UsageColumns.MORPH.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.TRAITS.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.CARTOON.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.DREAM_FROM_PROMPT.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.DREAM_FROM_IMAGE.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.CELEBS_LOOKALIKE.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.DREAM_FROM_MASK.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.DREAM_FROM_FACE.value: json.dumps([]),
        SQL_CONSTS.UsageColumns.AI_AVATARS.value : json.dumps([])
    }
    app.config.aurora_client.update_usage_data(new_user_data)
    return jsonify({'status':'success'})

@app.route('/create_token', methods=['POST']) #This endpoint is valid only for Android
def create_token_route():
    user_data = request.get_json(force = True)
    if True:
        if user_data.get('platform','android')=='android':
            #Check for the validity of the token. If invalid then return the reason
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
        elif user_data['platform']=='ios':
            purchase_token = user_data.get('purchase_token','no_purchase_token')
            subscription_id=user_data.get('subscriptionId','no_subscription_id_apple')
            valid = verify_valid_apple_receipt(receipt_data=purchase_token)
            if not valid:
                return jsonify({'token_status': 'invalid', 'reason': 'Apple token-TODO reason'})
            else:
                print('Apple token was receieved and approved')
        else:
            return jsonify({'status':'incorrect platform request'}) , 404
    expire_token_time = time.time()+60*60*23 #Let the client know the token will expire earlier than a day so he will try sooner to get a new token
    #Create and return iSee token
    subscription_id = user_data.get('subscriptionId', 'no_subscription_id') #TODO remove this line once done debugging
    iSee_token = create_token(subscription_id=subscription_id)
    return jsonify({'token_status':'valid','iSee_token':iSee_token,'expire_timestamp':expire_token_time*1000})


@app.route('/', defaults={'path': ''},methods=['POST','GET'])
@app.route('/<path:path>',methods=['POST','GET'])
def catch_all(path):
    #Calculate the host based on the path
    url = request.url
    url = get_actual_host(url=url)
    if 'https' not in url:
        url = url.replace('http','https')
    print(f"url is going to be {url}")
    if route_is_premium(url):
        user_id = request.headers.get('isee_user_id', 'no_user_id')
        valid_token = False
        token = request.headers.get('premium_token_header', '')
        if (token is not None and len(token) > 0):
            valid_token = validate_token(token)
        print(f'premium route, token valid is {valid_token}')
        current_time = int(time.time())
        relevant_route_key = get_key_for_premium_route(url)
        user_usage_data = app.config.aurora_client.get_usage_by_id(user_id=user_id)
        if user_usage_data is None or user_usage_data.get(relevant_route_key,None) is None:
            proposed_new_usage_times = [current_time]
        else:
            old_data = json.loads(user_usage_data[relevant_route_key])
            proposed_new_usage_times = old_data + [current_time]
        #TODO check here if proposed new usage times is in-line with current policy
        allow,limitation_data = should_allow(route_description=relevant_route_key,is_premium=valid_token,user_history_in_route=proposed_new_usage_times[:-1])
        if not allow:
            limitation_data.update({'status': 'used_daily_limit'})
            return jsonify(limitation_data),403
        new_user_data = {
            SQL_CONSTS.UsageColumns.USER_ID.value:user_id,
            relevant_route_key:json.dumps(proposed_new_usage_times)
                        }
        app.config.aurora_client.update_usage_data(new_user_data)
        #TODO calculate_usage_from_db(uid)
        #TODO if not premium and used too much, return a proper json with info such as next time the user can use the operation etc



    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,timeout=60)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    excluded_headers += [x.lower() for x in ["Connection","Keep - Alive","Proxy - Authenticate","Proxy - Authorization","TE",
    "Trailers","Transfer - Encoding","Upgrade"]
                         ]
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response






if __name__ == '__main__':
   app.run(threaded=True,port=20010,host="0.0.0.0",debug=False) #ssl_context=('/home/premium_service/keys/selfsigned.crt', '/home/premium_service/keys/selfsigned.key'))#('/home/premium_service/keys/dordating.crt', '/home/premium_service/keys/dordating.key'))
   