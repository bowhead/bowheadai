FROM python:3.10-buster

WORKDIR /api

COPY requirements.txt .
COPY main.py .

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 poppler-utils tesseract-ocr

RUN wget https://sqlite.org/2023/sqlite-autoconf-3420000.tar.gz && \
    tar xvfz sqlite-autoconf-3420000.tar.gz && \
    cd sqlite-autoconf-3420000 && \
    ./configure && \
    make && \
    make install && \
    cd .. && \
    rm -rf sqlite-autoconf-3420000 && \
    rm sqlite-autoconf-3420000.tar.gz

RUN pip install -r requirements.txt

ENTRYPOINT [ "gunicorn", "-b", "0.0.0.0:3000", "--reload", "--timeout", "600" ,"-k", "eventlet", "-w", "1", "main:app"]