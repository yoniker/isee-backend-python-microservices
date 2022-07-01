from FaceRecognition.align.detector import detect_faces,DetectionNets
from flask import Flask,jsonify,request
from image_utils import jsoned_image_to_image
import time
import boto3
from PIL import Image

device='cpu'
detection_nets = DetectionNets(device=device)

app = Flask(__name__)

def detect_faces_task(img,is_jsoned = True):
    try:
        t1 = time.time()
        if is_jsoned: img = jsoned_image_to_image(img)
        t2=time.time()
        detections = detect_faces(img, detection_nets=detection_nets)
        t3=time.time()
        print(f'It took {t2-t1} to unload image, {t3-t2} to detect')
        print(detections)
        return [detection.to_json() for detection in detections]
    except:
        return []

@app.route('/analyze/detection',methods=['POST'])
def detect_faces_endpoint():
    jsoned_image = request.get_json(force = True)['image']
    detections = detect_faces_task(img=jsoned_image)
    return jsonify({'image':jsoned_image,'detections':detections})

@app.route('/analyze/froms3/<demo_file_name>')
def analyze_from_s3(demo_file_name):
    s3 = boto3.client('s3')
    s3.download_file('com.voiladating.users', f'demo_images/{demo_file_name}', demo_file_name)
    img = Image.open(demo_file_name)
    detections = detect_faces_task(img=img,is_jsoned=False)
    return jsonify({'filename': demo_file_name, 'detections': detections})

@app.route('/analyze/detection_healthcheck')
def say_healthy():
    return jsonify({'status':'face detection service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20001,host="0.0.0.0",debug=False)

