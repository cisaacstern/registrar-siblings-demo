FROM docker:latest

RUN apk update && apk add py3-pip

RUN pip install click pygithub

COPY ./app.py app.py

COPY ./recipe-handler-demo /recipe-handler-demo/

ENTRYPOINT ["python3", "app.py"]
