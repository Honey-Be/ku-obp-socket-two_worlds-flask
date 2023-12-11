FROM python:3.12.1-slim-bookworm

EXPOSE 80
EXPOSE 11000

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /app

WORKDIR /app


CMD ["uwsgi" "--http" ":5000" "--gevent" "1000" "--http-websockets" "--master" "--wsgi-file" "app.py" "--callable" "app"]