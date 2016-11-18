FROM ubuntu:14.04
MAINTAINER jobevers@lbry.io

ADD lbrycrdd /usr/local/bin/lbrycrdd
# contains 150 blocks, used to bootstrap the network
ADD data /data

VOLUME /data
EXPOSE 19000 19001

CMD ["/usr/local/bin/lbrycrdd", "-datadir=/data/lbrycrd"]
