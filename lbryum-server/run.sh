#!/bin/bash

# lbrycrdd is set to daemon-fy
/usr/local/bin/lbrycrdd -datadir=/data/lbrycrd
runuser -l lbryum -c 'run_lbryum_server.py --conf=/etc/lbryum.conf'
