#!/usr/bin/env bash

echo "install pixi"
docker exec  ndts /bin/bash -c 'mkdir /home/tango/bin; cp /home/tango/test/TestServer2 /home/tango/bin/TestServer ; cp /home/tango/test/MacroServer2 /home/tango/bin/MacroServer'
# docker exec  ndts /bin/bash -c 'curl -fsSL https://pixi.sh/install.sh | sh ; export PATH=/var/lib/tango/.pixi/bin:$PATH ; pixi shell-hook  --manifest-path .github/workflows/pixi/pixi.toml > .sh.sh ; source .sh.sh ; pixi add  --manifest-path .github/workflows/pixi/pixi.toml rattler-build numpy pytango'
# docker exec  ndts /bin/bash -c 'curl -fsSL https://pixi.sh/install.sh | sh ; export PATH=/var/lib/tango/.pixi/bin:$PATH ; cp .github/workflows/pixi/pixi.toml . ; pixi shell-hook  > .sh.sh ; source .sh.sh ; pixi add   numpy pytango  setuptools pip wheel argcomplete lxml pytz pyyaml "pytango==10.0.4" python-dateutil pninexus fabio h5py matplotlib-base blissdata pytest docutils nxsconfigserver nxswriter nxsrecselector pymysql'
docker exec  ndts /bin/bash -c 'curl -fsSL https://pixi.sh/install.sh | sh ; export PATH=/var/lib/tango/.pixi/bin:$PATH ; cp .github/workflows/pixi/pixi.toml . ; pixi shell-hook  > .sh.sh ; source .sh.sh ; pixi add   numpy pytango  setuptools pip wheel argcomplete lxml pytz pyyaml pytango python-dateutil pninexus fabio h5py matplotlib-base blissdata pytest docutils nxsconfigserver nxswriter pymysql'

# # create nxsconfig database
# docker exec  --user root ndts /bin/bash -c 'source /home/tango/.sh.sh ; export MYSQL_PASSWORD="rootpw" ; create_nxsconfig_db -x -d=nxsonfig -u=tango -p="$CONDA_PREFIX"'

echo "run nxstools tests"
# docker exec  ndts /bin/bash -c 'source .sh.sh ; pixi run  --manifest-path .github/workflows/pixi/pixi.toml arattler-build build  --recipe .github/workflows/pixi/recipe.yaml'
docker exec  ndts /bin/bash -c 'source .sh.sh ;  echo "export MYTANGO_PREFIX=$CONDA_PREFIX/bin" > /home/tango/.env ;   python -m pip install . -vv --no-deps --no-build-isolation ;  python test'

ERROR=$?
if [ $ERROR -ne "0" ]
then
    echo "ERROR "$ERROR
    exit 255
fi
