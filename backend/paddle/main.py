from flask import Flask, request
from flask_cors import CORS
from pdf2image import convert_from_path
import os
import cv2
from paddleocr import PPStructure,draw_structure_result,save_structure_res, PaddleOCR
import requests
import shutil
#from dotenv import load_dotenv
from flask_socketio import SocketIO, emit

# Load environment variables from .env file
#load_dotenv()

# Access the URL variables
api_url = "http://langchain:3001/upload"

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/upload', methods=['POST'])
def upload_files():
    #delete_old_files = True

    # Get the value of deleteOldFiles from the form data
    delete_old_files = request.form.get('deleteOldFiles', 'true') == 'true'
    
    
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
                shutil.rmtree(os.path.join(dir, f))
    
    # Check if files were sent
    if 'files' not in request.files:
        return 'No files uploaded', 400
    
    uploaded_files = request.files.getlist('files')

    # Get the names of the old files
    old_files = get_file_names('temp/') + get_file_names('images/')
    
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
            file.save("temp/"+file.filename)
            # Convert PDF to images
            images = convert_from_path('temp/'+file.filename)
            
            # Save each image
            for i, image in enumerate(images):
                image_path = f"{filename[0]}_{i}.jpg"
                image.save('images/'+image_path)
                # You can perform additional operations on the image here
                
                # Remove the original PDF file
        else:
            file.save("output/"+file.filename)
    
    print('INFO: Paddle Process')
    socketio.emit('progress', {'progress': 33})      
    paddle_process(old_files)
    
    socketio.emit('progress', {'progress': 66})
    print('INFO: Create Vector')
    post_files()

        
    
    return 'Files uploaded successfully'

def get_file_names(dir):
    if os.path.exists(dir):
        return [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    return []

def paddle_process(old_files):
    #table_engine = PPStructure(show_log=False)
    

    save_folder = './output'
    files = os.listdir('images/')

   
    
    ocr = PaddleOCR(show_log=False)
    for file in files:
        if file in old_files:
            print(f'INFO: Skipping image {file}, already processed')
            continue
        print('INFO: Paddle Process ' + file)

        img_path = f'images/{file}'
        img = cv2.imread(img_path)
        #result = table_engine(img)
        result = ocr.ocr(img_path)
        #print(os.path.basename(img_path).split('.')[0])
        #save_structure_res(result, save_folder,os.path.basename(img_path).split('.')[0])
        txts = [line[1][0] for line in result[0]]
        
        with open(f'output/{file.split(".")[0]}.txt', 'w') as f:
            for line in txts:
                f.write(f"{line}\n")

def post_files():
    folder_path = 'output/'

    # Get all file paths in the folder
    file_paths = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path)]

    # Prepare the files dictionary
    files = []
    for file_path in file_paths:
        with open(file_path, 'rb') as file:
            file_content = file.read() 
        files.append(('files', (file_path, file_content, 'application/octet-stream')))

    print('INFO: Langchain Process')
    # Send the POST request
    response = requests.post(api_url, files=files)

    # Print the response
    print(response.text)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)