#!/usr/bin/env bash

if [ "$2" = "2" ]; then
    echo "run python-nxsrecselector"
    docker exec ndts python test/main.py $1
else
    echo "run python3-nxsrecselector"
    docker exec ndts python3 test/main.py $1
fi
if [ "$?" -ne "0" ]; then exit 255; fi
