#!/usr/bin/env bash

# workaround for a bug in debian9, i.e. starting mysql hangs
if [ "$1" = "debian11" ] || [ "$1" = "debian12" ] || [ "$1" = "debian13" ] || [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu26.10py" ] || [ "$1" = "ubuntu26.04" ]; then
    docker exec --user root ndts service mariadb restart
else
    docker exec --user root ndts service mysql stop
    if [ "$1" = "ubuntu22.04" ] || [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ]; then
	docker exec --user root ndts /bin/bash -c 'usermod -d /var/lib/mysql/ mysql'
    fi
    docker exec --user root ndts service mysql start
    # docker exec  --user root ndts /bin/bash -c '$(service mysql start &) && sleep 30'
fi

docker exec  --user root ndts chown -R tango:tango .

echo "install tango-common"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y tango-common; sleep 10'
if  [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu25.04" ] || [ "$1" = "ubuntu26.04" ]; then
    # docker exec  --user tango ndts /bin/bash -c '/usr/lib/tango/DataBaseds 2 -ORBendPoint giop:tcp::10000  &'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=root\npassword=rootpw" > /root/.my.cnf'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=localhost\npassword=rootpw" > /var/lib/tango/.my.cnf'
    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"%" identified by "rootpw"'
    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"localhost" identified by "rootpw"'
    docker exec  --user root ndts /usr/bin/mysql -e 'FLUSH PRIVILEGES'
fi
if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ] || [ "$1" = "ubuntu21.10" ] || [ "$1" = "ubuntu22.04" ]; then
    # docker exec  --user tango ndts /bin/bash -c '/usr/lib/tango/DataBaseds 2 -ORBendPoint giop:tcp::10000  &'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=root\npassword=rootpw" > /root/.my.cnf'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=127.0.0.1\npassword=rootpw" > /var/lib/tango/.my.cnf'
fi

if   [ "$1" = "ubuntu26.10py" ]; then
    # docker exec  --user tango ndts /bin/bash -c '/usr/lib/tango/DataBaseds 2 -ORBendPoint giop:tcp::10000  &'
    docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=root\npassword=rootpw" > /root/.my.cnf'
    docker exec  --user tango ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=localhost\npassword=rootpw" > /var/lib/tango/.my.cnf'
    docker exec  --user tango ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=localhost\npassword=rootpw" > /home/tango/.my.cnf'
    # docker exec  --user root ndts /bin/bash -c 'echo -e "[client]\nuser=tango\nhost=127.0.0.1\npassword=rootpw" > /var/lib/tango/.my.cnf'
    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"%" identified by "rootpw"'
    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON tango.* TO "tango"@"localhost" identified by "rootpw"'
    docker exec  --user root ndts /usr/bin/mysql -e 'FLUSH PRIVILEGES'
    # docker exec --user tango ndts /usr/bin/bash  -c 'pwd'
    # docker exec --user tango ndts /usr/bin/bash  -c 'echo "$TANGO_HOST"'
    # docker exec --user tango ndts /usr/bin/mysql -e 'show databases;'
fi

echo "install tango-db"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y tango-db; sleep 10'
if [ "$?" -ne "0" ]; then exit 255; fi
if  [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu26.10py" ] || [ "$1" = "ubuntu26.04" ]; then
    docker exec  --user tango ndts /usr/bin/mysql -e 'create database tango'
    docker exec  --user tango ndts /bin/bash -c '/usr/bin/mysql tango < /usr/share/dbconfig-common/data/tango-db/install/mysql'
fi

if   [ "$1" = "ubuntu26.10py" ] ; then
    docker exec  --user tango ndts /bin/bash -c '/usr/lib/tango/Databaseds 2   -ORBendPoint giop:tcp::10000  &'
    # docker exec  --user root ndts /bin/bash -c 'ps -ef | grep Databaseds'
    # docker exec  --user root ndts /bin/bash -c 'ps -ef | grep tango'
else
    docker exec  --user root ndts service tango-db restart
fi


echo "install tango servers"
docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive;  apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java'
if [ "$?" -ne "0" ]; then exit 255; fi

if   [ "$1" = "ubuntu26.10py" ] ; then
    echo "status tango-starter"
    # docker exec --user root ndts service tango-starter status
    # docker exec  --user root ndts /bin/bash -c 'ps -ef | grep Starter'
    # echo "start  STARTER"
    docker exec  --user tango ndts /bin/bash -c '/usr/bin/tango_admin --add-server Starter/$(hostname) Starter tango/admin/$(hostname)'
    docker exec  --user tango ndts /bin/bash -c '/usr/lib/tango/Starter $(hostname) &'
    docker exec  --user root ndts /bin/bash -c 'ps -ef | grep Starter'
    # docker exec --user root ndts systemctl restart tango-starter.service
    # docker exec --user root ndts systemctl status tango-starter.service
    # docker exec  --user root ndts service tango-db status
else
    docker exec --user root ndts service tango-starter restart
fi

if [ "$2" = "2" ]; then
    echo "install pytango and nxsconfigserver-db"
    docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get install -y   python-pytango  nxsconfigserver-db ; sleep 10'
else
    if [ "$1" = "debian10" ] || [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu26.10py" ] || [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu25.04" ] || [ "$1" = "ubuntu26.04" ] || [ "$1" = "debian11" ] || [ "$1" = "debian12" ] || [ "$1" = "debian13" ] ; then
	echo "install pytango"
	docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get install -y   python3-tango'
	echo "install nxsconfigserver-db"
	docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get  install -y   nxsconfigserver-db'
	if [ "$1" = "ubuntu24.04" ] || [ "$1" = "ubuntu25.04" ] || [ "$1" = "ubuntu26.04" ]; then
	    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON nxsconfig.* TO "tango"@"%" identified by "rootpw"'
	    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON nxsconfig.* TO "tango"@"localhost" identified by "rootpw"'
	    docker exec  --user root ndts /usr/bin/mysql -e 'FLUSH PRIVILEGES'
	    docker exec  --user tango ndts /usr/bin/mysql -e 'create database nxsconfig'
	    docker exec  --user tango ndts /bin/bash -c '/usr/bin/mysql nxsconfig < /usr/share/dbconfig-common/data/nxsconfigserver-db/install/mysql'
	fi
	if [ "$1" = "ubuntu26.10py" ]; then
	    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON nxsconfig.* TO "tango"@"%" identified by "rootpw"'
	    docker exec  --user root ndts /usr/bin/mysql -e 'GRANT ALL PRIVILEGES ON nxsconfig.* TO "tango"@"localhost" identified by "rootpw"'
	    docker exec  --user root ndts /usr/bin/mysql -e 'FLUSH PRIVILEGES'
	fi
    else
	echo "install pytango and nxsconfigserver-db"
	docker exec  --user root ndts /bin/bash -c 'apt-get -qq update; apt-get -qq install -y   python3-pytango nxsconfigserver-db; sleep 10'
    fi
fi
if [ "$?" != "0" ]; then exit 255; fi


echo "install nxs packages"
if [ "$2" = "2" ]; then
    echo "install python-pytango"
    docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get install -y python-nxsconfigserver python-nxswriter python-nxstools; sleep 10'
else
    docker exec --user root ndts /bin/bash -c 'apt-get -qq update; apt-get install -y python3-nxsconfigserver python3-nxswriter python3-nxstools; sleep 10'
fi
if [ "$?" != "0" ]; then exit 255; fi


echo "install nxsrecselector"
if [ "$2" = "2" ]; then
    docker exec --user root ndts python setup.py -q install
else
    docker exec ndts mkdir build
    if [ "$1" = "ubuntu22.04" ] ; then
	docker exec --user root ndts python3 -m pip install . -vv  --no-deps --no-build-isolation
    else
	docker exec --user root ndts python3 -m pip install . -vv  --no-deps --no-build-isolation  --break-system-packages --root-user-action=ignore
    fi    
    # if [ "$?" != "0" ]; then exit 255; fi

    echo "build python3-nxstools docs"
    docker exec ndts mkdir doc/_static
    docker exec ndts sphinx-build  doc build/sphinx/html
fi
if [ "$1" != "ubuntu26.04" ] && [ "$1" != "ubuntu26.04py" ] && [ "$?" != "0" ]; then exit 255; fi

if  [ "$1" = "debian13py" ] || [ "$1" = "ubuntu26.04py" ] || [ "$1" = "ubuntu26.10py" ] ; then
    echo "remove python3-mysqldb"
    docker exec  --user root ndts /bin/bash -c 'apt-get  install -y   python3-pymysql'
    docker exec  --user root ndts /bin/bash -c 'apt-get  remove -y   python3-mysqldb'
fi
