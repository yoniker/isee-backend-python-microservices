from FaceRecognition.backbone.api import load_recognition_model
from FaceRecognition.align.align_trans import warp_and_crop_face
from FaceRecognition.util.extract_feature_v1 import pil_extract_feature





'''
docker build . -t recognition_service:1
docker run -d -p20002:20002/tcp -v /home/yoni/Projects/docker_services/recognize:/home/recognition_service recognition_service:1
'''