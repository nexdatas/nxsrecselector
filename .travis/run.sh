#!/usr/bin/env bash

if [ $2 = "2" ]; then
    echo "run python-nxsrecselector"
    docker exec -it ndts python test/runtest.py $1
else
    echo "run python3-nxsrecselector"
    docker exec -it ndts python3 test/runtest.py $1
fi
if [ $? -ne "0" ]
then
    exit -1
fi
