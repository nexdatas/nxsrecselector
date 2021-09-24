#!/usr/bin/env bash

# workaround for incomatibility of default ubuntu 16.04 and tango configuration
if [ "$1" = "ubuntu16.04" ]; then
    docker exec --user root ndts sed -i "s/\[mysqld\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION/g" /etc/mysql/mysql.conf.d/mysqld.cnf
fi
if [ "$1" = "ubuntu20.04" ]; then
    docker exec --user root ndts sed -i "s/\[mysql\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,NO_ENGINE_SUBSTITUTION\ncharacter_set_server=latin1\ncollation_server=latin1_swedish_ci\n\[mysql\]/g" /etc/mysql/mysql.conf.d/mysql.cnf
fi

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

docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y   tango-db tango-common; sleep 10'
if [ "$?" -ne "0" ]; then exit 255; fi

echo "install tango servers"
docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java'
if [ "$?" -ne "0" ]; then exit 255; fi

docker exec --user root ndts service tango-db restart
docker exec --user root ndts service tango-starter restart

if [ "$2" = "2" ]; then
    echo "install python-pytango"
    docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y  python-setuptools python-enum34 python-pytango python-tz; apt-get -qq install -y nxsconfigserver-db; sleep 10'
else
    echo "install python3-pytango"
    docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y libboost-python-dev libboost-dev git python3-six python3-numpy graphviz python3-sphinx g++ build-essential python3-dev pkg-config python3-all-dev  python3-setuptools libtango-dev python3-tz'
    if [ "$1" = "debian10" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "debian11" ]; then
	echo " "
	docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y python3-tango; apt-get -qq install -y nxsconfigserver-db; sleep 10'
	# docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y libboost-python1.62-dev libboost1.62-dev'
    else
	docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y python3-pytango; apt-get -qq install -y nxsconfigserver-db; sleep 10'
	docker exec --user root ndts /bin/bash -c 'git clone https://gitlab.com/tango-controls/pytango pytango; cd pytango; git checkout tags/v9.2.5 -b b9.2.5'
	docker exec --user root ndts /bin/bash -c 'cd pytango; python3 setup.py install'
    fi

fi
if [ "$?" -ne "0" ]; then exit 255; fi


if [ "$1" = "debian8" ]; then
    if [ "$2" = "3" ]; then
	echo "install python3-mysqldb"
	docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y -t=jessie-backports  python3-mysqldb'
    fi
fi

if [ "$2" = "2" ]; then
    echo "install sardana, taurus and nexdatas"
    docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y  python-nxsconfigserver python-nxswriter python-nxstools'
else
    echo "install sardana, taurus and nexdatas"
    docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get install -y  python3-nxsconfigserver python3-nxswriter python3-nxstools'
fi
if [ "$?" -ne "0" ]; then exit 255; fi

docker exec --user root ndts chown -R tango:tango .

if [ "$2" = "2" ]; then
    echo "install python-nxsrecselector"
    docker exec --user root ndts python setup.py -q install
else
    echo "install python3-nxsrecselector"
    docker exec --user root ndts python3 setup.py -q install
fi
if [ "$?" -ne "0" ]
then
    exit 255
fi
