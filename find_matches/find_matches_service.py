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
import boto3
from multiprocessing.pool import ThreadPool

app = Flask(__name__)


FACE_RECOGNITION_THRESHOLDS = {'best':1.2,'good':1.24,'okish':1.262,'weak':1.278,'meh':1.3} #Thresholds I chose manually by going over some celebs data.


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

DUMMY_BUCKET = 'com.voiladating.dummy'
REAL_BUCKET = 'com.voiladating.users2'

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


def get_dummy_users_images(users):
   start_time = time.time()
   users_ids = [str(user[SQL_CONSTS.UsersColumns.FIREBASE_UID.value]) for user in users]
   images_data = app.config.aurora_client.get_dummy_users_images(users_ids = users_ids)
   for user in users:
    user_id = str(user[SQL_CONSTS.UsersColumns.FIREBASE_UID.value])
    user_images = [image_info[SQL_CONSTS.DummyUsersImagesColumns.FILENAME.value] for image_info in images_data if image_info[SQL_CONSTS.DummyUsersImagesColumns.USER_ID.value]==user_id]
    user_images.sort() #I could use priority as in real users but meh.
    user['images'] = [f'user_data/dummy/{user_id}/{user_image}' for user_image in user_images]
   
   print(f'It took {time.time()-start_time} to get users images')
   return users

def get_real_users_images(users):
    users_ids = [str(user[SQL_CONSTS.UsersColumns.FIREBASE_UID.value]) for user in users]
    images_data = app.config.aurora_client.get_users_profile_images(users_ids)
    for user in users:
      user_id = str(user[SQL_CONSTS.UsersColumns.FIREBASE_UID.value])
      user_images = [image_info for image_info in images_data if image_info[SQL_CONSTS.ImageColumns.USER_ID.value]==user_id]
      user_images.sort(key=lambda x:x[SQL_CONSTS.ImageColumns.PRIORITY.value])
      user_images = [f'user_data/profile_images/real/{user_image[SQL_CONSTS.ImageColumns.FILENAME.value]}' for user_image in user_images]
      user['images'] = user_images
    return users

#TODO make the following env variables
aurora_reader_host = 'voila-aurora-cluster.cluster-ro-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'


app.config.aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_reader_host)


def settings_require_face_recognition(user_settings):
  if user_settings.get(SQL_CONSTS.UsersColumns.FILTER_NAME.value,None) == SQL_CONSTS.FilterTypes.CELEB_IMAGE.value and len(user_settings.get(SQL_CONSTS.UsersColumns.CELEB_ID.value, '')) > 0:
    return True
  if user_settings.get(SQL_CONSTS.UsersColumns.FILTER_NAME.value,None) == SQL_CONSTS.FilterTypes.CUSTOM_IMAGE.value and len(user_settings.get(SQL_CONSTS.UsersColumns.FILTER_DISPLAY_IMAGE.value, '')) > 0:
    return True
  return False


def get_celeb_embeddings(celeb_name):
  embedding = pickle.loads(app.config.aurora_client.get_celeb_embeddings(celeb_name=celeb_name))
  return embedding

def filter_current_matches_by_embedding(embeddings,current_user_matches,threshold=FACE_RECOGNITION_THRESHOLDS['best'],max_users_to_check=2000):
   t0 = time.time()
   current_user_matches = current_user_matches.sample(min(len(current_user_matches),max_users_to_check))
   print(f'Filtering current user matches by face_recognition,filtering {len(current_user_matches)} matches')
   current_user_matches = current_user_matches[~current_user_matches.fr_data.isnull()]
   all_embeddings = np.stack(current_user_matches.fr_data,axis=0)
   distances = np.linalg.norm(embeddings - all_embeddings,axis=1)
   current_user_matches['fr_distance'] = distances
   current_user_matches = current_user_matches[current_user_matches.fr_distance < threshold]
   print(f'FINISHED APPLYING AI EMBEDDINGS FILTERS,IT TOOK {time.time()-t0} seconds!')   
   return current_user_matches

