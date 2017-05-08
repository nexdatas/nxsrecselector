#!/usr/bin/env bash

echo "run python-nxsrecselector"
docker exec -it ndts python test/runtest.py $1
if [ $? -ne "0" ]
then
    exit -1
fi
