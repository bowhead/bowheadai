from flask import Flask, request, session
from flask_cors import CORS
from pdf2image import convert_from_path
import os
from os import getenv
import cv2
from paddleocr import PPStructure,draw_structure_result,save_structure_res, PaddleOCR
import requests
import shutil
#from dotenv import load_dotenv
from flask_socketio import SocketIO, emit
from flask_session import Session
from os import getenv
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file
load_dotenv()

# Access the URL variables
api_url = "http://langchain:3001/upload"

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = getenv('SECRET_KEY', 'dfasdfasd')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

@socketio.on('connect')
def handle_connect():
    emit('message', {'text': 'Connected'})
    

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    
    
    # Get the value of deleteOldFiles from the form data
    delete_old_files = request.form.get('deleteOldFiles', 'true') == 'true'

    socketio.emit('progress', {'progress': 10}, room = session.get('sid', ''))
    
    if delete_old_files:
        user_id = str(uuid.uuid4())+"/"
        # Crear una carpeta con el ID del usuario
        temp_path = 'temp/' + user_id
        images_path = 'images/' + user_id
        output_path = 'output/' + user_id
        os.makedirs(temp_path)
        os.makedirs(images_path)
        os.makedirs(output_path)

        
    
    
    

    """
    if delete_old_files:
        dir = 'temp/'
        if not os.path.exists(dir): os.makedirs(dir)# Create a new directory because it does not exist
        for f in os.listdir(dir):
            if os.path.isfile(os.path.join(dir, f)):
                os.remove(os.path.join(dir, f))
            else:
                shutil.rmtree(os.path.join(dir, f))

        
        dir = 'images/'
        if not os.path.exists(dir): os.makedirs(dir)
        for f in os.listdir(dir):
            if os.path.isfile(os.path.join(dir, f)):
                os.remove(os.path.join(dir, f))
            else:
                shutil.rmtree(os.path.join(dir, f))
        

        dir = 'output/'
        if not os.path.exists(dir): os.makedirs(dir)
        for f in os.listdir(dir):
            if os.path.isfile(os.path.join(dir, f)):
                os.remove(os.path.join(dir, f))
            else:
                shutil.rmtree(os.path.join(dir, f))"""
    
    # Check if files were sent
    if 'files' not in request.files:
        return 'No files uploaded', 400
    
    uploaded_files = request.files.getlist('files')

    # Get the names of the old files
    old_files = get_file_names(temp_path) + get_file_names(images_path)
    
    # Process each uploaded file
    for file in uploaded_files:
        # Check if the file is already present
        if file.filename in old_files:
            print(f'INFO: Skipping file {file.filename}, already processed')
            continue
        print('INFO: Image Process ' + file.filename)
        
        # Save the file or perform any desired operations
        filename = file.filename.split(".")
        if filename[1] =='pdf':
            file.save(temp_path + file.filename)
            # Convert PDF to images
            images = convert_from_path(temp_path+file.filename)
            
            # Save each image
            for i, image in enumerate(images):
                image_name = f"{filename[0]}_{i}.jpg"
                image.save(images_path + image_name)
                # You can perform additional operations on the image here
                
                # Remove the original PDF file
        else:
            file.save(output_path+file.filename)
    
    print('INFO: Paddle Process')
    socketio.emit('progress', {'progress': 33}, room = session.get('sid', ''))      
    paddle_process(old_files, images_path, output_path)
    
    socketio.emit('progress', {'progress': 66}, room = session.get('sid', ''))
    print('INFO: Create Vector')
    post_files(output_path)
    
    socketio.emit('progress', {'progress': 100}, room = session.get('sid', ''))
    
    return 'Files uploaded successfully'

def get_file_names(dir):
    if os.path.exists(dir):
        return [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    return []

def paddle_process(old_files, images_path, output_path):
    #table_engine = PPStructure(show_log=False)
    
    files = os.listdir(images_path)

   
    
    ocr = PaddleOCR(show_log=False)
    for file in files:
        if file in old_files:
            print(f'INFO: Skipping image {file}, already processed')
            continue
        print('INFO: Paddle Process ' + file)

        img_path = images_path + file
        #result = table_engine(img)
        result = ocr.ocr(img_path)
        #print(os.path.basename(img_path).split('.')[0])
        #save_structure_res(result, save_folder,os.path.basename(img_path).split('.')[0])
        txts = [line[1][0] for line in result[0]]
        
        with open(f'{output_path}{file.split(".")[0]}.txt', 'w') as f:
            for line in txts:
                f.write(f"{line}\n")

def post_files(output_path):

    # Get all file paths in the folder
    file_paths = [os.path.join(output_path, filename) for filename in os.listdir(output_path)]

    # Prepare the files dictionary
    files = []
    for file_path in file_paths:
        with open(file_path, 'rb') as file:
            file_content = file.read() 
        files.append(('files', (file_path, file_content, 'application/octet-stream')))
    
    # Add the ID to the files dictionary
    #files.append(('text_data', output_path.split("/")[1]))

    print('INFO: Langchain Process',flush=True)
    # Send the POST request
    response = requests.post(api_url, files=files)

    # Print the response
    print(response.text)

if __name__ == '__main__':
    socketio.run(app)
