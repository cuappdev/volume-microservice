FROM python:3.9.7
RUN mkdir -p /usr/src/microservice
WORKDIR /usr/src/microservice
COPY . .
RUN pip3 install -r requirements.txt
CMD python3 app.py