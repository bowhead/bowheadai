from functools import wraps
from flask import Flask, request, session, jsonify
from flask_cors import CORS
from os import getenv
import shutil
from flask_socketio import SocketIO, emit, disconnect
from flask_session import Session
from flask_login import login_user, current_user, LoginManager, login_required
from os import getenv
from dotenv import load_dotenv
from pathvalidate import sanitize_filename


import os
from dotenv import load_dotenv
import re
from models.User import User
import sys
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser

sys.setrecursionlimit(1000)
# Load environment variables from .env file
load_dotenv()

# Access the URL variables
openai_token = getenv('OPENAI_TOKEN')
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

general_prompt = PromptTemplate.from_template("{question}")
general_runnable = general_prompt | ChatOpenAI(model="gpt-3.5-turbo") | StrOutputParser()

trials_prompt = PromptTemplate.from_template(
    """
    *** Instructions ***
    Use the following pieces of context about clinical trials to answer the user's question. Add the necessary information about the trials. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    *** Context ***
    {context}

    *** User's Question ***
    {question}"""
)
trials_runnable = trials_prompt | ChatOpenAI(model="gpt-3.5-turbo", base_url="https://api.openai.com/v1", api_key=openai_token) | StrOutputParser()

classification_chain = (
    PromptTemplate.from_template(
        """Given the user question below, classify it as either being about `clinicalTrials`, `cancerGuidelines`, or `general`.

Do not respond with more than one word.

<question>
{question}
</question>

Classification:"""
    )
    | ChatOpenAI(model="gpt-3.5-turbo", base_url="https://api.openai.com/v1", api_key=openai_token)
    | StrOutputParser()
)


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
@login_required
def send_message():
    message = request.json.get('message', '')
    docs = retriever.get_relevant_documents(message)
    text = ""

    classification = classification_chain.invoke({"question": message})
    print("classification: `" + classification, flush=True)

    if "clinicaltrials" in classification.lower():
        for doc in docs:
            text += f"""Clinical trial nctId: {doc.metadata["nctId"]} \nInformation: {doc.page_content} \n\n"""
        response = trials_runnable.invoke({"question": message, "context": text})
        return jsonify({'response': response})

    elif "cancerguidelines" or "general" in classification.lower():
        response = general_runnable.invoke({"question": message})
        return jsonify({'response': response})

    else:
        response = general_runnable.invoke({"question": message})
        return jsonify({'response': response})


if __name__ == '__main__':
    socketio.run(app)
