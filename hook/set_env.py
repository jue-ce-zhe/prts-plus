import os
import sys

if getattr(sys, 'frozen', False):
    # If application is run as a bundle
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

tessdata_path = os.path.join(application_path, "_internal", "Tesseract-OCR", "tessdata")
os.environ['TESSDATA_PREFIX'] = tessdata_path
