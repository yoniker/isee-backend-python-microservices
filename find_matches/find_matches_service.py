
import os
import psycopg2
from flask import Flask,jsonify,request
import time
import random
from postgres_client import PostgresClient
import numpy as np
import pickle
import json
from sql_consts import SQL_CONSTS
from server_consts import ServerConsts
import geopy
from functools import partial
import pandas as pd


app = Flask(__name__)


DUMMY_COLUMNS_TO_REAL_NAMES = {
    'pof_id':SQL_CONSTS.UsersColumns.FIREBASE_UID.value,
    'username':SQL_CONSTS.UsersColumns.NAME.value,
    'smoke':SQL_CONSTS.UsersColumns.SMOKING.value,
    'gender':SQL_CONSTS.UsersColumns.USER_GENDER.value,
    'height':SQL_CONSTS.UsersColumns.HEIGHT_IN_CM.value,
    'religion':SQL_CONSTS.UsersColumns.RELIGION.value,
    'zodiac':SQL_CONSTS.UsersColumns.ZODIAC.value,
    'college_id':SQL_CONSTS.UsersColumns.SCHOOL.value,
    'profession':SQL_CONSTS.UsersColumns.JOB_TITLE.value,
    'seekinga':SQL_CONSTS.UsersColumns.GENDER_PREFERRED.value,
    'searchtype':SQL_CONSTS.UsersColumns.RELATIONSHIP_TYPE.value,
    'drink':SQL_CONSTS.UsersColumns.DRINKING.value,
    'wantchildren':SQL_CONSTS.UsersColumns.CHILDREN.value,
    'description':SQL_CONSTS.UsersColumns.USER_DESCRIPTION.value,
    'body':SQL_CONSTS.UsersColumns.FITNESS.value,
    'searchtype':SQL_CONSTS.UsersColumns.RELATIONSHIP_TYPE.value
    
}

def pof_height_to_height_in_cm(height):
    try:
        
        return int(height[height.find('('):][1:-3])
    except:
        return None

def get_exact_distance(match,user_location):
    try:
        if any([x is None for x in user_location]): return None
        match_lat = match[SQL_CONSTS.UsersColumns.LATITUDE.value]
        match_lon = match[SQL_CONSTS.UsersColumns.LONGITUDE.value]
        match_location = (match_lat,match_lon)
        if any([x is None for x in match_location]): return None
        return geopy.distance.distance(user_location,match_location).km
    except:
        return None

aurora_reader_host = 'voila-aurora-cluster.cluster-ro-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'


connect_str_papush = f"dbname='dummy_users' user='yoni' host='192.116.48.67' " + \
                        "password='dor'"


aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_reader_host)
conn_papush = psycopg2.connect(connect_str_papush)

@app.route('/matches/perform_query_aws')
def perform_query_aws():
    #lat=40.71427000,lon=-74.00597000
    lat =  request.args.get('lat')
    lon = request.args.get('lon')
    radius = request.args.get('radius')
    max_age = request.args.get('max_age')
    min_age = request.args.get('min_age')
    gender_index = request.args.get('gender_index')
    uid = request.args.get('uid')
    limit = int(request.args.get('limit') or 100)
    need_fr_data = request.args.get('fr')=='true'
    t1 = time.time()
    result = aurora_client.get_matches(lat=lat,lon=lon,radius=radius,min_age=min_age,max_age=max_age,gender_index=gender_index,uid=uid,need_fr_data=need_fr_data,max_num_users=limit)
    t2 = time.time()
    if need_fr_data:
      result['fr_data'] = result.fr_data.transform(pickle.loads)
    t3 = time.time()
    return jsonify({'time querying db':t2-t1,'time making jsonifyable':t3-t2,'overall time':t3-t1})

