CoSoCoW
-------
Command line `Sonos`_  Control Wrapper to manage a Network of Zones by Python Console.

As centerpiece the wrapper uses the great `SoCo`_ library to establish a UPnP connection to your speaker.


Installation and Usage
----------------------
Add the tool folder to your python library search path and check that all dependent libraries are available.

Execute in python console:

    >>> from cosocow import CoSoCoW
    >>> mc = CoSoCoW([ip_addr1, ip_addr2])

Licence
-------
CoSoCoW is released under the `MIT`_ license.

.. _Sonos: http://www.sonos.com/system/
.. _SoCo: http://docs.python-soco.com
.. _MIT: https://opensource.org/licenses/MIT
