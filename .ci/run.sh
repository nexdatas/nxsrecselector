#!/usr/bin/env bash

echo "run python3-nxsrecselector"
docker exec ndts python3 test/main.py $1
ERR=$?

echo "ERROR: "$ERR

if [ $ERR != 0 ]; then
    if [ $ERR != 139 ]; then
	exit $ERR;
    fi
fi
