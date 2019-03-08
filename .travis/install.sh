#!/usr/bin/env bash

# workaround for incomatibility of default ubuntu 16.04 and tango configuration
if [ $1 = "ubuntu16.04" ]; then
    docker exec -it --user root ndts sed -i "s/\[mysqld\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION/g" /etc/mysql/mysql.conf.d/mysqld.cnf
fi

echo "restart mysql"
docker exec -it --user root ndts service mysql stop
docker exec -it --user root ndts /bin/sh -c '$(service mysql start &) && sleep 30'

docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y   tango-db tango-common; sleep 10'
if [ $? -ne "0" ]
then
    exit -1
fi
echo "install tango servers"
docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java'
if [ $? -ne "0" ]
then
    exit -1
fi

docker exec -it --user root ndts service tango-db restart
docker exec -it --user root ndts service tango-starter restart

if [ $2 = "2" ]; then
    echo "install python-pytango"
    docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y python-enum34 python-pytango python-tz; apt-get -qq install -y nxsconfigserver-db; sleep 10'
else
    echo "install python3-pytango"
    docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y git python3-six python3-numpy graphviz python3-sphinx g++ build-essential python3-dev pkg-config python3-all-dev  python3-setuptools libtango-dev python3-pytango python3-tz python-pytango python-enum34; apt-get -qq install -y nxsconfigserver-db; sleep 10'
    if [ $1 = "debian10" ]; then
	docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y libboost-python1.62-dev libboost1.62-dev'
    else
	docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y libboost-python-dev libboost-dev'
    fi

    if [ $1 -ne "debian10" ]; then
	docker exec -it --user root ndts /bin/sh -c 'git clone https://github.com/tango-controls/pytango pytango; git checkout tags/v9.2.5 -b b9.2.5'
	docker exec -it --user root ndts /bin/sh -c 'cd pytango; python3 setup.py install'
    fi
fi
if [ $? -ne "0" ]
then
    exit -1
fi

if [ $1 = "debian8" ]; then
    if [ $2 = "3" ]; then
	echo "install python3-mysqldb"
	docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y -t=jessie-backports  python3-mysqldb'
    fi
fi

if [ $2 = "2" ]; then
    echo "install sardana, taurus and nexdatas"
    docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y  python-nxsconfigserver python-nxswriter python-nxstools'
else
    echo "install sardana, taurus and nexdatas"
    docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y  python3-nxsconfigserver python3-nxswriter python3-nxstools'
fi
if [ $? -ne "0" ]
then
    exit -1
fi


if [ $2 = "2" ]; then
    echo "install python-nxsrecselector"
    docker exec -it --user root ndts python setup.py -q install
else
    echo "install python3-nxsrecselector"
    docker exec -it --user root ndts python3 setup.py -q install
fi
if [ $? -ne "0" ]
then
    exit -1
fi
