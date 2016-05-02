========================================
Welcome to nxsrecconfig's documentation!
========================================

Authors: Jan Kotanski
Introduction

Tango server with Sardana Recorder settings

| Source code: https://github.com/nexdatas/recselector
| Web page: http://www.desy.de/~jkotan/nxsrecselector


------------
Installation
------------

Install the dependencies:

    Sardana, PyTango, sphinx

From sources
^^^^^^^^^^^^

Download the latest version of NeXuS Configuration Server from

    https://github.com/jkotan/nexdatas/recselector/

Extract the sources and run

.. code:: bash

	  $ python setup.py install

Debian packages
^^^^^^^^^^^^^^^

Debian Jessie (and Wheezy) packages can be found in the HDRI repository.

To install the debian packages, add the PGP repository key

.. code:: bash

	  $ sudo su
	  $ wget -q -O - http://repos.pni-hdri.de/debian_repo.pub.gpg | apt-key add -

and then download the corresponding source list

.. code:: bash

	  $ cd /etc/apt/sources.list.d
	  $ wget http://repos.pni-hdri.de/jessie-pni-hdri.list

Finally,

.. code:: bash

	  $ apt-get update
	  $ apt-get install python-nxsrecselector

To instal other NexDaTaS packages

.. code:: bash

	  $ apt-get install python-nxswriter nxsconfigtool nxstools python-nxsconfigserver nxsconfigserver-db

and

.. code:: bash

	  $ apt-get install nxselector python-sardana-nxsrecorder

for Component Selector and Sardana related packages.
