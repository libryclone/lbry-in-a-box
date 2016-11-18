FROM python:2.7
MAINTAINER jobevers@lbry.io

ADD simple-testing-server/simple-testing-server.py /app/server.py
ADD data.json /app/data.json

EXPOSE 8003

WORKDIR /app
CMD ["/usr/local/bin/python", "server.py"]