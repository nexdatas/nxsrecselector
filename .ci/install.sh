#!/usr/bin/env bash

# workaround for a bug in debian9, i.e. starting mysql hangs
if [ "$1" = "debian11" ]; then
    docker exec --user root ndts service mariadb restart
else
    docker exec --user root ndts service mysql stop
    if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ]; then
	# docker exec --user root ndts /bin/bash -c 'mkdir -p /var/lib/mysql'
	# docker exec --user root ndts /bin/bash -c 'chown mysql:mysql /var/lib/mysql'
	docker exec --user root ndts /bin/bash -c 'usermod -d /var/lib/mysql/ mysql'
    fi
    docker exec  --user root ndts /bin/bash -c '$(service mysql start &) && sleep 30'
fi

docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y   tango-db tango-common; sleep 10'
if [ "$?" != "0" ]; then exit 255; fi

echo "install tango servers"
docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y  tango-starter tango-test'
if [ "$?" != "0" ]; then exit 255; fi

docker exec --user root ndts service tango-db restart
docker exec --user root ndts service tango-starter restart
docker exec --user root ndts chown -R tango:tango .


echo "install python3-pytango and nxs packages"
if [ "$2" = "2" ]; then
    echo "install python-pytango"
    docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get install -y python-pytango nxsconfigserver-db python-nxsconfigserver python-nxswriter python-nxstools; sleep 10'
else
    docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get install -y python3-tango nxsconfigserver-db python3-nxsconfigserver python3-nxswriter python3-nxstools; sleep 10'
fi
if [ "$?" != "0" ]; then exit 255; fi


echo "install nxsrecselector"
if [ "$2" = "2" ]; then
    docker exec --user root ndts python setup.py -q install
else
    docker exec --user root ndts python3 setup.py -q install
fi
if [ "$?" != "0" ]; then exit 255; fi
