FROM python:2.7
MAINTAINER jobevers@lbry.io

ADD lbrycrdd /usr/local/bin/lbrycrdd
ADD lbrycrd.conf /data/lbrycrd/lbrycrd.conf


# Need to install all of the lbrynet and its requirements

################
# Copied from the lbrynet Dockerfile

RUN apt-get update \
 && apt-get install -y  \
      libgmp3-dev build-essential \
      git libssl-dev libffi-dev

# doing the requirements first allows them to be cached
ADD lbry/requirements.txt /src/lbry/requirements.txt
RUN virtualenv /app \
 && /app/bin/pip install -r /src/lbry/requirements.txt

# I don't think we need lbryum
# build the app from source
ADD lbry/ /src/lbry
RUN /app/bin/pip install /src/lbry

# End of copied setup
################

# TODO: we should have a requirements.txt file

ADD lighthouse /src/lighthouse
RUN /app/bin/pip install /src/lighthouse

# Would probably be worthwhile to actually add some
# process management to this, but this works for now.
ADD run.sh /usr/local/bin/run.sh
CMD ["/usr/local/bin/run.sh"]
