import datetime
import os
from enum import Enum
from flask import Flask,jsonify,request,redirect
from sql_consts import SQL_CONSTS
from postgres_client import PostgresClient
import requests
from s3_functions import upload_file_to_s3,download_file_from_s3,generate_users_presigned_url
from image_utils import jsoned_image_to_image
import pickle
import numpy as np
from group_faces import embeddings_to_groups,EmbeddingsData,get_mid_embedding
from datetime import datetime
from pandas import DataFrame
from faceDetectionsApi import FaceDetection

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


def s3_user_fr_dir(user_id):
    return f'{user_id}/profile_fr_analyzed'

def s3_groups_filename(user_id):
    return s3_user_fr_dir(user_id)+'/'+'groups_data.pickle'


def local_location_save_data(user_id):
    return os.path.join(cache_location, user_id)

def groups_local_filename(user_id):
    return local_location_save_data(user_id=user_id) + '/' + f'{user_id}_groups.pickle'
@app.route('/analyze-user-fr/healthcheck')
def say_hello():
    return jsonify({'status':'analyze user fr is up and running'})


@app.route('/analyze-user-fr/get_analysis/<user_id>')
def get_user_analysis(user_id):
    #Step 1: Is the analysis ready? For now, assume that if there are no unanalyzed images, the user data is ready.
    user_images_to_analyze = app.config.postgres_client.get_unanalyzed_fr_images_by_uid(user_id=user_id)
    if len(user_images_to_analyze) > 0:
        return jsonify({'status':'user images still need to be analyzed'}),202
    user_analysis_s3_key = s3_groups_filename(user_id=user_id)

    groups_user_data_filename = groups_local_filename(user_id=user_id)
    try:
        os.makedirs(os.path.dirname(groups_user_data_filename),exist_ok=True)
        download_file_from_s3(filename=groups_user_data_filename,object_name=user_analysis_s3_key)
        with open(groups_user_data_filename,'rb') as f:
            user_fr_data = pickle.load(f)
    except:
        return jsonify({'status':'couldnt locate user data'}) , 404
    faces_details = []
    groups_data = user_fr_data['groups']
    for group in groups_data:
        for embeddingsData in group: #type:EmbeddingsData
            faces_details.append(embeddingsData.image_key+'/'+str(embeddingsData.detection_index))
    return jsonify({'status':'success','faces_details':faces_details})

    #Go to the groups' data, and get all of the info

@app.route('/analyze-user-fr/fr_face_image/<user_id>/<image_name>/<detection_index>')
def redirect_user_fr_image(user_id,image_name,detection_index):
    aws_key = os.path.join(s3_user_fr_dir(user_id=user_id),image_name,f'{detection_index}.jpg')
    url = generate_users_presigned_url(aws_key=aws_key, bucket_name=REAL_BUCKET, expiresIn=300)
    return redirect(url, code=302)


