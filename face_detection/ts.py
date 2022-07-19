from FaceRecognition.align.detector import detect_faces,DetectionNets
from flask import Flask,jsonify,request
from image_utils import jsoned_image_to_image
import time
import boto3
from PIL import Image
import torch.jit

device='cpu'
detection_nets = DetectionNets(device=device)
torch.jit.trace(detection_nets)