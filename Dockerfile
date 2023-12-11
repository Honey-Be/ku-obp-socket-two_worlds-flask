FROM python:3.12.1-slim-bookworm


EXPOSE 11000

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /app

WORKDIR /app


CMD ["python3", "app.py"]