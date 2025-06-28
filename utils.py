from PIL import Image, ImageDraw, ImageFont
from constants import DISEASE_INFO
import io
import base64
import numpy as np

def draw_detection(results):
    # Ambil numpy image dari results.plot()
    result_image_np = results.plot()
    return Image.fromarray(result_image_np)

# Convert image to base64 for database storage
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str
