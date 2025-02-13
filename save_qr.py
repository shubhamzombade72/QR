import os
from PIL import Image
import base64
from io import BytesIO

# Define absolute paths
BASE_DIR = r'c:\Users\ADMIN\OneDrive\Desktop\QR Generator'
IMAGES_DIR = os.path.join(BASE_DIR, 'static', 'images')

# Create directory if it doesn't exist
os.makedirs(IMAGES_DIR, exist_ok=True)

# Decode base64 image data and save
def save_qr_code(image_data):
	try:
		image_data = image_data.split(',')[1]  # Remove data:image/png;base64, prefix
		decoded_image = base64.b64decode(image_data)
		image = Image.open(BytesIO(decoded_image))
		image.save(os.path.join(IMAGES_DIR, 'donation_qr.png'))
		return True
	except Exception as e:
		print(f"Error saving QR code: {e}")
		return False

# Example usage (replace with actual base64 data)
# image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
# save_qr_code(image_data)