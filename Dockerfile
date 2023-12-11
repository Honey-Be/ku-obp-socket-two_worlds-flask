FROM python:3.12.1-slim-bookworm


ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /app

WORKDIR /app

CMD ["flask","--app", "app", "run"]