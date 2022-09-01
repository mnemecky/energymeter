FROM python:3.9-alpine

RUN mkdir /install
WORKDIR /install

RUN apk add --update-cache libusb libusb-compat
COPY requirements.txt /
RUN pip install -r /requirements.txt

STOPSIGNAL SIGINT
COPY src /app
WORKDIR /app

CMD [ "python", "-u", "/app/energymeter.py" ]
