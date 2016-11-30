#!/bin/bash

# lbrycrdd is set to daemon-fy
/usr/local/bin/lbrycrdd -datadir=/data/lbrycrd

# this python is the one installed in the virtualenv
/app/bin/python /app/bin/start-lighthouse --lbrycrdd-data-dir /data/lbrycrd
