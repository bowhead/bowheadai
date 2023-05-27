FROM --platform=linux/amd64 continuumio/anaconda3

WORKDIR /api

COPY environment.yaml .
COPY main.py .

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0
RUN apt-get -o Dpkg::Options::="--force-confmiss" install --reinstall netbase

RUN conda config --add channels conda-forge
RUN conda env create --file environment.yaml

ENTRYPOINT [ "conda", "run", "--no-capture-output", "-n", "paddle", "gunicorn", "-b", "0.0.0.0:8000", "-k", "eventlet", "-w", "1", "main:app"]