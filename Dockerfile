FROM python:3.12.1-bookworm

EXPOSE 80 443 22
EXPOSE 5000
EXPOSE 7000-8000
EXPOSE 8080
EXPOSE 11000

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /app

WORKDIR /app


CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "module:app"]