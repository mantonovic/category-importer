FROM python:3.14.3-slim-trixie

RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    apt-get clean

WORKDIR /app
COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app/src

