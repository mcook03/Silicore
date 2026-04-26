FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
COPY frontend/package.json /app/frontend/package.json
COPY frontend/package-lock.json /app/frontend/package-lock.json

RUN pip install --no-cache-dir -r /app/requirements.txt
RUN cd /app/frontend && npm ci

COPY . /app
RUN cd /app/frontend && npm run build

EXPOSE 5001

CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
