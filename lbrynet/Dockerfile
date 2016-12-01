FROM python:2.7
MAINTAINER jobevers@lbry.io

# install the requirements
RUN apt-get update \
 && apt-get install -y  \
      libgmp3-dev build-essential \
      git libssl-dev libffi-dev

# doing the requirements first allows them to be cached
ADD lbry/requirements.txt /src/lbry/requirements.txt
RUN virtualenv /app \
 && /app/bin/pip install -r /src/lbry/requirements.txt

ADD lbryum /src/lbryum
RUN /app/bin/pip install -U /src/lbryum

# build the app from source
ADD lbry/ /src/lbry
RUN /app/bin/pip install /src/lbry

RUN mkdir -p /data /data/lbryum /data/lbrynet \
 && mkdir -p /home/lbry/.lbrynet

VOLUME /data
ADD data /data
ADD lbry-web-ui/dist /data/ui
# this is temporary; eventually all
# lbrynet data should go in /data/lbrynet
VOLUME /home/lbry/.lbrynet


# until Docker fixes the ability to change
# the ownership of ADDed files, we have
# to run as root, unfortunately
# USER lbry


# UPNP would be silly for this
ENV LBRY_USE_UPNP=false

ENV LBRY_LBRYUM_WALLET_DIR=/data/lbryum \
 LBRY_DATA_DIR=/data/lbrynet \
 LBRY_DOWNLOAD_DIR=/data/downloads \
 LBRY_DEFAULT_DHT_NODES=dht:3333 \
 LBRY_BITTREX_FEED=http://fake-bittrex:8003/data \
 LBRY_REFLECTOR_SERVERS=reflector:5566

EXPOSE 3333 4444 5279 5566

CMD ["/app/bin/python", "/app/bin/lbrynet-daemon", "--log-to-console", "--no-launch", "--verbose", "--ui", "/data/ui"]




