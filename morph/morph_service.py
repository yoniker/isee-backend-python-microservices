from flask import Flask,request,jsonify
import boto3
from botocore.exceptions import ClientError
import logging
import os
import requests
from face_morpher.facemorpher.morpher import morpher
from s3_functions import download_file_from_s3,upload_file_to_s3
import time
import base64
import json


def dict_into_b64(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).decode()


app = Flask(__name__)
app.url_map.strict_slashes = False

REAL_BUCKET = 'com.voiladating.users2'
CELEBS_BUCKET = 'com.voiladating.celebs'

local_cache_dir = '/tmp'

@app.route('/morph/perform')
def perform_morph():
    user_id = request.args.get('user_id', '')
    user_image_filename = request.args.get('user_image_filename', '')
    detection_index = request.args.get('detection_index', '')
    celeb_name = request.args.get('celeb_name', '')
    celeb_filename = request.args.get('celeb_filename', '')
    if any([x == '' for x in [user_id,user_image_filename, detection_index, celeb_name, celeb_filename]]):
        return jsonify({'status':'bad parameters'}), 404
    user_detection_key = os.path.join(user_id,'profile_fr_analyzed',user_image_filename,f'{detection_index}.jpg')
    celeb_key = f'{celeb_name}/{celeb_filename}'
    user_local_dir = os.path.join(local_cache_dir,user_id)
    os.makedirs(user_local_dir,exist_ok=True)
    user_full_filename = os.path.join(user_local_dir,'user_detection_'+os.path.basename(user_detection_key))
    celeb_full_filename = os.path.join(user_local_dir,'celeb_detection_'+os.path.basename(celeb_key))
    download_file_from_s3(filename=user_full_filename,object_name=user_detection_key,bucket=REAL_BUCKET)
    download_file_from_s3(filename=celeb_full_filename,object_name=celeb_key,bucket=CELEBS_BUCKET)
    short_filename = str(time.time())+'.avi'
    out_video_filename = os.path.join(user_local_dir, short_filename)
    morpher(imgpaths=[user_full_filename,celeb_full_filename],out_video=out_video_filename)
    upload_file_to_s3(file_name=out_video_filename,object_name=f'{user_id}/morph_video/{short_filename}')
    return jsonify({'status':'success','morph_filename':short_filename})


@app.route('/morph/healthcheck')
def say_healthy():
    return jsonify({'status': 'morph service is up and running'})




if __name__ == '__main__':
    app.run(threaded=True, port=20009, host="0.0.0.0", debug=False)

#docker build . -t morph
#docker run -d -it morph:latest
#python facemorpher/morpher.py --src=l.jpg --dest=b.jpg  --out_video=out.avi
#curl localhost:20009/morph/perform?user_id=5EX44AtZ5cXxW1O12G3tByRcC012&user_image_filename=1645896125.589132_5EX44AtZ5cXxW1O12G3tByRcC012_61388.jpg&detection_index=0&celeb_name=Ailee&celeb_filename=1.png