import requests
from flask import Flask,jsonify,request
from FaceDetection.api import FaceDetection
import json
from FaceRecognition.align.align_trans import warp_and_crop_face
from PIL import Image
import numpy as np
from FaceRecognition.backbone.api import load_recognition_model
from FaceRecognition.util.extract_feature_v1 import pil_extract_feature
import time

recognition_net = load_recognition_model(device='cpu')
crop_size=112



app = Flask(__name__)



@app.route('/analyze/play')

def local_play():
    detections_response = requests.get('http://dordating.com:5000/analyze/local/phil.jpg')
    t1 = time.time()
    jsoned_detection = json.loads(detections_response.content)['detections'][0]
    detection = FaceDetection.from_json(jsoned_detection)
    facial5points = detection.get_facial5points()
    img = Image.open('phil.jpg')
    aligned_face = Image.fromarray(warp_and_crop_face(np.array(img), facial5points, None, crop_size=(crop_size, crop_size)))
    features = pil_extract_feature([aligned_face],backbone=recognition_net)
    return jsonify({'status':'finished features ','total time':time.time()-t1})



@app.route('/analyze/recognition_healthcheck')
def say_healthy():
    return jsonify({'status':'face detection service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20002,host="0.0.0.0",debug=False)


'''
docker build . -t recognition_service:1
docker run -d -p20002:20002/tcp recognition_service:1
'''