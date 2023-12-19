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
from dotenv import load_dotenv
import re

from queue import Queue
import sys
from flask import Response, stream_with_context
import threading 


import time
from langchain.text_splitter import RecursiveCharacterTextSplitter, Document
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser

import json

sys.setrecursionlimit(1000)
# Load environment variables from .env file
load_dotenv()

# Access the URL variables
api_url = getenv('LANGCHAIN_UPLOAD_ENDPOINT')
delete_url = getenv('LANGCHAIN_DELETE_ENDPOINT')
cors_domains = getenv('CORS_DOMAINS').split(',')
cookie_domain = getenv('COOKIE_DOMAIN')
app = Flask(__name__)
app.secret_key = getenv('SECRET_KEY', '')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_DOMAIN'] = cookie_domain
app.config['REMEMBER_COOKIE_SAMESITE'] = 'None'
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_DOMAIN'] = cookie_domain

CORS(app, supports_credentials=True, origins=cors_domains)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
Session(app)

socketio = SocketIO(app, cors_allowed_origins=cors_domains, manage_session=False)

# load from disk
instructor_embeddings = HuggingFaceInstructEmbeddings(model_name = 'hkunlp/instructor-base')
db3 = Chroma(persist_directory="./ovarian-cancer", embedding_function=instructor_embeddings)
# create the open-source embedding function
retriever = db3.as_retriever(
    search_type="mmr",  # Also test "similarity"
    search_kwargs={"k": 3},
)

prompt = PromptTemplate.from_template(
    """
    *** Instructions ***
    Use the following pieces of context about clinical trials to answer the user's question. Add the necessary information about the trials. If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    *** Context *** 
    page_content='Inclusion Criteria:
    Clinical diagnosis of epithelial ovarian cancer stage III
    nctId: NCT05212779

    page_content='Inclusion Criteria:
    Women with stage III-IV ovarian cancer, undergoing interval (after 3-4 cycles of chemotherapy) or delayed (\>5 cycles of chemotherapy) cytoreductive surgeries or no cytoreductive surgery (\>5 cycles of chemotherapy alone.
    nctId: NCT05523804
    
    page_content='Inclusion Criteria:
    * Minimum age 18 years
    * Signed informed consent form
    * Confirmed diagnosis of ovarian cancer except low grade serous, clear cell and mucinous histology
    * Where patients are treatment naïve, patients need to have disease stage FIGO (International Federation of Gynecology and Obstetrics) III or FIGO IV.
    * Patient is expected to receive primary chemotherapy/maintenance after initial surgical debulking or a further line of systemic therapy in the relapsed setting according to treatment guidelines
    * Feasibility of collecting malignant ascites and/or pleural effusion during either primary debulking surgery or a routine drainage procedure prior to initiation of the first or next line of systemic therapy
    * ECOG (Eastern Cooperative Oncology Group) stage 0-2
    nctId: NCT06068738
    
    *** User's Question ***
    {question}"""
)

runnable = prompt | ChatOpenAI(model="gpt-3.5-turbo") | StrOutputParser()


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
    for folder in ["temp/","images/","output/", "vectors/"]:
        dir = folder + uuid + "/"
        try:
            shutil.rmtree(dir)
            print(f"INFO: folder {dir} delete suscesfully", flush=True)
        except OSError as e:
            #pass
            print("Error: %s - %s." % (e.filename, e.strerror), flush=True)

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



@app.route('/send-message', methods=['GET', 'POST'])
@login_required
def send_message():
    message = request.json.get('message', '')
    response = runnable.invoke({"question": message})
    return jsonify({'response': response})

    
if __name__ == '__main__':
    socketio.run(app)
