FROM python:3.12-bookworm

EXPOSE 80 443 22
EXPOSE 5000
EXPOSE 7000-8000
EXPOSE 8080
EXPOSE 5000

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /app

WORKDIR /app


ENTRYPOINT [ "flask", "run", "--host=0.0.0.0" ]