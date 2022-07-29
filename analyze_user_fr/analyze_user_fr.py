import os
from enum import Enum
from flask import Flask,jsonify,request
from sql_consts import SQL_CONSTS
from postgres_client import PostgresClient
import requests
from s3_functions import upload_file_to_s3,download_file_from_s3
from image_utils import jsoned_image_to_image
import pickle
import numpy as np
from group_faces import embeddings_to_groups,EmbeddingsData,get_mid_embedding

class EnvConsts(str, Enum):
    POSTGRES_USERNAME = 'POSTGRES_USERNAME'
    POSTGRES_PASSWORD = 'POSTGRES_PASSWORD'
    POSTGRES_DB = 'POSTGRES_DB'
    POSTGRES_HOST = 'POSTGRES_HOST'
    


REAL_BUCKET = 'com.voiladating.users2'

app = Flask(__name__)

postgres_username = os.environ.get(EnvConsts.POSTGRES_USERNAME.value) or 'yoni'
postgres_password = os.environ.get(EnvConsts.POSTGRES_PASSWORD.value) or 'dordordor'
postgres_db = os.environ.get(EnvConsts.POSTGRES_DB.value) or 'dummy_users'
postgres_host = os.environ.get(EnvConsts.POSTGRES_HOST.value) or 'voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
app.config.postgres_client = PostgresClient(database=postgres_db,user=postgres_username,password=postgres_password,host=postgres_host)
cache_location = '/tmp'
os.makedirs(cache_location,exist_ok=True)

@app.route('/user_fr_analyze/<user_id>')
def analyze_user(user_id): 
    #Step 1: Get the images for which we need to detect and fr
    user_images_to_analyze = app.config.postgres_client.get_unanalyzed_images_by_uid(user_id=user_id)
    all_fr_data = dict()
    user_fr_data_s3_key = os.path.join(user_id, 'profile_analyzed', f'{user_id}.pickle')
    local_location_save_images = os.path.join(cache_location, user_id)
    os.makedirs(local_location_save_images, exist_ok=True)
    fr_user_filename = os.path.join(local_location_save_images, f'{user_id}.pickle')
    prior_data_exists = download_file_from_s3(filename=fr_user_filename, object_name=user_fr_data_s3_key)
    if prior_data_exists:
        with open(fr_user_filename, 'rb') as f:
            all_fr_data = pickle.load(f)
    for user_image_to_analyze in user_images_to_analyze:
        aws_key = user_image_to_analyze[SQL_CONSTS.ImageColumns.FILENAME.value]
        assert user_id == user_image_to_analyze[SQL_CONSTS.ImageColumns.USER_ID.value]
        if aws_key in all_fr_data.keys():
            continue
        response = requests.get(f'https://services.voilaserver.com/analyze/froms3/{aws_key}?fr_data=True&display_images=True')
        if not response.ok:
            continue
        analyzed_data = response.json()
        detections_data = analyzed_data['detections_data']
        s3_save_location = os.path.join(user_id,'profile_analyzed',os.path.basename(aws_key))
        for i, (display_image_data,fr_data) in enumerate(zip(detections_data['display_images'],detections_data['fr_data'])):
            display_image = jsoned_image_to_image(display_image_data)
            display_image_filename = os.path.join(local_location_save_images,f'{i}.jpg')
            display_image.save(display_image_filename)
            upload_file_to_s3(file_name=display_image_filename,bucket=REAL_BUCKET,object_name=os.path.join(s3_save_location,os.path.basename(display_image_filename)))
        image_fr_data = detections_data['fr_data']
        image_fr_data = [np.array(x).squeeze() for x in image_fr_data]
        fr_filename = os.path.join(local_location_save_images,f'{os.path.basename(aws_key)}.pickle')
        with open(fr_filename, 'wb') as handle:
           pickle.dump(image_fr_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        upload_file_to_s3(file_name=fr_filename,bucket=REAL_BUCKET,object_name=os.path.join(s3_save_location,f'{os.path.basename(aws_key)}.pickle'))
        all_fr_data[aws_key] = image_fr_data
        print(f'done with the file {os.path.basename(aws_key)}')
    
    with open(fr_user_filename, 'wb') as handle:
        pickle.dump(all_fr_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    upload_file_to_s3(file_name=fr_user_filename,bucket=REAL_BUCKET,object_name=user_fr_data_s3_key)
    #TODO: update the images table info regrading the analysis timestamp
    #At this point we have the info on all analyzed images. Let's now analyze only the images which are 'in_profile'.
    in_profile_images_data = app.config.postgres_client.get_user_profile_images(user_id=user_id)
    in_profile_images_filenames = [in_profile_image['filename'] for in_profile_image in in_profile_images_data]
    #sift only the profile images from the images data. If a profile image is not included in the data,restart the process
    in_profile_images_fr_data = {k:v for k,v in all_fr_data.items() if k in in_profile_images_filenames}
    if len(in_profile_images_fr_data) != len(in_profile_images_filenames):
        #TODO in the (far) future, if needed then restart the process here (if not all the data on profile images is available). This can happen if the user uploaded an image just as we checked previously :D
        pass
    # analyze the user fr_data, create mutual exclusive groups of faces
    embeddings_data = []
    for aws_key,image_fr_data in in_profile_images_fr_data.items():
        for detection_index,detection_fr_data in enumerate(image_fr_data):
            embeddings_data.append(EmbeddingsData(image_key=aws_key,embedding=detection_fr_data,detection_index=detection_index))
    embeddings_grouped = embeddings_to_groups(embeddings_data=embeddings_data)
    mid_embedding = get_mid_embedding(embeddings_grouped[0]) if len(embeddings_grouped)>0 else None
    embeddings_grouped_data = {'groups':embeddings_grouped,'mid_embedding':mid_embedding}
    # save groups data in user directory at s3
    groups_user_data_filename = os.path.join(local_location_save_images, f'{user_id}_groups.pickle')
    with open(groups_user_data_filename, 'wb') as handle:
        pickle.dump(embeddings_grouped_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    upload_file_to_s3(file_name=groups_user_data_filename, object_name=f'{user_id}/profile_analyzed/groups_data.pickle')

    if mid_embedding is not None:
        # Update user_fr_data table
        app.config.postgres_client.update_users_fr_data(users_fr_data={
            SQL_CONSTS.UsersFrDataColumns.USER_ID.value:user_id,
            SQL_CONSTS.UsersFrDataColumns.FR_DATA.value: pickle.dumps(mid_embedding)
        })
        has_fr_data = SQL_CONSTS.UserHasFr.TRUE.value
    else:
        has_fr_data = SQL_CONSTS.UserHasFr.FALSE.value
    user_data = {SQL_CONSTS.UsersColumns.FIREBASE_UID.value: user_id,
                 SQL_CONSTS.UsersColumns.HAS_FR_DATA.value: has_fr_data
                 }
    #update users main table
    app.config.postgres_client.update_user_data(user_data=user_data)

    
    return jsonify({'status':'success'})



if __name__ == '__main__':
   app.run(threaded=True,port=20006,host="0.0.0.0",debug=False)


'''

docker build . -t analyze_user_fr
docker run -it -d -p20006:20006/tcp analyze_user_fr
curl "localhost:20006/user_fr_analyze/5EX44AtZ5cXxW1O12G3tByRcC012"
'''