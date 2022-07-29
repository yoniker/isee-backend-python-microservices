import numpy as np
from PIL import Image
def np_to_jsoned_np(np_array):
    return np_array.tolist()

def jsoned_np_to_np(jsoned_np):
    return np.array(jsoned_np)


def jsoned_image_to_image(np_image_jsoned):
    np_image = np.array(np_image_jsoned)
    np_image = np_image.astype('uint8')
    return Image.fromarray(np_image)

def image_to_jsoned_image(pil_image):
    return np.array(pil_image).tolist()