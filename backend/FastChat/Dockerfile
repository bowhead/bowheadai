FROM nvidia/cuda:12.2.0-runtime-ubuntu20.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -y && apt-get install -y python3.9 python3.9-distutils curl git

# Set working directory and copy 'fastchat' folder
WORKDIR /app
COPY fastchat /app/fastchat

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.9 get-pip.py
RUN pip3 install fschat[model_worker,webui] pydantic==1.10.13
RUN pip3 install huggingface_hub[cli]
RUN pip3 install bitsandbytes
RUN pip3 install scipy