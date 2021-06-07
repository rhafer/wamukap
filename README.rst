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

``pip install .``

Configuration File
==================

By default the services read their configuration from the file ``/etc/wamukap.toml``.
It is using the `TOML <https://toml.io/>`_ format. The location of the configuration file
can be overriden using the ``--config-file`` command line argument.

Global Settings
---------------

The ``[kafka]`` section
-----------------------

The ``[datbase]`` section
-------------------------

The ``[watcher]`` section
-------------------------


Usage
=====

``wamukap-consumer`` and ``wamukap-producer`` support the same command line arguments, all
of the are optional:

-h, --help                                    show help message and exit
-c CONFIG_FILE, --config-file CONFIG_FILE     Path to the configuration file (default:/etc/wamukap.toml)
-l LOG_LEVEL, --log-level LOG_LEVEL           Override log-level from config file

License
=======

Licensed under the Apache License, Version 2.0. See LICENSE for the full license text.

Contributing
============
