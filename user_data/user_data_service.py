import os
import psycopg2
import requests
from flask import Flask,jsonify,request,redirect
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
from datetime import datetime
import logging
from botocore.exceptions import ClientError
import os
from datetime import datetime
from image_utils import jsoned_image_to_image
import numpy as np
from srv_resolve import resolve_srv_addr
from dateutil.relativedelta import relativedelta
from functools import partial

def calculate_birthday_timestamp(birthday_text):
    if birthday_text is None or len(birthday_text) == 0:
        return None
    try:
        date = datetime.fromisoformat(birthday_text)
        return date.timestamp()
    
    except:
        return None


app = Flask(__name__)

DUMMY_BUCKET = 'com.voiladating.dummy'
REAL_BUCKET= 'com.voiladating.users2'
CELEBS_BUCKET = 'com.voiladating.celebs'



aurora_writer_host = 'voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'


app.config.aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_writer_host)
app.config.local_cache_dir = 'tmp/local_cache'
os.makedirs(app.config.local_cache_dir,exist_ok=True)

def generate_users_presigned_url(aws_key,bucket_name,expiresIn=60,region_name='us-east-1'):
    session = boto3.session.Session()
    s3_client = session.client('s3',region_name=region_name)
    return s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket_name, 'Key': aws_key},
        ExpiresIn=expiresIn)

def get_real_user_images(user_id):
    user_images_details = app.config.aurora_client.get_user_profile_images(user_id)
    user_images_links = ['user_data/profile_images/real/' + x['filename'] for x in user_images_details]
    return user_images_links


@app.route('/user_data/settings/<userid>', methods=['POST'])
def post_user_settings(userid):
    # TODO: check if userid matches the one in dict, add some security layer
    user_data = request.get_json(force = True)
    location_description = ''
    if user_data.get(SQL_CONSTS.UsersColumns.LATITUDE.value, 0.0) != 0.0 or user_data.get(
            SQL_CONSTS.UsersColumns.LONGITUDE.value, 0.0) != 0.0:
        lat = user_data.get(SQL_CONSTS.UsersColumns.LATITUDE.value, 0.0)
        lon = user_data.get(SQL_CONSTS.UsersColumns.LONGITUDE.value, 0.0)
        location_description = 'To be implemented at AWS' #app.config.geo_service.location_descrpition_by_coordinates(lat=lat,lon=lon,postgres_client=app.config.postgres_client)
        user_data[SQL_CONSTS.UsersColumns.LOCATION_DESCRIPTION.value] = location_description
    if user_data.get(SQL_CONSTS.UsersColumns.USER_BIRTHDAY.value, None) is not None and len(
            user_data[SQL_CONSTS.UsersColumns.USER_BIRTHDAY.value]) > 0:
        user_data[SQL_CONSTS.UsersColumns.USER_BIRTHDAY_TIMESTAMP.value] = calculate_birthday_timestamp(
            user_data[SQL_CONSTS.UsersColumns.USER_BIRTHDAY.value])
    app.config.aurora_client.update_user_data(user_data)
    return jsonify(
        {'status': 'success', SQL_CONSTS.UsersColumns.LOCATION_DESCRIPTION.value: location_description})


