FROM python:3.12.1-bookworm

EXPOSE 80
EXPOSE 11000

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /app

WORKDIR /app


CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "module:app"]