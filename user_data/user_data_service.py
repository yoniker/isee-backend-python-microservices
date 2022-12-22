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
from firebase_admin import auth
import firebase_admin
import concurrent.futures
import requests
from collections import defaultdict
from PIL import Image

user_analyze_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)


FIREBASE_PROJECT_ID = 'swiper-db2c5'
default_app = firebase_admin.initialize_app()


def calculate_birthday_timestamp(birthday_text):
    if birthday_text is None or len(birthday_text) == 0:
        return None
    try:
        date = datetime.fromisoformat(birthday_text)
        return date.timestamp()
    
    except:
        return None


app = Flask(__name__)
app.url_map.strict_slashes = False

DUMMY_BUCKET = 'com.voiladating.dummy'
REAL_BUCKET= 'com.voiladating.users2'
ISEE_BUCKET = 'com.voiladating.isee'
CELEBS_BUCKET = 'com.voiladating.celebs'
FREE_CELEBS_BUCKET = 'free-celebs'



aurora_writer_host = 'voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'


app.config.aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_writer_host)
app.config.local_cache_dir = 'tmp/local_cache'
os.makedirs(app.config.local_cache_dir,exist_ok=True)


def generate_users_presigned_url(aws_key,bucket_name,expiresIn=300,region_name='us-east-1'):
    s3_client = boto3.client('s3', region_name=region_name)
    url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket_name, 'Key': aws_key},
        ExpiresIn=expiresIn)
    del s3_client
    return url

def get_real_user_images(user_id):
    user_images_details = app.config.aurora_client.get_user_profile_images(user_id)
    user_images_links = ['user_data/profile_images/real/' + x['filename'] for x in user_images_details]
    return user_images_links


def get_location_description(lat,lon):
    if lat is None or lon is None:
        return ''
    try:
        response = requests.get(url=f'https://services.voilaserver.com/geolocation/description_by_coordinates?lat={lat}&lon={lon}')
        data = response.json()
        return data['location_description']
    except:
        return ''

@app.route('/user_data/settings/<userid>', methods=['POST'])
def post_user_settings(userid):
    # TODO: check if userid matches the one in dict, add some security layer
    user_data = request.get_json(force = True)
    location_description = ''
    if user_data.get(SQL_CONSTS.UsersColumns.LATITUDE.value, 0.0) != 0.0 or user_data.get(
            SQL_CONSTS.UsersColumns.LONGITUDE.value, 0.0) != 0.0:
        lat = user_data.get(SQL_CONSTS.UsersColumns.LATITUDE.value, 0.0)
        lon = user_data.get(SQL_CONSTS.UsersColumns.LONGITUDE.value, 0.0)
        location_description = get_location_description(lat=lat,lon=lon) #app.config.geo_service.location_descrpition_by_coordinates(lat=lat,lon=lon,postgres_client=app.config.postgres_client)
        user_data[SQL_CONSTS.UsersColumns.LOCATION_DESCRIPTION.value] = location_description
    if user_data.get(SQL_CONSTS.UsersColumns.USER_BIRTHDAY.value, None) is not None and len(
            user_data[SQL_CONSTS.UsersColumns.USER_BIRTHDAY.value]) > 0:
        user_data[SQL_CONSTS.UsersColumns.USER_BIRTHDAY_TIMESTAMP.value] = calculate_birthday_timestamp(
            user_data[SQL_CONSTS.UsersColumns.USER_BIRTHDAY.value])
    if user_data.get(SQL_CONSTS.UsersColumns.USER_GENDER.value,'') == SQL_CONSTS.DummyUsersGender.MALE.value:
        user_data[SQL_CONSTS.UsersColumns.GENDER_INDEX.value] = 1
    elif user_data.get(SQL_CONSTS.UsersColumns.USER_GENDER.value,'') == SQL_CONSTS.DummyUsersGender.FEMALE.value:
        user_data[SQL_CONSTS.UsersColumns.GENDER_INDEX.value] = 0
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

def download_file_from_s3(filename,object_name,bucket=ISEE_BUCKET):
    try:
        s3 = boto3.client('s3')
        with open(filename, 'wb') as f:
            s3.download_fileobj(bucket, object_name, f)
            return True
    except:
        return False
