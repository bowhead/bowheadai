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
from langchain.document_loaders import DirectoryLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.agents.tools import Tool
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.prompts import StringPromptTemplate
from langchain import LLMChain
from typing import List, Union
from langchain.schema import AgentAction, AgentFinish, OutputParserException
import re
from langchain.prompts import PromptTemplate
from src.pupmed import PubMedRetriever
from langchain.memory import ConversationBufferMemory, ReadOnlySharedMemory

import sys

sys.setrecursionlimit(1000)
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

# *** TEMPLATE ***
template = """Answer the following questions as best you can, You are a friendly, conversational personal medical assistant. 
You have access to the following tools:

{tools}

You must show information about user data, find insights between data with the tool health-documents-vector. If is necessary you should give health recommendations with pubmed-query-search tool about the user health problems, always making it clear that users should consult a specialist.

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times until there is enough information to answer the Question)
Thought: I now know the final answer
Final Answer: the final answer to the original input question, adding all necessary information and sources, should be a json with the keys: answer and source, source should be a list of uids

Chat history:
{chat_history}

New question: {input}
{agent_scratchpad}"""

# *** Set up a prompt template ***
class CustomPromptTemplate(StringPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)

# *** Output Parser ***
class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
    
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

@app.route('/send-message', methods=['GET', 'POST'])
#@login_required
def send_message():
    message = request.json.get('message', '')
    history = request.json.get('history', '')
    userId = sanitize_filename(request.json.get('userId', ''))
    print('INFO: Message recived: ' + message, flush=True)

     # ************ HEALTH DATA VECTOR ************
    llm = OpenAI(temperature=0)

    embeddings = OpenAIEmbeddings()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    if history:
        for num in range(0,len(history),2):
            memory.save_context(history[num], history[num+1])
    #memory.save_context(history)
    readonlymemory = ReadOnlySharedMemory(memory=memory)

    vectorstore = Chroma(persist_directory=f"./vectors/{userId}/", embedding_function=embeddings)

    prompt_template_vector = """Use the following context about medical records to show to the user the information they need, help find exactly what they want. 
    You must give information about user data, especially negative results that may affect the user's health. 

    The context could be in multiple languages. You should always respond in English even if the context is in another language.
    It's ok if you don't know the answer. 

    Context:
    {context}

    Question: {question}
    Answer:"""

    PROMPT = PromptTemplate(
        template=prompt_template_vector, input_variables=["context", "question"]
    )
    chain_type_kwargs = {"prompt": PROMPT}

    health_data_vectorstore = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=vectorstore.as_retriever(), 
        chain_type_kwargs=chain_type_kwargs,
        memory=readonlymemory,
    )

    
    # ************ PUBMED RETRIEVER ************
    pubmed_retriever = PubMedRetriever(top_k_results=5)

    prompt_template_pubmed = """Use the following context about medical articles to respond to the question. Return an answer with metadata ("uid").

    Context:
    {context}

    Question: {question}
    Answer:"""


    PROMPT_PUBMED = PromptTemplate(
        template=prompt_template_pubmed, input_variables=["context", "question"]
    )
    DOC_PROMPT = PromptTemplate(
        template="Answer: {page_content}\nuids: {uid}", input_variables=["page_content", "uid"]
    )

    chain_type_kwargs = {"prompt": PROMPT_PUBMED, "document_prompt":DOC_PROMPT}

    pubmed_chain = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=pubmed_retriever, 
        chain_type_kwargs=chain_type_kwargs,
        memory=readonlymemory
    )

    # ************ TOOLS ************
    tools = [
        Tool(
            name = "pubmed-query-search",
            func = pubmed_chain.run,
            description = "Pubmed Query Search - Useful to obtain health information resources for recommendations from pubmed, the input should be a text for pubmed search"
        ),
        Tool(
            name="health-documents-vector",
            func=health_data_vectorstore.run,
            description="Health Documents QA - useful to obtain information about the users private health data. The input should be the original question",

        )
    ]

    # ************ CUSTOM AGENT ************
    prompt_with_history = CustomPromptTemplate(
        template=template,
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps", "chat_history"]
    )

    output_parser = CustomOutputParser()
    
    # LLM chain consisting of the LLM and a prompt
    llm_chain = LLMChain(llm=ChatOpenAI(model_name='gpt-4'), prompt=prompt_with_history)

    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names
    )

    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory)
    
    result = agent_executor.run(message)
    return jsonify({'response':result})


@app.route('/upload', methods=['GET', 'POST'])
#@login_required
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
    print('INFO: Create Vector', flush=True)
    create_vector(output_path)
    
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

def create_vector(output_path):
    # ************ HEALTH DATA VECTOR ************
    if not os.path.exists('vectors/'): os.makedirs('vectors/')
    llm = OpenAI(temperature=0)

    loader = DirectoryLoader(output_path)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    documents = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings()

    vector_folder = "./vectors/"+output_path[:-1].split("/")[1]

    vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=vector_folder)
    vectorstore.persist()
    
if __name__ == '__main__':
    socketio.run(app)
