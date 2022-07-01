from PIL import Image
from image_utils import image_to_jsoned_image
import requests
import time
img = Image.open('2.jpg')
jsoned_image = image_to_jsoned_image(img)
while True:
    t1 =time.time()
    response = requests.get('http://shira.voilaserver.com/analyze/froms3/phil.jpg')
    t2=time.time()
    print(f'{t2-t1}')
    
