FROM python:3.11-bookworm

EXPOSE 80 443 22
EXPOSE 5000
EXPOSE 7000-8000
EXPOSE 8080
EXPOSE 11000

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /app

WORKDIR /app


CMD ["uwsgi", "--http", ":11000", "--gevent", "1000", "--http-websockets", "--master", "--wsgi-file", "app.py", "--callable", "app"]