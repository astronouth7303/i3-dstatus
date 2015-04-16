k5dstatus
==========

The ultimate DIY statusline generator for `i3wm <http://i3wm.org>`__.

About
-----

*k5dstatus is in the early phases of development and will need some
adjustments to get right. If you use k5dstatus, send me feedback!*

k5dstatus is a statusline generator for i3 that you can use to display
system information you may be interested in. i3 comes with ``i3status``
which has many limitations. It has no plugin interface. It has no
support for events and relies on polling for all its information, which
makes it surprisingly heavy on resources. It has a weird config file
format that makes it difficult to configure.

Other projects have come along to make up for these weaknesses and many
of them do a great job. k5dstatus is for users who want a more flexible
statusline that can be achieved from editing options in a configuration
file but without having to learn a complicated plugin api to create
custom statusline entries.

This is accomplished by allowing users to update the statusline through
interprocess communication using
`DBUS <http://www.freedesktop.org/wiki/Software/dbus/>`__. k5dstatus
exposes a DBUS service that you can use to update the statusline simply
in pretty much any programming language and from any process (maybe even
in a cron!).

-  No configuration file is required
-  Update the statusline from multiple processes
-  Update the statusline from any language (even from the command line!)
-  No complicated plugin api to learn


Relation to i3-dstatus
----------------------

This project is a source fork and rewrite of i3-dstatus. It does not attempt to
maintain compatibility or upstream pairing.

Installing
----------

k5dstatus is on `PyPI <https://pypi.python.org/pypi/k5dstatus>`__.

::

    pip install k5dstatus

You'll also need ``python-gobject`` and ``python-dbus`` from your package
manager.

Usage
-----

Use k5dstatus as your status command in your bar block like so:

::
    
    bar {
        status_command k5-dstatus clock
    }

Configuration
~~~~~~~~~~~~~

Generator scripts will look for ``~/.k5dstatus.conf`` for configuration
options. See ``k5dstatus.conf`` in the repo for an example. The
configuration file should be a single YAML object. (More documentation
to come).

Contributing
------------

Please report bugs, request feature, write documentation, and add
generators to the ``k5dstatus/generators`` directory. k5dstatus is a community
project so feedback is welcome!

License
-------

This work is available under a FreeBSD License (see LICENSE).

Copyright © 2015, James Bliss

All rights reserved.
