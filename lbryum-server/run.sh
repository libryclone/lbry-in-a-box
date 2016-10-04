#!/bin/bash

lbrycrdd -datadir=/data/lbrycrd &
runuser -l lbryum -c 'run_lbryum_server.py --conf=/etc/lbryum.conf'
