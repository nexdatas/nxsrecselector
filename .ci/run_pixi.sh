#!/usr/bin/env bash

echo "install pixi"
docker exec  ndts /bin/bash -c 'curl -fsSL https://pixi.sh/install.sh | sh ; export PATH=/var/lib/tango/.pixi/bin:$PATH ; cp .github/workflows/pixi/pixi.toml . ; pixi shell-hook  > .sh.sh ; source .sh.sh ; pixi add   numpy "pytango=10.3.1" setuptools pip wheel argcomplete lxml pytz pyyaml  python-dateutil pninexus fabio h5py matplotlib-base blissdata pytest docutils nxsconfigserver nxswriter pymysql nxstools pymysql sardana'

echo "run nxsrecselector tests"
docker exec  ndts /bin/bash -c 'source .sh.sh ;  echo "export MYTANGO_PREFIX=$CONDA_PREFIX/bin" > /home/tango/.env ;   python -m pip install . -vv --no-deps --no-build-isolation'
# cmd="source .sh.sh ;  python -m unittest test.ExtraNXSRecSelector_test.ExtraNXSRecSelectorTest.test_create_init_typeshape_tango_nods_attr"
cmd="source .sh.sh ;  python -m unittest test.ExtraNXSRecSelector_test.ExtraNXSRecSelectorTest.test_create_step_typeshape_tango_nods_attr"
echo $cmd
docker exec  ndts /bin/bash -c "$cmd"

ERROR=$?
if [ $ERROR -ne "0" ]
then
    echo "ERROR "$ERROR
    exit 255
fi
