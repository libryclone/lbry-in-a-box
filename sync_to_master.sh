#!/bin/bash
# Sync all lbry repos to master
# if supplied with argument, sync lbry to that tag instead

if [ $# -ge 1 ]
then
    tag=$1
else
    tag=origin/master
fi

(cd lbrynet/lbry; git fetch origin; git checkout $tag)
(cd lighthouse/lbry; git fetch origin; git checkout $tag)
(cd lbrynet/lbryum; git fetch origin; git checkout origin/master)
(cd lbryum-server/lbryum-server; git fetch origin; git checkout origin/master)
(cd lighthouse/lighthouse; git fetch origin; git checkout origin/master)