def upload_file_to_s3(file_name, bucket=REAL_BUCKET, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def custom_image_path(userid,imagename):
    return f'{userid}/custom_image/{imagename}'

@app.route('/user_data/upload_custom_image/<username>', methods=['POST'])
def upload_custom_face_image(username):
   try:
      imagefile = request.files.get('file', '')
      imagefile.save(imagefile.filename)
      upload_file_to_s3(file_name=imagefile.filename,bucket=REAL_BUCKET,object_name=custom_image_path(userid=username,imagename=imagefile.filename))

      #analyze_thread = threading.Thread(target=detecet_faces_img, args=(os.path.join(user_folder,imagefile.filename),))
      #analyze_thread.start() #TODO in general pytorch inference is thread-safe, but if many people will access at the same time there will be a mem issue https://discuss.pytorch.org/t/is-inference-thread-safe/88583
      return jsonify(success=True)
   except Exception as _:
      return jsonify(success=False)

@app.route('/user_data/analyze_custom_image/<user_id>/<image_name>')
def analyze_custom_face_image(user_id,image_name):
    s3_path = custom_image_path(userid=user_id,imagename=image_name)
    print(f's3_path is {s3_path}')
    t1 = time.time()
    address_correctly_resolved = False
    host = resolve_srv_addr("face-detection-service.microservices.local")
    if len(host)>0:
        address = f'http://{host}/analyze/froms3/{s3_path}?fr_data=True&display_images=True'
        address_correctly_resolved = True
    if not address_correctly_resolved:
        address = f'https://services.voilaserver.com/analyze/froms3/{s3_path}?fr_data=True&display_images=True'
    print(f'address resolved from srv is {address_correctly_resolved}')
    response = requests.get(address)
    #TODO something if response is not 200
    t2 = time.time()
    data = response.json()
    detections_data = data['detections_data'] #The keys for detections_data are ['display_images', 'detections', 'fr_data']
    location_to_save_analysis = os.path.join(os.path.dirname(s3_path),f'analysis{datetime.now().timestamp()}')
    local_location_save_images = os.path.join('/tmp',location_to_save_analysis)
    os.makedirs(local_location_save_images,exist_ok=True)
    
    for i, (display_image_data,fr_data) in enumerate(zip(detections_data['display_images'],detections_data['fr_data'])):
        print(f'at face number {i}')
        display_image = jsoned_image_to_image(display_image_data)
        display_image_filename = os.path.join(local_location_save_images,f'{i}.jpg')
        display_image.save(display_image_filename)
        upload_file_to_s3(file_name=display_image_filename,bucket=REAL_BUCKET,object_name=os.path.join(location_to_save_analysis,display_image_filename.split('/')[-1]))
        fr_data = np.array(fr_data)
        fr_filename = os.path.join(local_location_save_images,f'{i}.pickle')
        with open(fr_filename, 'wb') as handle:
            pickle.dump(fr_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        upload_file_to_s3(file_name=fr_filename,bucket=REAL_BUCKET,object_name=os.path.join(location_to_save_analysis,fr_filename.split('/')[-1]))
    t3 = time.time()
    display_images_links= [os.path.join(location_to_save_analysis,f'{i}.jpg') for i in range(len(detections_data['display_images']))]

    return jsonify({'display_images':display_images_links,'t3-t2':t3-t2,'t2-t1':t2-t1})


@app.route('/user_data/custom_face_search_image/<user_id>/custom_image/<analysis_directory_name>/<filename>')
def get_custom_face_image_url(user_id,analysis_directory_name,filename):
    #Get image links in the form of
    #5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg
    #and produce s3 links
    s3_client = boto3.client('s3')
    object_key = f'{user_id}/custom_image/{analysis_directory_name}/{filename}'
    print(f'object key is {object_key}')
    presigned_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': REAL_BUCKET, 'Key': object_key})
    print(f'redirect link is {presigned_url}')
    return redirect(presigned_url, code=302)
@app.route('/user_data/healthcheck')
def say_healthy():
    print('dor')
    return jsonify({'status':'user data service is up and running'})

@app.route('/user_data/celeb_image_links/<celebname>')
def get_celeb_image_links(celebname):
    res = app.config.aurora_client.get_celeb_images(celebname)
    files_names = [x['filename'] for x in res]
    celeb_image_links = [f'celeb_image/{celebname}/{x}' for x in files_names]
    return jsonify({'celeb_image_links':celeb_image_links})

@app.route('/user_data/celeb_image/<celeb_name>/<filename>')
def get_celeb_image_url(celeb_name,filename):
    #/celeb_image/Jackie Chan/1.jpeg
    s3_client = boto3.client('s3')
    object_key = f'{celeb_name}/{filename}'
    presigned_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': CELEBS_BUCKET, 'Key': object_key})
    return redirect(presigned_url, code=302)


@app.route('/user_data/profile_images/real/<user_id>/<filename>')
def redirect_to_aws_real(user_id,filename):
    aws_key = f'{user_id}/{filename}'
    url = generate_users_presigned_url(aws_key=aws_key,bucket_name=REAL_BUCKET,expiresIn=300)
    return redirect(url, code=302)

@app.route('/user_data/upload_profile_image/<user_id>',methods=['POST'])
def upload_profile_image(user_id):
    # TODO Auth
    full_file_uploaded_path = app.config.local_cache_dir + f"/{time.time()}_{user_id}_{random.randint(0,100000)}.jpg"
    short_filename = os.path.basename(full_file_uploaded_path)
    object_key = f'{user_id}/{short_filename}'
    request.files["file"].save(full_file_uploaded_path)
     #TODO verify file type,size etc
    # Step 1:Save the file in AWS in the proper location (<userid/filename.jpg>)
    upload_file_to_s3(full_file_uploaded_path, bucket=REAL_BUCKET, object_name=object_key)
    # Step 2:Save the file in the images SQL table with the appropriate index (transaction)
    upload_data= {SQL_CONSTS.ImageColumns.TYPE.value: 'in_profile',
    SQL_CONSTS.ImageColumns.BUCKET_NAME.value:REAL_BUCKET,
    SQL_CONSTS.ImageColumns.FILENAME.value:object_key,
    SQL_CONSTS.ImageColumns.USER_ID.value:user_id,
    }
    app.config.aurora_client.insert_new_image(upload_data=upload_data)
    # Step 3.Delete the file from local cache
    os.remove(full_file_uploaded_path)
    return jsonify({'status':'success','image_url':'profile_images/real/'+upload_data[SQL_CONSTS.ImageColumns.FILENAME.value]})


@app.route('/user_data/profile_images/get_urls/<user_id>',strict_slashes=False)
def get_user_image_urls(user_id):
    #TODO Auth
    user_images_details = app.config.aurora_client.get_user_profile_images(user_id=user_id)
    user_images_links = ['user_data/profile_images/real/'+x['filename'] for x in user_images_details]
    return jsonify(user_images_links)

#user_data/dummy/153367418/153367418.2.jpg
@app.route('/user_data/dummy/<user_id>/<filename>')
def redirect_to_aws_dummy(user_id,filename):
    aws_key = f'{user_id}/{filename}'
    url = generate_users_presigned_url(aws_key=aws_key,bucket_name=DUMMY_BUCKET,expiresIn=300,region_name='us-east-2')
    return redirect(url, code=302)

@app.route('/user_data/profile/<user_id>')
def get_user_profile(user_id): #TODO move this functionality to find_matches?
    #TODO auth
    user_data = app.config.aurora_client.get_user_profile(user_id=user_id)
    if len(user_data) == 0 :
        return jsonify({'status':'not_found'}),404
    user_images_links = get_real_user_images(user_id)
    user_data[SQL_CONSTS.ADDED_USER_COLUMNS.IMAGES.value] = user_images_links
    current_date = datetime.now()
    try:
        user_data[SQL_CONSTS.ADDED_USER_COLUMNS.AGE.value] = \
            partial(relativedelta, current_date)(datetime.fromtimestamp(user_data[SQL_CONSTS.UsersColumns.USER_BIRTHDAY_TIMESTAMP.value])).years
    except:
        pass
    return jsonify({'status':'found','user_data':user_data})

@app.route('/user_data/profile_image/<user_id>')
def get_profile_image(user_id):
    # TODO Auth
    user_images_details = app.config.aurora_client.get_user_profile_images(user_id=user_id)
    user_images_links = [x['filename'] for x in user_images_details]
    if len(user_images_links) == 0:
        return redirect_to_aws_real(aws_key='app_assets/anonymous_user.jpg')
    profile_image_url = user_images_links[0]
    return redirect_to_aws_real(aws_key=profile_image_url)

@app.route('/user_data/profile_images/swap/<user_id>',methods=['POST'])
def swap_profile_images(user_id):
    #TODO Auth
    profile_image_prefix = 'user_data/profile_images/real/'
    file1_key = request.get_json(force = True)['file1_url'][len(profile_image_prefix):]
    file2_key = request.get_json(force = True)['file2_url'][len(profile_image_prefix):]
    #TODO make sure the user is referring to his own files...
    app.config.aurora_client.swap_images_priorities(image1_key=file1_key,image2_key=file2_key)
    return jsonify({'status':'success'})

@app.route('/user_data/profile_images/delete/<user_id>',methods=['POST'])
def delete_profile_image(user_id):
    #TODO Auth
    profile_image_prefix = 'user_data/profile_images/real/'
    file_key = request.get_json(force = True)['file_url'][len(profile_image_prefix):]
    #TODO make sure that the user refers to his own files
    app.config.aurora_client.delete_image(image_key=file_key)
    #TODO in the future,remove it after some time from s3. For now keep it, to make other users experience better in case they already have the link to this image somewhere
    return jsonify({'status':'success'})

if __name__ == '__main__':
   app.run(threaded=True,port=20003,host="0.0.0.0",debug=False)



'''

docker build . -t user_data
docker run -d -it -p  20003:20003/tcp user_data:latest
curl "localhost:20003/user_data/celeb_image_links/Jackie Chan"
curl localhost:20003/user_data/custom_face_search_image/5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg
curl localhost:20003/user_data/analyze_custom_image/5EX44AtZ5cXxW1O12G3tByRcC012/name2.jpg
services.voilaserver.com/user_data/analyze_custom_image/5EX44AtZ5cXxW1O12G3tByRcC012/name2.jpg
aws s3 presign s3://com.voiladating.users2/5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg
'''

#

#curl "localhost:20002/matches/perform_query_aws?lat=40.71&lon=-74.005&radius=40000&min_age=25&max_age=45&limit=2000&fr=true"


#http://shira.voilaserver.com/matches/perform_query_aws?lat=40.71&lon=-74.005&radius=40000&min_age=25&max_age=35&limit=10&fr=true

#http://shira.voilaserver.com/matches/no_join_query_aws?lat=40.71&lon=-74.105&radius=40000&min_age=25&max_age=35&limit=10

#psql -h voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com -U yoni dummy_users < users_fr_data2.dump

#PGPASSWORD=dordordor nohup psql -h voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com -U yoni dummy_users < dummy_users_images.dump &

#curl "localhost:20002/matches/kRlw3NNKk5aavKfYEupXroBcfYp1"



'''


SELECT count(*) FROM dummy_users
  WHERE earth_box(ll_to_earth(40.71427000, -74.00597000), 50000) @> ll_to_earth(latitude, longitude) and age>20 and age<55 and not cast (pof_id as varchar)  in (select decidee_id from decisions where decider_id='kRlw3NNKk5aavKfYEupXroBcfYp1')

  curl "localhost:20002/matches/kRlw3NNKk5aavKfYEupXroBcfYp1"


5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg

working:
https://s3.amazonaws.com/com.voiladating.users2/5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg?AWSAccessKeyId=AKIAVIASWTZFO7GHDZF4&Signature=WnXnmBMxG5O96YM7JC9EBK4sj6c%3D&Expires=1658382580
not working:
https://s3.amazonaws.com/com.voiladating.users2/5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg?AWSAccessKeyId=AKIAVIASWTZFO7GHDZF4&amp;Signature=WnXnmBMxG5O96YM7JC9EBK4sj6c%3D&amp;Expires=1658382580

aws s3 sync s3://com.voiladating.dummy s3://com.voiladating.dummy2 --source-region us-east-2 --region us-east-1

'''
