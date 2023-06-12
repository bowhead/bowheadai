from flask import Flask, request, session
from flask_cors import CORS
import os
from os import getenv
import requests
import shutil
#from dotenv import load_dotenv
from flask_socketio import SocketIO, emit
from flask_session import Session
from os import getenv
from dotenv import load_dotenv
from pathvalidate import sanitize_filename

from pypdf import PdfReader
import os
from PIL import Image
import pytesseract


# Load environment variables from .env file
load_dotenv()

# Access the URL variables
api_url = getenv('LANGCHAIN_UPLOAD_ENDPOINT')
delete_url = getenv('LANGCHAIN_DELETE_ENDPOINT')
cors_domains = getenv('CORS_DOMAINS').split(',')
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = getenv('SECRET_KEY', '')
app.config['SESSION_TYPE'] = 'filesystem'
#Session(app)

socketio = SocketIO(app, cors_allowed_origins=cors_domains, manage_session=False)

@socketio.on('connect')
def handle_connect():
    emit('message', {'text': 'Connected'})

@socketio.on('disconnect')
def disconnect():
    uuid = sanitize_filename(request.headers.get('uuid'))
    # Try to remove the tree; if it fails, throw an error using try...except.
    for folder in ["temp/","images/","output/"]:
        dir = folder + uuid + "/"
        try:
            shutil.rmtree(dir)
            print(f"INFO: folder {folder} delete suscesfully")
        except OSError as e:
            pass
            #print("Error: %s - %s." % (e.filename, e.strerror))
    data = {'user_id':uuid}    
    response = requests.post(delete_url, data=data)
    print(response.text,flush=True)


@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    # Get the value of deleteOldFiles from the form data
    delete_old_files = request.form.get('deleteOldFiles', 'true') == 'true'

    socketio.emit('progress', {'progress': 10})
    
    user_id = sanitize_filename(request.form.get('userId', ''))+"/"

    if not os.path.exists('temp/'): os.makedirs('temp/')
    if not os.path.exists('images/'): os.makedirs('images/')
    if not os.path.exists('output/'): os.makedirs('output/')

    # Crear una carpeta con el ID del usuario
    temp_path = 'temp/' + user_id
    images_path = 'images/' + user_id
    output_path = 'output/' + user_id
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
        os.makedirs(images_path)
        os.makedirs(output_path)

    
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

        else:
            file.save(output_path+file.filename)
            
    print('INFO: PyPDF Process')
    socketio.emit('progress', {'progress': 33})      
    pypdf_process(old_files, images_path, output_path, temp_path)
    
    socketio.emit('progress', {'progress': 66})
    print('INFO: Create Vector')
    post_files(output_path)
    
    socketio.emit('progress', {'progress': 100})
    
    return 'Files uploaded successfully'

def get_file_names(dir):
    if os.path.exists(dir):
        return [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    return []

def pypdf_process(old_files, images_path, output_path, temp_path):
    files = os.listdir(temp_path)

    for file in files:
        if file in old_files:
            print(f'INFO: Skipping image {file}, already processed')
            continue
        print('INFO: Pypdf Process ' + file)

        
        reader = PdfReader(temp_path+file)
        pages = len(reader.pages)

        text_list = []
        count = 0
        images_text = []

        #Get images and text for every page
        for page_num in range(pages):
            page = reader.pages[page_num]
            text_list.append(page.extract_text())

            #Get images in page
            for image_file_object in page.images:
                with open(images_path + str(page_num) + "_" + file.split(".")[0] + "_" + str(count) + "_" + image_file_object.name, "wb") as fp:
                    fp.write(image_file_object.data)
                images_text.append(pytesseract.image_to_string(Image.open(images_path + str(page_num) + "_" + file.split(".")[0] + "_" + str(count) + "_" + image_file_object.name)))
                count += 1

        #Save text in txt
        if images_text:
            with open(f'{output_path}image_{file.split(".")[0]}.txt', 'w') as f:
                for line in images_text:
                    clean_line = line.replace("\n\n","\n")
                    f.write(f'{clean_line}\n\n')

        #Save text from pdf
        with open(f'{output_path}{file.split(".")[0]}.txt', 'w') as f:
            for line in text_list:
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
    data = {'user_id':output_path.split("/")[1]}

    print('INFO: Langchain Process',flush=True)
    # Send the POST request
    response = requests.post(api_url, files=files, data=data)

    # Print the response
    print(response.text)

if __name__ == '__main__':
    socketio.run(app)
