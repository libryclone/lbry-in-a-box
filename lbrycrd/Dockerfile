FROM ubuntu:14.04
MAINTAINER jobevers@lbry.io

ADD lbrycrdd /usr/local/bin/lbrycrdd
ADD lbrycrd.conf /data/lbrycrd/lbrycrd.conf

VOLUME /data
EXPOSE 19000 19001

CMD ["/usr/local/bin/lbrycrdd", "-datadir=/data/lbrycrd"]