def get_custom_embeddings(custom_embedding_link):
  #example of a custom embedding link:
  #5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658413515.446852/0.jpg
  s3_dir = '/'.join(custom_embedding_link.split('/')[:-1]) #'5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658413515.446852'
  local_dir = os.path.join('/tmp',s3_dir)
  short_filename = custom_embedding_link.split('/')[-1] #0.jpg
  short_filename = '.'.join(short_filename.split('.')[:-1])+'.pickle' #0.pickle
  full_local_filename = os.path.join(local_dir,short_filename)
  full_s3_key = os.path.join(s3_dir,short_filename)
  os.makedirs(local_dir,exist_ok=True)
  s3 = boto3.client('s3')
  with open(full_local_filename, 'wb') as f:
    s3.download_fileobj(REAL_BUCKET, full_s3_key, f)
  with open(full_local_filename, 'rb') as handle:
    custom_embedding = pickle.load(handle)
  custom_embedding = custom_embedding.squeeze()
  os.remove(full_local_filename)
  return custom_embedding


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
    result = app.config.aurora_client.get_matches(lat=lat,lon=lon,radius=radius,min_age=min_age,max_age=max_age,gender_index=gender_index,uid=uid,need_fr_data=need_fr_data,max_num_users=limit)
    t2 = time.time()
    if need_fr_data:
      result['fr_data'] = result.fr_data.transform(pickle.loads)
    t3 = time.time()
    return jsonify({'time querying db':t2-t1,'time making jsonifyable':t3-t2,'overall time':t3-t1})

@app.route('/matches/<uid>')
def get_user_matches(uid):
    user_settings = app.config.aurora_client.user_info(uid=uid)
    if len(user_settings)==0:
      return jsonify({'status':f'no user with uid {uid} was found'}),404
    lat = user_settings.get(SQL_CONSTS.UsersColumns.LATITUDE.value)
    lon = user_settings.get(SQL_CONSTS.UsersColumns.LONGITUDE.value)
    search_distance_enabled = user_settings.get(SQL_CONSTS.UsersColumns.SEARCH_DISTANCE_ENABLED.value,SQL_CONSTS.UserRadiusEnabled.FALSE.value)
    if search_distance_enabled == SQL_CONSTS.UserRadiusEnabled.TRUE.value:
      radius = user_settings.get(SQL_CONSTS.UsersColumns.RADIUS.value,50) #radius in kms
    else:
      radius = None
    max_age = user_settings.get(SQL_CONSTS.UsersColumns.MAX_AGE.value)
    min_age = user_settings.get(SQL_CONSTS.UsersColumns.MIN_AGE.value)
    gender_preferred = user_settings.get(SQL_CONSTS.UsersColumns.GENDER_PREFERRED,SQL_CONSTS.UsersPreferredGender.EVERYONE)
    if gender_preferred == SQL_CONSTS.UsersPreferredGender.WOMEN:
      gender_index = 0
    elif gender_preferred == SQL_CONSTS.UsersPreferredGender.MEN:
      gender_index = 1
    else:
      gender_index = None
    need_fr_data = settings_require_face_recognition(user_settings=user_settings)
    if user_settings.get(SQL_CONSTS.UsersColumns.FILTER_NAME.value,'') == SQL_CONSTS.FilterTypes.TEXT_SEARCH.value and len(user_settings.get(SQL_CONSTS.UsersColumns.TEXT_SEARCH.value,''))>0:
      text_search = user_settings.get(SQL_CONSTS.UsersColumns.TEXT_SEARCH.value,'')
    else:
      text_search = ''

    limit = 2000 if need_fr_data else 20 #TODO move to server consts
    t1 = time.time()
    show_dummy_profiles = user_settings[SQL_CONSTS.UsersColumns.SHOW_DUMMY_PROFILES.value]=='true'
    if show_dummy_profiles:
      current_user_matches = app.config.aurora_client.get_dummy_matches(lat=lat,lon=lon,radium_in_kms=radius,min_age=min_age,max_age=max_age,gender_index=gender_index,uid=uid,need_fr_data=need_fr_data,text_search=text_search,max_num_users=limit)
      t2 = time.time()
      current_user_matches[SQL_CONSTS.UsersColumns.HEIGHT_IN_CM.value]= current_user_matches['height'].apply(pof_height_to_height_in_cm)
      current_user_matches['user_type'] = 'dummy'
      current_user_matches[SQL_CONSTS.UsersColumns.LOCATION_DESCRIPTION.value]=current_user_matches['city'].fillna('?')+','+current_user_matches['state_id'].fillna('?')
      current_user_matches.rename(columns=DUMMY_COLUMNS_TO_REAL_NAMES,inplace=True)
      current_user_matches.replace({np.nan: None}, inplace=True)
      current_user_matches.pets = current_user_matches.pets.apply(lambda x: json.dumps([x]) if x is not None and len(x)>0 else json.dumps(["No pets"])) #since pets expects a list of strings
    else: #real users
      print('Showing real users')
      current_user_matches = app.config.aurora_client.get_real_matches(lat=lat,lon=lon,radium_in_kms=radius,min_age=min_age,max_age=max_age,gender_index=gender_index,uid=uid,need_fr_data=need_fr_data,text_search=text_search,max_num_users=limit)
      t2 = time.time()
      current_user_matches.replace({np.nan: None}, inplace=True)
    if need_fr_data and show_dummy_profiles: #TODO implement real users fr_data
      current_user_matches['fr_data'] = current_user_matches.fr_data.transform(pickle.loads)
      #Let's sort by fr!
      search_embedding = None
      if user_settings.get(SQL_CONSTS.UsersColumns.FILTER_NAME.value,None) == SQL_CONSTS.FilterTypes.CELEB_IMAGE.value and len(user_settings.get(SQL_CONSTS.UsersColumns.CELEB_ID.value, '')) > 0:
        search_embedding = get_celeb_embeddings(celeb_name=user_settings.get(SQL_CONSTS.UsersColumns.CELEB_ID.value))
      if user_settings.get(SQL_CONSTS.UsersColumns.FILTER_NAME.value,None) == SQL_CONSTS.FilterTypes.CUSTOM_IMAGE.value and len(user_settings.get(SQL_CONSTS.UsersColumns.FILTER_DISPLAY_IMAGE.value, '')) > 0:
        search_embedding = get_custom_embeddings(custom_embedding_link=user_settings.get(SQL_CONSTS.UsersColumns.FILTER_DISPLAY_IMAGE.value))
      if search_embedding is None or len(search_embedding) ==0 : 
          return jsonify({'status':'embeddings not found'}) , 404
      current_user_matches = filter_current_matches_by_embedding(embeddings=search_embedding,current_user_matches=current_user_matches)
      
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
    if show_dummy_profiles:
      current_user_matches = get_dummy_users_images(current_user_matches)
    else:
      current_user_matches = get_real_users_images(current_user_matches)
    t3 = time.time()
    status = ServerConsts.MatchesStatus.FOUND.value if len(current_user_matches)>0 else ServerConsts.MatchesStatus.NOT_FOUND.value #TODO check for other statuses.
    return jsonify({'time querying db':t2-t1,'time making jsonifyable':t3-t2,'overall time':t3-t1,ServerConsts.MatchesDataNames.MATCHES.value:current_user_matches,
    ServerConsts.MatchesDataNames.STATUS.value: status})


