========================================
Welcome to nxsrecconfig's documentation!
========================================

|github workflow|
|docs|
|Pypi Version|
|Python Versions|

.. |github workflow| image:: https://github.com/nexdatas/nxsrecselector/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/nexdatas/nxsrecselector/actions
   :alt:

.. |docs| image:: https://img.shields.io/badge/Documentation-webpages-ADD8E6.svg
   :target: https://nexdatas.github.io/nxsrecselector/index.html
   :alt:

.. |Pypi Version| image:: https://img.shields.io/pypi/v/nxsrecselector.svg
                  :target: https://pypi.python.org/pypi/nxsrecselector
                  :alt:

.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/nxsrecselector.svg
                     :target: https://pypi.python.org/pypi/nxsrecselector/
                     :alt:

Authors: Jan Kotanski
Introduction

Tango server with Sardana Recorder settings

Tango Server API: https://nexdatas.github.io/nxsrecselector/doc_html

| Source code: https://github.com/nexdatas/nxsrecselector
| Web page: https://nexdatas.github.io/nxsrecselector
| NexDaTaS Web page: https://nexdatas.github.io

------------
Installation
------------

Install the dependencies:

|    sardana, tango, sphinx

From sources
^^^^^^^^^^^^

Download the latest version of NeXuS Configuration Server from

|    https://github.com/nexdatas/nxsrecselector

Extract the sources and run

.. code-block:: console

	  $ python setup.py install

Debian packages
^^^^^^^^^^^^^^^

Debian bookworm, bullseye and buster or ubuntu lunar, jammy nad focal packages can be found in the HDRI repository.

To install the debian packages, add the PGP repository key

.. code-block:: console

	  $ sudo su
	  $ wget -q -O - http://repos.pni-hdri.de/debian_repo.pub.gpg | apt-key add -

and then download the corresponding source list

.. code-block:: console

	  $ cd /etc/apt/sources.list.d
	  $ wget http://repos.pni-hdri.de/bookworm-pni-hdri.list

Finally, install module

.. code-block:: console

	  $ apt-get update
	  $ apt-get install python-nxsrecselector

and the NXSRecSelector tango server

.. code-block:: console

	  $ apt-get update
	  $ apt-get install nxsrecselector

To instal other NexDaTaS packages

.. code-block:: console

	  $ apt-get install python-nxswriter nxsconfigtool nxstools python-nxsconfigserver nxsconfigserver-db

and

.. code-block:: console

	  $ apt-get install nxselector python-sardana-nxsrecorder

for Component Selector and Sardana related packages.

From pip
^^^^^^^^

To install it from pip you can

.. code-block:: console

   $ python3 -m venv myvenv
   $ . myvenv/bin/activate

   $ pip install nxsrecselector

Moreover it is also good to install

.. code-block:: console

   $ pip install pytango
   $ pip install taurus
   $ pip install sardana
   $ pip install nxswriter
   $ pip install nxsconfigserver
   $ pip install nxstools
   $ pip install pymysqldb

-------------------
Setting environment
-------------------


Setting Saradna
^^^^^^^^^^^^^^^
If sardana is not yet set up run


.. code-block:: console

	  $ Pool

- enter a new instance name
- create the new instance

Then wait a while until Pool is started and in a new terminal run

.. code-block:: console

	  $ MacroServer

- enter a new instance name
- create the new instance
- connect pool

Next, run Astor and change start-up levels: for Pool to 2,
for MacroServer to 3 and restart servers.

Alternatively, terminate Pool and MacroServer in the terminals and run

.. code-block:: console

          $ nxsetup -s Pool -l2

wait until Pool is started and run

.. code-block:: console

          $ nxsetup -s MacroServer -l3


Additionally, one can create dummy devices by running `sar_demo` in

.. code-block:: console

	  $ spock



Setting NeXus Servers
^^^^^^^^^^^^^^^^^^^^^

To set up  NeXus Servers run

.. code-block:: console

	  $ nxsetup -x

or

.. code-block:: console

          $ nxsetup -x NXSDataWriter
          $ nxsetup -x NXSConfigServer
	  $ nxsetup -x NXSRecSelector

for specific servers.

If the `RecoderPath` property of MacroServer is not set one can do it by

.. code-block:: console

	  $ nxsetup -a /usr/lib/python2.7/dist-packages/sardananxsrecorder

where the path should point the `sardananxsrecorder` package.
