﻿from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import numpy as np
import png, pydicom
import PIL

# Keras
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image

# Flask utils
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
from gevent.wsgi import WSGIServer

# Define a flask app
app = Flask(__name__)

# Model saved with Keras model.save()
MODEL_PATH = 'models/trained_model.h5'

#Load your trained model
model = load_model(MODEL_PATH)
#model._make_predict_function()          # Necessary to make everything ready to run on the GPU ahead of time
print('Model loaded. Start serving...')

# You can also use pretrained model from Keras
# Check https://keras.io/applications/
#from keras.applications.resnet50 import ResNet50
#model = ResNet50(weights='imagenet')
#print('Model loaded. Check http://127.0.0.1:5000/')

def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(64, 64)) #target_size must agree with what the trained model expects!!

    # Preprocessing the image
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
   
    preds = model.predict(img)
    return preds

def dicom2png(dicom_file,output_folder):
    try:
        ds = pydicom.dcmread(dicom_file)
        shape = ds.pixel_array.shape

        # Convert to float to avoid overflow or underflow losses.
        image_2d = ds.pixel_array.astype(float)

        # Rescaling grey scale between 0-255
        image_2d_scaled = (np.maximum(image_2d,0) / image_2d.max()) * 255.0

        # Convert to uint
        image_2d_scaled = np.uint8(image_2d_scaled)

        # Write the PNG file
        # with open(f'{dicom_file.strip(".dcm")}.png', 'wb') as png_file:
        with open(os.path.join(output_folder,dicom_file)+'.png' , 'wb') as png_file:
            w = png.Writer(shape[1], shape[0], greyscale=True)
            w.write(png_file, image_2d_scaled)
            print('dicom successfuly converted')
    except:
        print("could not convert dicom file")
    
@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')    
      
@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
	
        # Make prediction

        #if its dicom file
        output_folder = os.path.join(basepath,'uploads')
        list_of_files = os.listdir(output_folder)
        for i in list_of_files:
            os.remove(i)
        print(len(list_of_files))


        str1 = 'Pneumonia'
        str2 = 'Normal'
        if file_path.endswith(".dcm"):
            dicom2png(file_path,output_folder)
            print(len(list_of_files))
            preds = model_predict(list_of_files[1], model)
            os.remove(list_of_files[1])#removes file from the server after prediction has been returned
            if preds == 1:
                return str1
            else:
                return str2
        else:
            print('this is not a dicom file')
            preds = model_predict(file_path, model)
            os.remove(file_path) 
            if preds == 1:
                return str1
            else:
                return str2
        # Arrange the correct return according to the model. 
		#In this model 1 is Pneumonia and 0 is Normal.

    return None

    #this section is used by gunicorn to serve the app on Heroku
if __name__ == '__main__':
        app.run()
    #uncomment this section to serve the app locally with gevent at:  http://localhost:5000
    # Serve the app with gevent 
    #http_server = WSGIServer(('', 5000), app)
    #http_server.serve_forever()

    
