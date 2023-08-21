FROM python:3.9.7
ENV TZ="America/New_York"
RUN mkdir -p /usr/src/microservice
WORKDIR /usr/src/microservice
COPY . .
RUN mkdir -p /usr/src/microservice/.states
RUN pip3 install -r requirements.txt
CMD python3 src/app.py