@app.route('/matches/<uid>')
def get_user_matches(uid):
    user_settings = aurora_client.user_info(uid=uid)
    if len(user_settings)==0:
      return jsonify({'status':f'no user with uid {uid} was found'}),404
    lat = user_settings.get(SQL_CONSTS.UsersColumns.LATITUDE.value)
    lon = user_settings.get(SQL_CONSTS.UsersColumns.LONGITUDE.value)
    radius = user_settings.get(SQL_CONSTS.UsersColumns.RADIUS.value,50) #radius in kms
    max_age = user_settings.get(SQL_CONSTS.UsersColumns.MAX_AGE.value)
    min_age = user_settings.get(SQL_CONSTS.UsersColumns.MIN_AGE.value)
    gender_preferred = user_settings.get(SQL_CONSTS.UsersColumns.GENDER_PREFERRED,SQL_CONSTS.UsersPreferredGender.EVERYONE)
    if gender_preferred == SQL_CONSTS.UsersPreferredGender.WOMEN:
      gender_index = 0
    elif gender_preferred == SQL_CONSTS.UsersPreferredGender.MEN:
      gender_index = 1
    else:
      gender_index = None
    need_fr_data = request.args.get('fr')=='true' #TODO change this according to filter type
    limit = int(request.args.get('limit') or 100) #TODO change this according to filter type
    t1 = time.time()
    current_user_matches = aurora_client.get_dummy_matches(lat=lat,lon=lon,radium_in_kms=radius,min_age=min_age,max_age=max_age,gender_index=gender_index,uid=uid,need_fr_data=need_fr_data,max_num_users=limit)
    t2 = time.time()



    
    current_user_matches[SQL_CONSTS.UsersColumns.HEIGHT_IN_CM.value]= current_user_matches['height'].apply(pof_height_to_height_in_cm)
    current_user_matches['user_type'] = 'dummy'
    current_user_matches[SQL_CONSTS.UsersColumns.LOCATION_DESCRIPTION.value]=current_user_matches['city'].fillna('?')+','+current_user_matches['state_id'].fillna('?')
    current_user_matches.rename(columns=DUMMY_COLUMNS_TO_REAL_NAMES,inplace=True)
    current_user_matches.replace({np.nan: None}, inplace=True)
    current_user_matches.pets = current_user_matches.pets.apply(lambda x: json.dumps([x]) if x is not None and len(x)>0 else json.dumps(["No pets"])) #since pets expects a list of strings
    
    
    if need_fr_data:
      current_user_matches['fr_data'] = current_user_matches.fr_data.transform(pickle.loads)
      #TODO sort by fr vector here
    current_user_matches = current_user_matches.sample(min(ServerConsts.LIMITS.MAX_MATCHES_PER_USER_QUERY.value,len(current_user_matches)))
    if 'fr_data' in current_user_matches: #we don't want to save the embeddings in redis because 1.not serialable 2.memory
        current_user_matches.drop(columns=['fr_data'],inplace=True)
    if len(current_user_matches)>0:
        current_user_matches['location_distance'] = current_user_matches.apply(partial(get_exact_distance,user_location = (lat, lon)), axis=1)
    current_user_matches.drop(columns=['latitude','longitude'], inplace=True)
    current_user_matches = current_user_matches.where(pd.notnull(current_user_matches), None)
    if user_settings[SQL_CONSTS.UsersColumns.SHOW_DUMMY_PROFILES.value] == 'true':
        pass
        #current_user_matches = get_dummy_users_images(current_user_matches)
    current_user_matches = current_user_matches.to_dict(orient='records')
    t3 = time.time()
    return jsonify({'time querying db':t2-t1,'time making jsonifyable':t3-t2,'overall time':t3-t1,'matches':current_user_matches})


@app.route('/matches/healthcheck')
def say_healthy():
    return jsonify({'status':'matches service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20002,host="0.0.0.0",debug=False)

#docker build . -t find_matches:14

#docker run -d -p 20002:20002/tcp find_matches:6

#curl "localhost:20002/matches/perform_query_aws?lat=40.71&lon=-74.005&radius=40000&min_age=25&max_age=45&limit=2000&fr=true"


#http://shira.voilaserver.com/matches/perform_query_aws?lat=40.71&lon=-74.005&radius=40000&min_age=25&max_age=35&limit=10&fr=true

#http://shira.voilaserver.com/matches/no_join_query_aws?lat=40.71&lon=-74.105&radius=40000&min_age=25&max_age=35&limit=10

#psql -h voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com -U yoni dummy_users < users_fr_data2.dump

#curl "localhost:20002/matches/kRlw3NNKk5aavKfYEupXroBcfYp1"



'''


SELECT count(*) FROM dummy_users
  WHERE earth_box(ll_to_earth(40.71427000, -74.00597000), 50000) @> ll_to_earth(latitude, longitude) and age>20 and age<55 and not cast (pof_id as varchar)  in (select decidee_id from decisions where decider_id='kRlw3NNKk5aavKfYEupXroBcfYp1')

  curl "localhost:20002/matches/cO6wkLgrH4XUKClFqaJzrGKzNp53
'''