from PIL import ImageGrab
   import datetime

   def capture_screenshot():
       timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
       screenshot_name = f"./screenshots/screenshot_{timestamp}.png"
       ImageGrab.grab().save(screenshot_name)
       return screenshot_name