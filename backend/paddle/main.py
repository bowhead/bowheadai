from flask import Flask, request
from flask_cors import CORS
from pdf2image import convert_from_path
import os
import cv2
from paddleocr import PPStructure,draw_structure_result,save_structure_res, PaddleOCR
import requests
import shutil

app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_files():
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

    # Process each uploaded file
    for file in uploaded_files:
        
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
    paddle_process()
    
    
    print('INFO: Create Vector')
    post_files()

    
        
    
    return 'Files uploaded successfully'


def pdf_to_img():
    pages = convert_from_path('foobar.pdf', 500)
    for count, page in enumerate(pages):
        page.save(f'images/prueba{count}.jpg', 'JPEG')

def paddle_process():
    #table_engine = PPStructure(show_log=False)
    ocr = PaddleOCR(show_log=False)

    save_folder = './output'
    files = os.listdir('images/')

    for file in files:
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

    print('INFO: Files complete')
    # Send the POST request
    response = requests.post('http://localhost:3001/upload', files=files)

    # Print the response
    print(response.text)

if __name__ == '__main__':
    app.run()