def delete_from_s3(bucket=ISEE_BUCKET, object_key=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_key: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.delete_object(Bucket=bucket, Key=object_key)
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
    presigned_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': REAL_BUCKET, 'Key': object_key})
    return redirect(presigned_url, code=302)
@app.route('/user_data/healthcheck')
def say_healthy():
    return jsonify({'status':'user data service is up and running'})

@app.route('/user_data/celeb_image_links/<celebname>')
def get_celeb_image_links(celebname):
    res = app.config.aurora_client.get_celeb_images(celebname)
    files_names = [x['filename'] for x in res]
    celeb_image_links = [f'celeb_image/{celebname}/{x}' for x in files_names]
    return jsonify({'celeb_image_links':celeb_image_links})
@app.route('/user_data/free_celeb_image_links/<celebname>')
def get_free_celeb_image_links(celebname):
    res = app.config.aurora_client.get_free_celeb_images(celebname)
    files_names = [x['filename'] for x in res]
    celeb_image_links = [f'free_celeb_image/{celebname}/{x}' for x in files_names]
    return jsonify({'celeb_image_links':celeb_image_links})



@app.route('/user_data/celeb_image/<celeb_name>/<filename>')
def get_celeb_image_url(celeb_name,filename):
    #/celeb_image/Jackie Chan/1.jpeg
    s3_client = boto3.client('s3')
    object_key = f'{celeb_name}/{filename}'
    presigned_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': CELEBS_BUCKET, 'Key': object_key})
    return redirect(presigned_url, code=302)

@app.route('/user_data/free_celeb_image/<celeb_name>/<filename>')
def get_free_celeb_image_url(celeb_name,filename):
    #/celeb_image/Jackie Chan/1.jpeg
    s3_client = boto3.client('s3')
    object_key = f'{celeb_name}/{filename}'
    presigned_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': FREE_CELEBS_BUCKET, 'Key': object_key})
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
    user_analyze_pool.submit(requests.get,f'https://services.voilaserver.com/analyze-user-fr/perform_analysis/{user_id}')
    return jsonify({'status':'success','image_url':'user_data/profile_images/real/'+upload_data[SQL_CONSTS.ImageColumns.FILENAME.value]})



@app.route('/user_data/profile_images/get_urls/<user_id>')
def get_user_image_urls(user_id):
    #TODO Auth
    user_images_details = app.config.aurora_client.get_user_profile_images(user_id=user_id)
    user_images_links = ['user_data/profile_images/real/'+x['filename'] for x in user_images_details]
    return jsonify(user_images_links)

"""
In this section there will be the functions which are specific only to iSee
"""
@app.route('/user_data/copy_gallery_image/<user_id>',methods=['POST'])
def copy_files_within_gallery(user_id):
    file1_url = request.get_json(force=True)['from_link']
    request_body = request.get_json(force=True)
    to_gallery_name = request_body.get('to_gallery','dream')
    creation_title = request_body.get('creation_title','')
    creation_prompt = request_body.get('creation_prompt','')
    creation_artist = request_body.get('creation_artist','')
    creation_timestamp = float(request_body.get('creation_timestamp',time.time()))

    file1_key = gallery_url_to_file_key(url_to_full_gallery_url(file1_url,user_id=user_id))
    #TODO 1.Download from s3. 2.Upload to s3 3.add the new file to the database
    user_id_by_path,gallery_name,filename = file1_key.split('/')
    full_from_file_local_path = app.config.local_cache_dir + f"{user_id}/{gallery_name}/{filename}"
    if not os.path.isfile(full_from_file_local_path):
        os.makedirs(os.path.dirname(full_from_file_local_path),exist_ok=True)
        download_file_from_s3(filename=full_from_file_local_path,object_name=file1_key,bucket=ISEE_BUCKET)
    file2_key = f'{user_id}/{to_gallery_name}/{filename}'
    upload_file_to_s3(full_from_file_local_path, bucket=ISEE_BUCKET, object_name=file2_key)
    # Step 2:Save the file in the images SQL table with the appropriate index (transaction)
    upload_data = {SQL_CONSTS.GalleryColumns.TYPE.value: to_gallery_name,
                   SQL_CONSTS.GalleryColumns.BUCKET_NAME.value: ISEE_BUCKET,
                   SQL_CONSTS.GalleryColumns.FILENAME.value: file2_key,
                   SQL_CONSTS.GalleryColumns.USER_ID.value: user_id,
                   SQL_CONSTS.GalleryColumns.CREATION_TITLE.value: creation_title,
                   SQL_CONSTS.GalleryColumns.CREATION_ARTIST.value: creation_artist,
                   SQL_CONSTS.GalleryColumns.CREATION_PROMPT.value : creation_prompt,
                   SQL_CONSTS.GalleryColumns.CREATION_TIMESTAMP.value : creation_timestamp,

                   }
    app.config.aurora_client.insert_new_gallery_image(upload_data = upload_data)
    return jsonify({'status':'success','debug url':file2_key})



@app.route('/user_data/upload_isee_gallery/<user_id>',methods=['POST'])
def upload_gallery_image(user_id):
    # TODO Auth
    args = request.args
    gallery_type = args.get('album_type', default='gallery')
    request_body = request.get_json(force=True)
    creation_title = request_body.get('creation_title','')
    creation_prompt = request_body.get('creation_prompt', '')
    creation_artist = request_body.get('creation_artist','')
    creation_timestamp = float(request_body.get('creation_timestamp',time.time()))
    file_extension = request.files["file"].filename.split('.')[-1]
    file_extension = 'jpg' if file_extension!='gif' else 'gif' #TODO support more file extensions?
    full_file_uploaded_path = app.config.local_cache_dir + f"/{time.time()}_{user_id}_{random.randint(0,100000)}.{file_extension}"
    short_filename = os.path.basename(full_file_uploaded_path)
    object_key = f'{user_id}/{gallery_type}/{short_filename}'
    request.files["file"].save(full_file_uploaded_path)
    if file_extension == 'jpg':
        try:
            print('going to try and save with PIL')
            raw_image = Image.open(full_file_uploaded_path)
            raw_image.save(full_file_uploaded_path) #The format is determined from file extension
        except:
            return jsonify({'status':'couldnt read data as image file'}) ,400
     #TODO verify file type,size etc
    # Step 1:Save the file in AWS in the proper location (<userid/filename.jpg>)
    upload_file_to_s3(full_file_uploaded_path, bucket=ISEE_BUCKET, object_name=object_key)
    # Step 2:Save the file in the images SQL table with the appropriate index (transaction)
    upload_data= {SQL_CONSTS.GalleryColumns.TYPE.value: gallery_type,
    SQL_CONSTS.GalleryColumns.BUCKET_NAME.value:ISEE_BUCKET,
    SQL_CONSTS.GalleryColumns.FILENAME.value:object_key,
    SQL_CONSTS.GalleryColumns.USER_ID.value:user_id,
    SQL_CONSTS.GalleryColumns.CREATION_PROMPT.value : creation_prompt,
    SQL_CONSTS.GalleryColumns.CREATION_ARTIST.value : creation_artist,
    SQL_CONSTS.GalleryColumns.CREATION_TITLE.value : creation_title,
    SQL_CONSTS.GalleryColumns.CREATION_TIMESTAMP:creation_timestamp
    }
    app.config.aurora_client.insert_new_gallery_image(upload_data=upload_data)
    # Step 3.Delete the file from local cache
    os.remove(full_file_uploaded_path)
    return jsonify({'status':'success','image_url':f'user_data/gallery_images/'+upload_data[SQL_CONSTS.GalleryColumns.FILENAME.value]})

@app.route('/user_data/gallery_images/<user_id>/<gallery_type>/<filename>')
def redirect_gallery_to_aws(user_id,gallery_type,filename):
    aws_key = f'{user_id}/{gallery_type}/{filename}'
    url = generate_users_presigned_url(aws_key=aws_key,bucket_name=ISEE_BUCKET,expiresIn=300)
    return redirect(url, code=302)

@app.route('/user_data/gallery_images/get_urls/<user_id>')
def get_user_gallery_image_urls(user_id):
    user_images_details = app.config.aurora_client.get_user_gallery_images(user_id=user_id)
    links_by_gallery = defaultdict(list)
    for user_image_details in user_images_details:
        links_by_gallery[user_image_details[SQL_CONSTS.GalleryColumns.TYPE.value]].append('user_data/gallery_images/'+user_image_details['filename'])
    links_by_gallery = dict(links_by_gallery)
    return jsonify(links_by_gallery)

@app.route('/user_data/gallery_images/get_shared_urls')
def get_shared_gallery_images():
    def translate_gallery_dict(gallery_dict):
        del gallery_dict[SQL_CONSTS.GalleryColumns.BUCKET_NAME]
        gallery_dict['gallery_shortlink'] = gallery_dict.pop(SQL_CONSTS.GalleryColumns.FILENAME.value)
        gallery_dict['gallery_name'] = gallery_dict.pop(SQL_CONSTS.GalleryColumns.TYPE.value)

    user_images_details = app.config.aurora_client.get_user_gallery_images(user_id='analyse_me_shared')
    for user_image_details in user_images_details:
        translate_gallery_dict(gallery_dict=user_image_details)
    return jsonify(user_images_details)

def url_to_full_gallery_url(url,user_id):
    if '/' not in url:
        url = f'user_data/gallery_images/{user_id}/dream/{url}'
    return url

def gallery_url_to_file_key(url):
    gallery_image_prefix = 'user_data/gallery_images/'
    file_key = url[len(gallery_image_prefix):]
    file_key = file_key.split('?')[0] #This is because the client sent url with args
    return file_key


@app.route('/user_data/gallery_images/delete/<user_id>',methods=['POST'])
def delete_gallery_image(user_id):
    #a typical url is user_data/gallery_images/analyse_me_d678f8d79aa52b93bd95c83f1615b3d4bd008261198fb40898b420bf4f2ebfc0/DreamArt/1668280908.5454662_analyse_me_d678f8d79aa52b93bd95c83f1615b3d4bd008261198fb40898b420bf4f2ebfc0_71517.jpg
    #TODO Auth

    url = request.get_json(force = True)['file_url']
    url = url_to_full_gallery_url(url,user_id=user_id)
    file_key = gallery_url_to_file_key(url)
    #file key now is <user id>/<gallery name>/<file name>
    app.config.aurora_client.delete_gallery_image(image_key=file_key,user_id=user_id)
    delete_from_s3(bucket=ISEE_BUCKET,object_key=file_key)
    return jsonify({'status':'success'})

#user_data/dummy/153367418/153367418.2.jpg
@app.route('/user_data/dummy/<user_id>/<filename>')
def redirect_to_aws_dummy(user_id,filename):
    aws_key = f'{user_id}/{filename}'
    url = generate_users_presigned_url(aws_key=aws_key, bucket_name=DUMMY_BUCKET, expiresIn=300, region_name='us-east-2')
    return redirect(url, code=302)

@app.route('/user_data/profile/<user_id>')
def get_user_profile(user_id): #TODO move this functionality to find_matches?
    #TODO auth
    user_data = app.config.aurora_client.get_user_by_id(user_id=user_id)
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
        return redirect_to_aws_real(user_id='app_assets',filename= 'anonymous_user.jpg')
    profile_image_url = user_images_links[0]
    username,filename = profile_image_url.split('/')
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
    app.config.aurora_client.delete_profile_image(image_key=file_key)
    #TODO in the future,remove it after some time from s3. For now keep it, to make other users experience better in case they already have the link to this image somewhere
    user_analyze_pool.submit(requests.get,
                             f'https://services.voilaserver.com/analyze-user-fr/perform_analysis/{user_id}')
    return jsonify({'status':'success'})


def send_message(user_id,data,fcm_token=None,notification_title=None,notification_body=None):
    
        requests.post(url='https://services.voilaserver.com/messaging/send_message',json=
        {
            'user_id':user_id,
            'fcm_token':fcm_token,
            'notification_title':notification_title,
            'notification_body':notification_body,
            'data': data


        })


def update_match(user_id1,user_id2,match_new_status,silent_update_on_match = False):
    current_time = time.time()
    match_data = {
        SQL_CONSTS.MatchColumns.TIMESTAMP_CREATED.value: current_time,
        SQL_CONSTS.MatchColumns.TIMESTAMP_CHANGED.value: current_time,
        SQL_CONSTS.MatchColumns.ID_USER1.value: user_id1,
        SQL_CONSTS.MatchColumns.ID_USER2.value: user_id2,
        SQL_CONSTS.MatchColumns.STATUS.value: match_new_status,
    }
    app.config.aurora_client.update_match(match_data=match_data)
    user1 = app.config.aurora_client.get_user_by_id(user_id=user_id1)
    user2 = app.config.aurora_client.get_user_by_id(user_id=user_id2)
    if match_new_status == SQL_CONSTS.MatchConsts.ACTIVE_MATCH.value:  # It's a new match
        data = {'push_notification_type': 'new_match' if not silent_update_on_match else 'silent_new_match'}
        send_notification = not silent_update_on_match
    else:
        data = {'push_notification_type': 'match_info'}
        send_notification = False
    for user in [user1,user2]:
        if user==user1:
            other_user_id = user2[SQL_CONSTS.UsersColumns.FIREBASE_UID.value]
            other_user_name = user2[SQL_CONSTS.UsersColumns.NAME.value]
        else:
            other_user_id = user1[SQL_CONSTS.UsersColumns.FIREBASE_UID.value]
            other_user_name = user1[SQL_CONSTS.UsersColumns.NAME.value]
        data['user_id'] = other_user_id
        fcm_token = user[SQL_CONSTS.UsersColumns.FCM_TOKEN.value]
        user_id = user[SQL_CONSTS.UsersColumns.FIREBASE_UID.value]
        send_message(user_id=user_id,fcm_token=fcm_token,
        notification_title="You have a new match!!" if send_notification else None,
        notification_body=f"You got matched with {other_user_name}!" if send_notification else None,
        data=data)



def remove_likes(user_id1,user_id2):
    current_time = time.time()
    for users in [(user_id1,user_id2),(user_id2,user_id1)]:
        u1,u2 = users
        unlike_data = {
            SQL_CONSTS.DecisionsColumns.DECIDER_ID.value:u1,
            SQL_CONSTS.DecisionsColumns.DECIDEE_ID.value:u2,
            SQL_CONSTS.DecisionsColumns.DECISION.value: SQL_CONSTS.DecisionsTypes.UNMATCHED.value,
            SQL_CONSTS.DecisionsColumns.DECISION_TIMESTAMP.value:current_time,
            
        }
        app.config.aurora_client.update_decisions(unlike_data)

@app.route('/user_data/match/<user_id1>/<user_id2>',methods=['GET'])
def match_users(user_id1,user_id2): #TODO remove from app api?
    #TODO auth
    update_match(user_id1=user_id1, user_id2=user_id2,
        match_new_status=SQL_CONSTS.MatchConsts.ACTIVE_MATCH.value)
    return jsonify({'result': 'success', 'action': 'match'})

@app.route('/user_data/unmatch/<user_id1>/<user_id2>',methods=['GET'])
def unmatch_users(user_id1,user_id2):
    remove_likes(user_id1, user_id2)
    update_match(user_id1=user_id1, user_id2=user_id2,
        match_new_status=SQL_CONSTS.MatchConsts.CANCELLED_MATCH.value)
    return jsonify({'result': 'success', 'action': 'unmatch'})
@app.route('/user_data/silent_match/<user_id1>/<user_id2>',methods=['GET'])
def silent_match_users(user_id1,user_id2):
    #TODO auth
    #TODO check that one of the uids are of an admin
    update_match(user_id1=user_id1, user_id2=user_id2,
        match_new_status=SQL_CONSTS.MatchConsts.ACTIVE_MATCH.value,silent_update_on_match=True)
    return jsonify({'result': 'success', 'action': 'match'})

@app.route('/user_data/decision/<userid>',methods=['POST'])
def post_user_decision(userid):
    #TODO Auth
    #TODO make sure that decision_data's decider is the same as the one at userid's decider
    decision_data = request.get_json(force=True)
    decision_data.update({SQL_CONSTS.DecisionsColumns.DECISION_TIMESTAMP:time.time()})
    app.config.aurora_client.post_decision(decision_data)
    #TODO if the decision was like, and decidee already liked the user,it's a match so create a match
    decision = decision_data.get(SQL_CONSTS.DecisionsColumns.DECISION.value,SQL_CONSTS.DecisionsTypes.NOPE.value)
    other_user_id = decision_data.get(SQL_CONSTS.DecisionsColumns.DECIDEE_ID.value,'id_didnt_exist_in_dict')
    if decision in [SQL_CONSTS.DecisionsTypes.LIKE.value,SQL_CONSTS.DecisionsTypes.SUPERLIKE.value]:
        other_user_decision = app.config.aurora_client.get_decision(decider=other_user_id,decidee = userid)
        if other_user_decision is not None and other_user_decision.get(SQL_CONSTS.DecisionsColumns.DECISION,SQL_CONSTS.DecisionsTypes.NOPE.value) in [SQL_CONSTS.DecisionsTypes.LIKE.value,SQL_CONSTS.DecisionsTypes.SUPERLIKE.value]:
            match_users(user_id1=userid,user_id2=other_user_id)
    return jsonify({'status':'success'})

@app.route('/user_data/clear_likes/<userid>')
def clear_likes(userid): #TODO this was done to facilitate development,remove at production
    #TODO auth
    app.config.aurora_client.clear_user_choices(user_id = userid)
    return jsonify({'status': 'success'})



def post_message(conversation_id, creator_id, content,sender_epoch_time):
   '''
   Post a new message in conversation id. Assumes that the conversation was previously created
   :param conversation_id:
   :param creator_id:
   :param content: The json content of the message. For example: {type:text,content:'Hi there!'}
   :return:
   '''
   message_users_data = app.config.aurora_client.post_message(conversation_id, creator_id, content,sender_epoch_time = sender_epoch_time,created_date=time.time(),status='created')
   users_in_chat_details = message_users_data['users_in_conversation']
   message_details = dict(message_users_data['message_details'])
   message_details['push_notification_type'] = 'new_message'
   sender_details = app.config.aurora_client.get_user_by_id(creator_id)
   for user_to_notify in users_in_chat_details:
      if user_to_notify[SQL_CONSTS.UsersColumns.FIREBASE_UID.value] != sender_details[SQL_CONSTS.UsersColumns.FIREBASE_UID.value]:
         #It's a different participant than the notified user, so send with sender details
         data = dict(message_details)
         data.update({'sender_details':json.dumps(sender_details)})
         send_message(user_id=user_to_notify[SQL_CONSTS.UsersColumns.FIREBASE_UID.value],
         fcm_token=user_to_notify[SQL_CONSTS.UsersColumns.FCM_TOKEN.value], 
         data=data,
         notification_title="You have a new message!",
         notification_body=f"{sender_details[SQL_CONSTS.UsersColumns.NAME]} sent you a new message!")
      else:
         data = dict(message_details)
         send_message(user_id=user_to_notify[SQL_CONSTS.UsersColumns.FIREBASE_UID.value],
                               fcm_token=user_to_notify[SQL_CONSTS.UsersColumns.FCM_TOKEN.value],
                                     data=data)
   return jsonify({'result': 'success'})


@app.route('/user_data/send_message/<user_id>', methods=['POST'])
def start_conversation(user_id,message_data=None):
    # TODO: check if userid matches the one in dict, add some security layer
    message_data = request.get_json(force=True) if message_data is None else message_data
    other_user_id = message_data['other_user_id']
    message_content = message_data['message_content']
    sender_epoch_time = message_data['sender_epoch_time']
    # TODO: Check if the chat already exist. Create the chat if it doesnt exist.
    # TODO and anyways return the conversation id.
    # TODO make sure the user has credentials
    conversation_id = app.config.aurora_client.create_conversation(user_id, other_user_id)
    post_message(conversation_id=conversation_id, creator_id=user_id, content=message_content,
                       sender_epoch_time=sender_epoch_time)
    return jsonify({'result': 'success'})


@app.route('/user_data/sync/<userid>/<timestamp>', methods=['GET'])
def get_all_messages(userid, timestamp):

    relevant_messages = app.config.aurora_client.get_all_user_messages_by_timeline(userid=userid, timestamp=timestamp)
    relevant_messages_dict = {relevant_message[SQL_CONSTS.MessagesColumns.MESSAGE_ID.value]: relevant_message for
                                relevant_message in relevant_messages}
    print(f'relevant messages at SQL are {relevant_messages}')
    relevant_receipts = app.config.aurora_client.get_all_user_receipts_by_timeline(userid=userid, timestamp=timestamp)
    for relevant_receipt in relevant_receipts:
        message_id = relevant_receipt[SQL_CONSTS.ReceiptColumns.MESSAGE_ID]
        if message_id not in relevant_messages_dict:  # The message was not changed but there's a receipt. For now put all the info in the dict anyways
            relevant_messages_dict[message_id] = dict(relevant_receipt)  # make a copy
            del relevant_messages_dict[message_id][SQL_CONSTS.ReceiptColumns.SENT_TS]
            del relevant_messages_dict[message_id][SQL_CONSTS.ReceiptColumns.READ_TS]
        if 'receipts' not in relevant_messages_dict[message_id]:
            relevant_messages_dict[message_id]['receipts'] = []
        relevant_messages_dict[message_id]['receipts'].append(relevant_receipt)
    relevant_matches_changes = app.config.aurora_client.get_matches_by_timeline(userid=userid,timestamp=timestamp)
    data = {'messages_data': list(relevant_messages_dict.values()), 'matches_data': relevant_matches_changes}

    print(f'SYNC Going to send {data}')
    return jsonify(data)

@app.route('/user_data/mark_conversation_read/<userid>/<conversation_id>', methods=['GET'])
def mark_conversation_read(userid, conversation_id):
    receipts_changed = app.config.aurora_client.mark_conersation_read(userid, conversation_id, time.time())
    if receipts_changed > 0:
        users_to_notify = app.config.aurora_client.get_users_by_conversation(conversation_id)
        data = {'push_notification_type': 'new_read_receipt'}  # TODO add more data here if and when needed...
        for user_to_notify in users_to_notify:
            send_message(
                user_id=user_to_notify[SQL_CONSTS.UsersColumns.FIREBASE_UID.value],
                fcm_token=user_to_notify[SQL_CONSTS.UsersColumns.FCM_TOKEN.value],
                data=data)
    return jsonify({'result': 'success'})

def handle_token(decoded_token,ignore_if_registered:bool):
    uid = decoded_token['uid']  # TODO something with the user's information
    if decoded_token['aud'] != FIREBASE_PROJECT_ID:
        print('wrong aud(audience=project id)')
        return jsonify({'status': 'bad project id'})
    
    data_from_token = {}
    data_from_token[SQL_CONSTS.UsersColumns.FIREBASE_UID.value] = uid
    data_from_token[SQL_CONSTS.UsersColumns.FIREBASE_NAME.value] = decoded_token.get('name', '')
    data_from_token[SQL_CONSTS.UsersColumns.FIREBASE_EMAIL.value] = decoded_token.get('email', '')
    data_from_token[SQL_CONSTS.UsersColumns.FIREBASE_IMAGE_URL.value] = decoded_token.get('picture', '')
    data_from_token[SQL_CONSTS.UsersColumns.FIREBASE_SIGNIN_PROVIDER.value] = decoded_token.get('firebase', {}).get(
        'sign_in_provider', '')
    data_from_token[SQL_CONSTS.UsersColumns.APPLE_ID.value] = decoded_token.get('firebase',{}).get('identities',{}).get('apple.com',[''])[0]
    data_from_token[SQL_CONSTS.UsersColumns.FACEBOOK_ID.value] = \
        decoded_token.get('firebase', {}).get('identities', {}).get('facebook.com', [''])[0]
    data_from_token[SQL_CONSTS.UsersColumns.FIREBASE_PHONE_NUMBER.value] = decoded_token.get('phone_number', '')
    if not ignore_if_registered:
        # Let's see if the user is already registered, and if so let's give the phone an indication
        current_user_data = app.config.aurora_client.get_user_by_id(
            user_id=data_from_token[SQL_CONSTS.UsersColumns.FIREBASE_UID.value])
        if current_user_data is not None and len(current_user_data) > 0:
            if current_user_data.get(SQL_CONSTS.UsersColumns.REGISTRATION_STATUS.value,
                                     None) in [SQL_CONSTS.REGISTRATION_STATUS_TYPES.REGISTERED_APPROVED.value,
                                               SQL_CONSTS.REGISTRATION_STATUS_TYPES.REGISTERED_NOT_APPROVED.value
                                               ]:
                return jsonify({
                    ServerConsts.RegistrationResponses.STATUS.value: ServerConsts.RegistrationResponses.ALREADY_REGISTERED.value,
                    ServerConsts.RegistrationResponses.USER_DATA.value: current_user_data
                })
    data_from_token[SQL_CONSTS.UsersColumns.UPDATE_DATE.value] = time.time()
    app.config.aurora_client.register_user(user_dict=data_from_token)
    return jsonify({
        ServerConsts.RegistrationResponses.STATUS.value: ServerConsts.RegistrationResponses.NEW_REGISTER.value
        , ServerConsts.RegistrationResponses.USER_DATA.value: {SQL_CONSTS.UsersColumns.FIREBASE_UID.value: uid}})


@app.route('/user_data/get_user_data/<user_id>')
def get_all_user_data(user_id):
    user_data = app.config.aurora_client.get_user_by_id(user_id=user_id)
    return jsonify({'user_data':user_data})

@app.route('/user_data/register_firebase_uid', methods=['GET'])
def register_user():
    firebase_id_token = request.headers.get("firebase_id_token")
    decoded_token = auth.verify_id_token(firebase_id_token)
    return handle_token(decoded_token,ignore_if_registered=False)
    
    

def test_user_status(user_id):
    user_data = app.config.aurora_client.get_user_by_id(user_id=user_id)
    return user_data.get(SQL_CONSTS.UsersColumns.IS_TEST_USER.value, SQL_CONSTS.TestUserStates.IS_NOT_TEST_USER.value)


@app.route('/user_data/add_test_user/<user_id>')
def add_test_user(user_id):
    app.config.aurora_client.add_test_user(user_id=user_id)
    user_data = app.config.aurora_client.get_user_by_id(user_id=user_id)
    fcm_token = user_data[SQL_CONSTS.UsersColumns.FCM_TOKEN.value]
    send_message(user_id=user_id, data={
      ServerConsts.PushedData.PUSH_NOTIFICATION_TYPE.value : ServerConsts.PushedData.CHANGE_USER_STATUS.value,
      ServerConsts.PushedData.CHANGE_USER_KEY.value : SQL_CONSTS.UsersColumns.IS_TEST_USER.value,
      ServerConsts.PushedData.CHANGE_USER_VALUE.value: SQL_CONSTS.TestUserStates.IS_TEST_USER.value
    },fcm_token=fcm_token)
    return jsonify({'status':'success'})

@app.route('/user_data/remove_test_user/<user_id>')
def remove_test_user(user_id):
    app.config.aurora_client.remove_test_user(user_id=user_id)
    user_data = app.config.aurora_client.get_user_by_id(user_id=user_id)
    fcm_token = user_data[SQL_CONSTS.UsersColumns.FCM_TOKEN.value]
    send_message(user_id=user_id, data={
      ServerConsts.PushedData.PUSH_NOTIFICATION_TYPE.value : ServerConsts.PushedData.CHANGE_USER_STATUS.value,
      ServerConsts.PushedData.CHANGE_USER_KEY.value : SQL_CONSTS.UsersColumns.IS_TEST_USER.value,
      ServerConsts.PushedData.CHANGE_USER_VALUE.value: SQL_CONSTS.TestUserStates.IS_NOT_TEST_USER.value
    },fcm_token=fcm_token)
    return jsonify({'status':'success'})


@app.route('/user_data/approve_user/<user_id>')
def approve_user(user_id):
    app.config.aurora_client.approve_user(user_id=user_id)
    user_data = app.config.aurora_client.get_user_by_id(user_id=user_id)
    fcm_token = user_data[SQL_CONSTS.UsersColumns.FCM_TOKEN.value]
    send_message(user_id=user_id, data={
      ServerConsts.PushedData.PUSH_NOTIFICATION_TYPE.value : ServerConsts.PushedData.CHANGE_USER_STATUS.value,
      ServerConsts.PushedData.CHANGE_USER_KEY.value : SQL_CONSTS.UsersColumns.REGISTRATION_STATUS.value,
      ServerConsts.PushedData.CHANGE_USER_VALUE.value: SQL_CONSTS.REGISTRATION_STATUS_TYPES.REGISTERED_APPROVED.value,
    },fcm_token=fcm_token,notification_title='Welcome to Voilà',notification_body='Congratulations! Your profile was reviewed and approved by us. Enjoy the world\'s best Dating App')
    return jsonify({'status':'success'})

@app.route('/user_data/disapprove_user/<user_id>')
def disapprove_user(user_id):
    app.config.aurora_client.disapprove_user(user_id=user_id)
    user_data = app.config.aurora_client.get_user_by_id(user_id=user_id)
    fcm_token = user_data[SQL_CONSTS.UsersColumns.FCM_TOKEN.value]
    send_message(user_id=user_id, data={
      ServerConsts.PushedData.PUSH_NOTIFICATION_TYPE.value : ServerConsts.PushedData.CHANGE_USER_STATUS.value,
      ServerConsts.PushedData.CHANGE_USER_KEY.value : SQL_CONSTS.UsersColumns.REGISTRATION_STATUS.value,
      ServerConsts.PushedData.CHANGE_USER_VALUE.value: SQL_CONSTS.REGISTRATION_STATUS_TYPES.REGISTERED_NOT_APPROVED.value
    },fcm_token=fcm_token)
    return jsonify({'status':'success'})

@app.route('/user_data/verify_token', methods=['GET'])
def verify_token():
    '''
    Verify the token, extract all of the login information relevant to the user (phone number, facebook id, gmail etc)
    :return:
    status success if the token is alright
    otherwise status with error message
    
    TODO return Voila JWT through this path
    '''
    firebase_id_token = request.headers.get("firebase_id_token")
    decoded_token = auth.verify_id_token(firebase_id_token)
    return handle_token(decoded_token,ignore_if_registered=True)

@app.route('/user_data/users_in_location/<user_id>', methods=['GET'])
def count_users_current_location(user_id):
    MINIMUM_THRESHOLD = 2000 if not test_user_status(user_id)==SQL_CONSTS.TestUserStates.IS_TEST_USER.value else 0
    #TODO auth
    user_settings = app.config.aurora_client.get_user_by_id(user_id=user_id)
    lon = user_settings.get(SQL_CONSTS.UsersColumns.LONGITUDE.value, None)
    lat = user_settings.get(SQL_CONSTS.UsersColumns.LATITUDE.value, None)
    if any([x is None for x in [lon, lat]]):
        return jsonify({ServerConsts.LocationCountResponses.STATUS.value:ServerConsts.LocationCountResponses.UNKNOWN_USER_LOCATION.value,
                        ServerConsts.LocationCountResponses.IS_TEST_USER.value: (test_user_status(user_id))
                        })
    count = app.config.aurora_client.num_users_by_location(lat,lon)
    if count>=MINIMUM_THRESHOLD:
        return jsonify({
           ServerConsts.LocationCountResponses.STATUS.value: ServerConsts.LocationCountResponses.ENOUGH_USERS.value,
            ServerConsts.LocationCountResponses.IS_TEST_USER.value: (test_user_status(user_id))
        })
    #If here it's only when there are not enough users, so therefore:
    return jsonify({
        ServerConsts.LocationCountResponses.STATUS.value: ServerConsts.LocationCountResponses.NOT_ENOUGH_USERS.value,
        ServerConsts.LocationCountResponses.CURRENT_NUM.value : count,
        ServerConsts.LocationCountResponses.REQUIRED_NUM.value : MINIMUM_THRESHOLD,
        ServerConsts.LocationCountResponses.IS_TEST_USER.value: (test_user_status(user_id))
        
    })
    
@app.route('/user_data/delete_account/<user_id>', methods=['GET'])
def delete_account(user_id):
    app.config.aurora_client.delete_user(user_id=user_id)
    return jsonify({'status':'success'})

if __name__ == '__main__':
   app.run(threaded=True,port=20003,host="0.0.0.0",debug=False,ssl_context=('keys/selfsigned.crt', 'keys/selfsigned.key'))



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

Jennifer ID
5EX44AtZ5cXxW1O12G3tByRcC012
Yoni:
either 
OdTJPB8VryaHE31305GeoPeZaoD3
or
yWfbjwpoZ3P7Ai3XyPmAfoMYya42

https://services.voilaserver.com/user_data/match/5EX44AtZ5cXxW1O12G3tByRcC012/yWfbjwpoZ3P7Ai3XyPmAfoMYya42

SELECT count(*) FROM dummy_users
  WHERE earth_box(ll_to_earth(40.71427000, -74.00597000), 50000) @> ll_to_earth(latitude, longitude) and age>20 and age<55 and not cast (pof_id as varchar)  in (select decidee_id from decisions where decider_id='kRlw3NNKk5aavKfYEupXroBcfYp1')

  curl "localhost:20002/matches/kRlw3NNKk5aavKfYEupXroBcfYp1"


5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg

working:
https://s3.amazonaws.com/com.voiladating.users2/5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg?AWSAccessKeyId=AKIAVIASWTZFO7GHDZF4&Signature=WnXnmBMxG5O96YM7JC9EBK4sj6c%3D&Expires=1658382580
not working:
https://s3.amazonaws.com/com.voiladating.users2/5EX44AtZ5cXxW1O12G3tByRcC012/custom_image/analysis1658365948.861391/0.jpg?AWSAccessKeyId=AKIAVIASWTZFO7GHDZF4&amp;Signature=WnXnmBMxG5O96YM7JC9EBK4sj6c%3D&amp;Expires=1658382580

aws s3 sync s3://com.voiladating.dummy s3://com.voiladating.dummy2 --source-region us-east-2 --region us-east-1


trytry = 'insert into messages (message_id_,content,conversation_id,user_id,added_date,changed_date,status) values (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING'
print(f'{cursor.mogrify(trytry, post_message_data)}')

cursor.mogrify(trytry, post_message_data).decode('utf-8').replace('/','')
'''
