#!/bin/bash
# This is a hack to ensure that lbrynet always starts up after lbryum-server is finished syncing
sleep 10
/app/bin/python /app/bin/lbrynet-daemon --log-to-console --no-launch --verbose

