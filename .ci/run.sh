#!/usr/bin/env bash

if [ "$2" = "2" ]; then
    echo "run python-nxsrecselector"
    docker exec ndts python test/main.py $1
else
    echo "run python3-nxsrecselector"
    docker exec ndts python3 test/main.py $1
fi
ERR=$?

echo "ERROR: "$ERR

if [ $ERR != 0 ]; then
    if [ $ERR != 139 ]; then
	exit $ERR;
    fi
fi
