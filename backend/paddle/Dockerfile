FROM --platform=linux/amd64 continuumio/anaconda3

WORKDIR /api

COPY environment.yaml .
COPY main.py .

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0

RUN conda config --add channels conda-forge
RUN conda env create --file environment.yaml

ENTRYPOINT [ "conda", "run", "--no-capture-output", "-n", "paddle", "python", "main.py"]