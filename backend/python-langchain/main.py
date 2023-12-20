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
from models.User import User
from queue import Queue
import sys
from flask import Response, stream_with_context
import threading 
from langchain.text_splitter import RecursiveCharacterTextSplitter, Document
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser

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
instructor_embeddings = HuggingFaceInstructEmbeddings(model_name='hkunlp/instructor-base')
db3 = Chroma(persist_directory="./ovarian-cancer-vector", embedding_function=instructor_embeddings)
# create the open-source embedding function
retriever = db3.as_retriever(
    search_type="mmr",  # Also test "similarity"
    search_kwargs={"k": 6},
)

prompt = PromptTemplate.from_template(
    """
    *** Instructions ***
    Use the following pieces of context about clinical trials to answer the user's question. Add the necessary information about the trials. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    *** Context ***
    {context}

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
    for folder in ["temp/", "images/", "output/", "vectors/"]:
        dir = folder + uuid + "/"
        try:
            shutil.rmtree(dir)
            print(f"INFO: folder {dir} delete suscesfully", flush=True)
        except OSError as e:
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
# @login_required
def send_message():
    message = request.json.get('message', '')
    docs = retriever.get_relevant_documents(message)
    text = ""
    for doc in docs:
        text += f"""Clinical trial nctId: {doc.metadata["nctId"]}
    Information: {doc.page_content}

    """
    response = runnable.invoke({"question": message, "context": text})
    return jsonify({'response': response})


if __name__ == '__main__':
    socketio.run(app)