@app.route('/analyze-user-fr/perform_analysis/<user_id>')
def analyze_user(user_id): 
    #Step 1: Get the images for which we need to detect and fr
    user_images_to_analyze = app.config.postgres_client.get_unanalyzed_fr_images_by_uid(user_id=user_id)
    all_fr_data = dict()
    all_traits_data = dict()
    user_fr_data_s3_key = os.path.join(s3_user_fr_dir(user_id=user_id), f'{user_id}.pickle')
    os.makedirs(local_location_save_data(user_id=user_id), exist_ok=True)
    data_user_filename = os.path.join(local_location_save_data(user_id=user_id), f'{user_id}.pickle')
    prior_data_exists = download_file_from_s3(filename=data_user_filename, object_name=user_fr_data_s3_key)
    if prior_data_exists:
        try:
            with open(data_user_filename, 'rb') as f:
                all_data = pickle.load(f)
                all_fr_data = all_data['fr']
                all_traits_data = all_data['traits']
        except:
            pass
    for user_image_to_analyze in user_images_to_analyze:
        aws_key = user_image_to_analyze[SQL_CONSTS.ImageColumns.FILENAME.value]
        assert user_id == user_image_to_analyze[SQL_CONSTS.ImageColumns.USER_ID.value]
        if (aws_key in all_fr_data.keys()) and (aws_key in all_traits_data.keys()): #Eg if image was already analyzed by traits and by fr
            continue
        response = requests.get(f'https://services.voilaserver.com/analyze/froms3/{aws_key}?fr_data=True&display_images=True') #TODO use SRV dns resolution
        if not response.ok:
            continue
        analyzed_data = response.json()
        detections_data = analyzed_data['detections_data']
        jsoned_detections = detections_data['detections']
        #detections = [FaceDetection.from_json(jsoned_detection) for jsoned_detection in jsoned_detections]
        #localhost: 5000 / age_service / analyze
        traits_response = requests.post(f'https://services.voilaserver.com/traits/analyze/{aws_key}',
                      json={'detections':jsoned_detections}
                      ) #TODO change DNS resolution to SRV
        detections_traits_data = traits_response.json().get('traits',[]) #should be a list with each detection traits
        if not len(detections_traits_data) == len(jsoned_detections):
            return jsonify({'status':'error:different traits and detections lengths', 'details': f'error - traits length is {len(detections_traits_data)} and not equal to detections length which is {len(jsoned_detections)}'})
        s3_profile_analysis_save_location = os.path.join(s3_user_fr_dir(user_id=user_id),os.path.basename(aws_key))
        for i, (display_image_data,fr_data,detection_trait_data) in enumerate(zip(detections_data['display_images'],detections_data['fr_data'],detections_traits_data)):
            #save display image
            display_image = jsoned_image_to_image(display_image_data)
            display_image_filename = os.path.join(local_location_save_data(user_id=user_id), f'{i}.jpg')
            display_image.save(display_image_filename)
            upload_file_to_s3(file_name=display_image_filename,bucket=REAL_BUCKET,object_name=os.path.join(s3_profile_analysis_save_location,os.path.basename(display_image_filename)))
            #save fr data
            fr_data = np.array(fr_data).squeeze()
            fr_filename = os.path.join(local_location_save_data(user_id=user_id), f'{i}_fr.pickle')
            with open(fr_filename,'wb') as f:
                pickle.dump(fr_data, f,protocol=pickle.HIGHEST_PROTOCOL)
            upload_file_to_s3(file_name=fr_filename,object_name=os.path.join(s3_profile_analysis_save_location,os.path.basename(fr_filename)))
            #save traits data
            traits_filename = os.path.join(local_location_save_data(user_id=user_id), f'{i}_traits.pickle')
            with open(traits_filename, 'wb') as f:
                pickle.dump(detection_trait_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            upload_file_to_s3(file_name=traits_filename, object_name=os.path.join(s3_profile_analysis_save_location,
                                                                              os.path.basename(traits_filename)))
        image_fr_data = detections_data['fr_data']
        image_fr_data = [np.array(x).squeeze() for x in image_fr_data]
        #fr_filename = os.path.join(local_location_save_images(user_id=user_id),f'{os.path.basename(aws_key)}.pickle')
        #with open(fr_filename, 'wb') as handle:
        #    pickle.dump(image_fr_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        #upload_file_to_s3(file_name=fr_filename,bucket=REAL_BUCKET,object_name=os.path.join(s3_current_image_fr_save_location,f'{os.path.basename(aws_key)}.pickle'))
        all_fr_data[aws_key] = image_fr_data
        all_traits_data[aws_key] = detections_traits_data
        print(f'done with the file {os.path.basename(aws_key)}')
    all_data = {'fr':all_fr_data,'traits':all_traits_data}
    with open(data_user_filename, 'wb') as handle:
        pickle.dump(all_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    upload_file_to_s3(file_name=data_user_filename,bucket=REAL_BUCKET,object_name=user_fr_data_s3_key)
    if len(user_images_to_analyze) > 0:
        app.config.postgres_client.update_images_analyzed(user_id=user_id,
                                                          filenames=[x[SQL_CONSTS.ImageColumns.FILENAME.value] for x in user_images_to_analyze],
                                                          timestamp=datetime.now().timestamp()
                                                          )
    #At this point we have the info on all analyzed images. Let's now analyze only the images which are 'in_profile'.
    in_profile_images_data = app.config.postgres_client.get_user_profile_images(user_id=user_id)
    if len(in_profile_images_data) == 0 :
        return jsonify({'status':'User images don\'t exist'})
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
            embeddings_data.append(EmbeddingsData(image_key=aws_key,embedding=detection_fr_data,detection_index=detection_index,traits_data=all_traits_data[aws_key][detection_index]))
    embeddings_grouped = embeddings_to_groups(embeddings_data=embeddings_data)
    mid_embedding = get_mid_embedding(embeddings_grouped[0]) if len(embeddings_grouped)>0 else None
    embeddings_grouped_data = {'groups':embeddings_grouped,'mid_embedding':mid_embedding}
    # save groups data in user directory at s3
    groups_user_data_filename = os.path.join(local_location_save_data(user_id=user_id), f'{user_id}_groups.pickle')
    with open(groups_user_data_filename, 'wb') as handle:
        pickle.dump(embeddings_grouped_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    upload_file_to_s3(file_name=groups_user_data_filename, object_name=f'{user_id}/profile_fr_analyzed/groups_data.pickle')

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


'''
Celeb look alike:
In this part I will implement celeb look alike
'''

with open('celebs.pickle', 'rb') as f:
    all_celebs_data = pickle.load(f)
all_celeb_embeddings = np.stack(all_celebs_data.fr_data, axis=0)

def get_most_lookalike_celebs(embeddings, num_celebs=7):
    distances = np.linalg.norm(embeddings - all_celeb_embeddings, axis=1)
    name_distances = DataFrame({'distance': distances,'celebname': all_celebs_data.celebname})
    name_distances.sort_values(by=['distance'], inplace=True)
    return name_distances[0:num_celebs].to_dict(orient='records')


def get_analyzed_profile_fr_data(user_id, image_filename, detection_index):
    s3_fr_data_location = os.path.join(s3_user_fr_dir(user_id),image_filename,f'{detection_index}_fr.pickle')
    local_fr_location = os.path.join(local_location_save_data(user_id=user_id),os.path.basename(s3_fr_data_location))
    os.makedirs(os.path.dirname(local_fr_location),exist_ok=True)
    download_file_from_s3(filename=local_fr_location,object_name=s3_fr_data_location)
    with open(local_fr_location,'rb') as f:
        fr_data = pickle.load(f)
    return fr_data

def get_analyzed_traits(user_id, image_filename, detection_index): #TODO DRY - merge with above function
    s3_fr_data_location = os.path.join(s3_user_fr_dir(user_id),image_filename,f'{detection_index}_traits.pickle')
    local_fr_location = os.path.join(local_location_save_data(user_id=user_id),os.path.basename(s3_fr_data_location))
    os.makedirs(os.path.dirname(local_fr_location),exist_ok=True)
    download_file_from_s3(filename=local_fr_location,object_name=s3_fr_data_location)
    with open(local_fr_location,'rb') as f:
        traits_data = pickle.load(f)
    return traits_data

@app.route('/analyze-user-fr/get_celebs_lookalike/<user_id>/<image_filename>/<detection_index>')
def get_most_lookalike_celebs_by_image(user_id, image_filename, detection_index):
    fr_data_chosen = get_analyzed_profile_fr_data(user_id=user_id,image_filename=image_filename,detection_index=detection_index)
    celebs_data = get_most_lookalike_celebs(embeddings=fr_data_chosen)
    return jsonify({'celebs_data':celebs_data,'status':'success'})

@app.route('/analyze-user-fr/get_traits/<user_id>/<image_filename>/<detection_index>')
def get_traits_by_detection(user_id, image_filename, detection_index):
    traits_data_chosen = get_analyzed_traits(user_id=user_id, image_filename=image_filename,
                                                  detection_index=detection_index)
    return jsonify({'traits': traits_data_chosen, 'status': 'success'})
    #5EX44AtZ5cXxW1O12G3tByRcC012/1659217900.4540095_5EX44AtZ5cXxW1O12G3tByRcC012_92715.jpg/0


if __name__ == '__main__':
    app.run(threaded=True, port=20006, host="0.0.0.0", debug=False)


'''

docker build . -t analyze_user_fr
docker run -it -d -p20006:20006/tcp analyze_user_fr
curl "localhost:20006/analyze-user-fr/get_analysis/5EX44AtZ5cXxW1O12G3tByRcC012"
curl "localhost:20006/analyze-user-fr/perform_analysis/5EX44AtZ5cXxW1O12G3tByRcC012"
curl "localhost:20006/analyze-user-fr/get_celebs_lookalike/5EX44AtZ5cXxW1O12G3tByRcC012/1659217900.4540095_5EX44AtZ5cXxW1O12G3tByRcC012_92715.jpg/0"
'''