#!/bin/bash
# This is a hack to ensure that lbrynet always starts up after lbryum-server is finished syncing
sleep 20
/app/bin/python /app/bin/lbrynet-daemon --verbose

