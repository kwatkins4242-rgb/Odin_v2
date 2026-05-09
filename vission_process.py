from PIL import Image

   def process_screenshot(filepath):
       with Image.open(filepath) as img:
           processed_image = img  # Additional processing can be done here
           return processed_image