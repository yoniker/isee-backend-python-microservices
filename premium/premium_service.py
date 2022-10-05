from flask import Flask,jsonify,request,redirect,Response
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import time
import json
from crypt import validate_token,create_token
import requests
from postgres_client import  PostgresClient
from sql_consts import SQL_CONSTS

credentials = ServiceAccountCredentials.from_json_keyfile_name('isee.json')
service = build('androidpublisher','v3',credentials=credentials)
app = Flask(__name__)

#The routes config.

PREMIUM_ROUTES_COLUMN_NAME = {
    'analyze-user-fr/get_free_celebs_lookalike':'celebs_lookalike',
    'analyze-user-fr/get_traits':'traits',
    '/morph/free_perform':'morph',
    '/cartoonize/create_cartoon':'cartoon',
    'generate_image_to_image':'dream_from_image', #TODO change prompt generated image path such that it wont be a substring of dream
    'generate_image':'dream_from_prompt',

}

PREMIUM_ROUTES = list(PREMIUM_ROUTES_COLUMN_NAME.keys())

HAIFA_ROUTES = [
'generate_image',
    'generate_image_to_image',
'get_generated_image',
'upload_custom_dream_image'
]

MAX_USAGE_PER_DAY = {
    'celebs_lookalike':4,
     'traits' : 4,
    'morph':4,
     'cartoon':4,
    'dream_from_image':4,
    'dream_from_prompt':4,

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


def route_to_haifa(route):
    if any([x in route for x in HAIFA_ROUTES]):
        return True
    return False

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
    }
    app.config.aurora_client.update_usage_data(new_user_data)
    return jsonify({'status':'success'})

@app.route('/create_token', methods=['POST']) #This endpoint is valid only for Android
def create_token_route():
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
    #Calculate the host based on the path
    url = request.url
    if route_to_haifa(url):
        url = url.replace(request.host, 'dordating.com:20004')
    else:
        url = url.replace(request.host, 'services.voilaserver.com')
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
   app.run(threaded=True,port=20010,host="0.0.0.0",debug=False)#ssl_context=('/home/premium_service/keys/selfsigned.crt', '/home/premium_service/keys/selfsigned.key'))#('/home/premium_service/keys/dordating.crt', '/home/premium_service/keys/dordating.key'))