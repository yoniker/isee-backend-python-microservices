from email.policy import default
from FaceRecognition.align.detector import detect_faces,DetectionNets
from flask import Flask,jsonify,request
from image_utils import jsoned_image_to_image,image_to_jsoned_image
import time
import boto3
from PIL import Image
from FaceRecognition.align.align_trans import warp_and_crop_face
import numpy as np
from FaceRecognition.backbone.api import load_recognition_model
from FaceRecognition.util.extract_feature_v1 import pil_extract_feature
from FaceDetection.api import FaceDetection
import pickle


device='cpu'
detection_nets = DetectionNets(device=device)
crop_size = 112 #crop size for FR system
recognition_net = load_recognition_model(device='cpu')

app = Flask(__name__)

def detect_faces_task(img,is_jsoned = True):
    try:
        if is_jsoned: img = jsoned_image_to_image(img)
        detections = detect_faces(img, detection_nets=detection_nets)
        return detections
    except:
        return []

def analyze(img,fr_data,display_images):
    detections = detect_faces_task(img=img,is_jsoned=False)
    detections_data = {'detections':[],'fr_data':[],'aligned_images':[]}
    for detection in detections:
        facial5points = detection.get_facial5points()
        aligned_face = Image.fromarray(warp_and_crop_face(np.array(img), facial5points, None, crop_size=(crop_size, crop_size)))
        features = pil_extract_feature([aligned_face],backbone=recognition_net)
        detections_data['detections'].append(detection.to_json())
        if fr_data: detections_data['fr_data'].append(features.tolist())
        if display_images: detections_data['aligned_images'].append(image_to_jsoned_image(calc_image_around_face(detection=detection,image=img)))
    return detections_data


def calc_image_around_face(detection,image):
   np_image = np.array(image.convert('RGB'))
   h,w,_ = np_image.shape
   [(x1,y1),(x2,y2)] = detection.bounding_box
   [x1,y1,x2,y2] = [round(x) for x in [x1,y1,x2,y2]]
   d = 2*min(y2-y1,x2-x1)
   if y1-2*d<0:
      d = max(round(y1/2-1),0)
   if y2+2*d>=h:
      d = round((h-y2)/2-1)
   if x1-2*d<0:
      d = max(round(x1/2-1),0)
   if x2+2*d>=w:
      d = round((w-x2)/2-1)
   [x1,x2,y1,y2] = [x1-2*d,x2+2*d,y1-2*d,y2+2*d]
   x1 = min(max(0,x1),w-1)
   x2 = min(max(0,x2),w-1)
   y1 = min(max(0,y1),h-1)
   y2 = min(max(0,y2),h-1)
   np_image = np_image[y1:y2,x1:x2,:]
   return Image.fromarray(np_image)


@app.route('/analyze/froms3/<demo_file_name>')
def analyze_from_s3(demo_file_name):
    s3 = boto3.client('s3')
    s3.download_file('com.voiladating.users', f'demo_images/{demo_file_name}', demo_file_name)
    img = Image.open(demo_file_name)
    t1 = time.time()
    fr_data = request.args.get('fr_data',default='False')=='True'
    display_images = request.args.get('display_images',default='False')=='True'
    detections_data = analyze(img=img,fr_data=fr_data,display_images=display_images)
    return jsonify({'detections_data':detections_data,'total_time':time.time()-t1})

@app.route('/analyze/display_image_around_face',methods=['POST'])
def around_face_local():
    request_data = request.get_json(force = True)
    jsoned_image = request_data['image']
    jsoned_detection = request_data['detection']
    img = jsoned_image_to_image(jsoned_image)
    detection = FaceDetection.from_json(jsoned_detection)
    display_image = calc_image_around_face(detection=detection,image=img)
    return image_to_jsoned_image(display_image)





@app.route('/analyze/detection_healthcheck')
def say_healthy():
    return jsonify({'status':'face detection+recognition service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20001,host="0.0.0.0",debug=False)



'''
docker build . -t face_service:1
docker run -d -it -v  /home/yoni/Projects/docker_services/face_detection:/home/face_detection_service -p20001:20001/tcp face_service:1


'''