@app.route('/matches/healthcheck')
def say_healthy():
    return jsonify({'status':'matches service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20002,host="0.0.0.0",debug=False)



'''

docker build . -t find_matches:latest

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 360816483914.dkr.ecr.us-east-1.amazonaws.com

docker tag find_matches:17 360816483914.dkr.ecr.us-east-1.amazonaws.com/find_matches:17
docker push 360816483914.dkr.ecr.us-east-1.amazonaws.com/find_matches:17

docker run -d -p -it 20002:20002/tcp find_matches:latest



docker run -d  -it -p20002:20002/tcp try

'''

#

#curl "localhost:20002/matches/perform_query_aws?lat=40.71&lon=-74.005&radius=40000&min_age=25&max_age=45&limit=2000&fr=true"


#http://services.voilaserver.com/matches/perform_query_aws?lat=40.71&lon=-74.005&radius=40000&min_age=25&max_age=35&limit=10&fr=true

#http://services.voilaserver.com/matches/no_join_query_aws?lat=40.71&lon=-74.105&radius=40000&min_age=25&max_age=35&limit=10

#psql -h voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com -U yoni dummy_users < users_fr_data2.dump

#PGPASSWORD=dordordor nohup psql -h voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com -U yoni dummy_users < dummy_users_images.dump &

#curl "localhost:20002/matches/5EX44AtZ5cXxW1O12G3tByRcC012"

#services.voilaserver.com/matches/5EX44AtZ5cXxW1O12G3tByRcC012

#psql -h voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com -U yoni dummy_users < celebs.dump

'''


SELECT count(*) FROM dummy_users
  WHERE earth_box(ll_to_earth(40.71427000, -74.00597000), 50000) @> ll_to_earth(latitude, longitude) and age>20 and age<55 and not cast (pof_id as varchar)  in (select decidee_id from decisions where decider_id='kRlw3NNKk5aavKfYEupXroBcfYp1')

  curl "localhost:20002/matches/kRlw3NNKk5aavKfYEupXroBcfYp1"
'''