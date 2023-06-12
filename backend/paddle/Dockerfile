FROM --platform=linux/amd64 paddlepaddle/paddle:2.5.0rc0-cpu

WORKDIR /api

COPY requirements.txt .
COPY main.py .

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 poppler-utils tesseract-ocr

RUN pip install -r requirements.txt

ENTRYPOINT [ "gunicorn", "-b", "0.0.0.0:3000", "--timeout", "600" ,"-k", "eventlet", "-w", "1", "main:app"]