Website Availability Monitor using Kafka and PostgreSQL (wamukap)
================================================================

WAMUKAP provides an simple framework for monitoring the network availability
of websites and persisting the availability data into a PostgreSQL database.
It consists of two services, which communicate with each other using the
Kafka event stream platform.

The Website Monitoring Service (``wamukap-producer``) periodically (with a
configurable interval) sends HTTP GET requests to a list of URLs. It records
the returned HTTP status code and message as well as any errors that occur
when the request fails. Additionally it is possible to define a pattern that
the return HTTP body is matched against. The result of the match is recorded
as well. ``wamukap-producer`` will feed the results into a Kafka event queue.
From where they can be consumed by the Database Persister Service
(``wamukap-consumer``).

The Database Persister Service (``wamukap-consumer``) subscribes to a configurable
topic on a Kafka Cluster and consumes any incoming event on that topic. If 
the event is a message produced by the ``wamukap-producer`` the consumer will persist
that event into a PostgreSQL database.

Installation
============


RPMs
----

RPM packages are currently available for openSUSE Tumbleweed via OBS to install use::

        zypper ar http://download.opensuse.org/repositories/home:/rhafer:/aiven/openSUSE_Tumbleweed/home:rhafer:aiven.repo
        zypper in wamukap

The RPMs ship with a default configuration installed into ``/etc/wamukap/wamukap.toml``. They
also provide ``systemd`` service unit for ``wamukap-producer`` and ``wamukap-consumer``. So
you can use ``systemctl`` to manage the service after adapting the configuration for you needs.


Using pip
---------

``pip install https://github.com/rhafer/wamukap/releases/download/v0.0.2/wamukap-0.0.2-py3-none-any.whl``

or

``pip install https://github.com/rhafer/wamukap/releases/download/v0.0.2/wamukap-0.0.2.tar.gz``

Create a configuration file ``/etc/wamukap/wamukap.toml``. For and example see
`configuration file <https://github.com/rhafer/wamukap/raw/master/wamukap.toml>`_. Do run the
service you can either call ``wamukap-producer`` and ``wamukap-consumer`` manually or
install the ``systemd`` service units provided
`here <https://github.com/rhafer/wamukap/tree/master/contrib>`_.


Configuration File
==================

By default the services read their configuration from the file ``/etc/wamukap.toml``.
It is using the `TOML <https://toml.io/>`_ format. The location of the configuration file
can be overriden using the ``--config-file`` command line argument. An example configuration
file can be found here: `https://github.com/rhafer/wamukap/blob/master/wamukap.toml`_

Global Settings
---------------

``log-level``

The ``[kafka]`` section
-----------------------

The ``[kafka]`` is used by both wamukap service. It defines the connection details for accessing
the Kafka cluster. Please note that currently the only support authentication mechanism is using
SSL client certificates. Support for other authentication mechansims might be added in a future
release.

``servers``
        A list of ``host:port`` strings that defines the initial Kafka servers to contact.

``ssl_ca_cert``
       The path to a CA Certificate in PEM format that is used for verifying the Kafka
       cluster's SSL certificates.

``ssl_cert``
       Path to the SSL certificate that is used for authenticating to the Kafka cluster

``ssl_cert_key``
       Path to the private key associated with the ``ssl_cert`` certificate

``topic``
       The topic on which ``wamukap-producer`` should send events and where ``wamukap-consumer``
       should listen to event.

``consumer_group_id``
       This setting is specific to ``wamukap-consumer`` and does not need to be present on
       nodes that only run ``wamukap-producer``. It defines the consumer group that ``wamukap-consumer``
       joins. It's needed e.g. for Kafka's autocommit feature.

The ``[datbase]`` section
-------------------------

The ``[database]`` section is only used by ``wamukap-conumer`` it defines the connection pararmeters
for the PostgreSQL database. Basically in can include any keyword that is an accepted connection
parameter for ``libpq`` as docuemented `here <https://www.postgresql.org/docs/13/libpq-connect.html#LIBPQ-PARAMKEYWORDS>`_.

For example::

        host = "hostname"
        port = 18935
        database = "wamukap"
        user = "dbuser"
        password = "secret"
        sslmode = "require"
        sslrootcert = "/etc/wamukap/ca-cert.pem"

The ``[watcher]`` section
-------------------------

The ``[watcher]`` is specifc to ``wamukap-producer`` and defines the details about the URLs that
should be monitored. It mainly consists of the top level ``interval`` setting and a list of
``[[watcher.sites]]`` subsections.

``interval``
        Defines the default interval in secondes which to check each URL. Unless the settings for the URL
        define an own interval.

``[[watcher.sites]]``
        One ``[[watcher.sites]]`` elements need to be defined per URL to watch. These settings
        are allowed:

        ``url``
                The URL to query

        ``interval``
                Optional. Use this to override the top-level ``interval`` setting.

        ``regexp``
                Optional. A regular expression to match against the body that is return when querying
                the URL.

Usage
=====

``wamukap-consumer`` and ``wamukap-producer`` support the same command line arguments, all
of the are optional:

-h, --help                                    show help message and exit
-c CONFIG_FILE, --config-file CONFIG_FILE     Path to the configuration file (default:/etc/wamukap/wamukap.toml)
-l LOG_LEVEL, --log-level LOG_LEVEL           Override log-level from config file

License
=======

Licensed under the Apache License, Version 2.0. See LICENSE for the full license text.

Contributing
============

Reporting an issue
------------------

Please create `Github issues <https://github.com/rhafer/wamukap/issues/new/choose>`_
for any enhancement request or bug.

Fixing issues and new feature
-----------------------------

We are to bugfixes and other contribution, feel free to submit any enhanced
as a `Github Pull Request <https://github.com/rhafer/wamukap/pulls>`_.
