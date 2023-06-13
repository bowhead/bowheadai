from functools import wraps
from flask import Flask, request, session, jsonify
from flask_cors import CORS
import os
from os import getenv
import requests
import shutil
from flask_socketio import SocketIO, emit, disconnect
from flask_session import Session
from flask_login import login_user, current_user, LoginManager, login_required
from os import getenv
from dotenv import load_dotenv
from pathvalidate import sanitize_filename

from pypdf import PdfReader
import os
from PIL import Image
import pytesseract

from models.User import User

# Load environment variables from .env file
load_dotenv()

# Access the URL variables
api_url = getenv('LANGCHAIN_UPLOAD_ENDPOINT')
delete_url = getenv('LANGCHAIN_DELETE_ENDPOINT')
cors_domains = getenv('CORS_DOMAINS').split(',')
app = Flask(__name__)
app.secret_key = getenv('SECRET_KEY', '')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'None'
app.config['REMEMBER_COOKIE_SECURE'] = True

CORS(app, supports_credentials=True)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
Session(app)

socketio = SocketIO(app, cors_allowed_origins=cors_domains, manage_session=False)


def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


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
   

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/login', methods=['POST'])
def login():
    if request.cookies.get('session'):
        return jsonify({'status': 200}), 200

    session['foo'] = 'barbar'
    uuid = request.json.get('uuid')
    user = User(uuid)
    login_user(user, remember=True, force=True)
    return jsonify({'status': 200, 'userId': uuid}), 200


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_files():
    delete_old_files = request.form.get('deleteOldFiles', 'true') == 'true'
    session['progress'] = 10
    session['message'] = 'Processing files'
    
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
    session['progress'] = 33
    session['message'] = 'Extracting key information'
    pypdf_process(old_files, images_path, output_path, temp_path)
    
    session['progress'] = 66
    session['message'] = 'Training model'
    print('INFO: Create Vector')
    post_files(output_path)
    
    session['progress'] = 100
    
    session['message'] = 'All done!'
    return 'Files uploaded successfully'


@app.route('/progress')
def progress():
    return jsonify({'progress': session.get('progress', 0), 'message': session.get('message', '')})


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
