.. image:: https://travis-ci.com/rhafer/wamukap.svg?branch=master
   :target: https://travis-ci.com/github/rhafer/wamukap

Website Availability Monitor using Kafka and PostgreSQL (wamukap)
================================================================

`wamkup` provides an simple framework for monitoring the network availability
of websites and persisting the availability data into a PostgreSQL database.
It consists of two services, which communicate with each other leveraging a
Kafka message queue.

Website-Monitor
---------------

Database Persister
------------------

License
=======

Licensed under the Apache License, Version 2.0. See LICENSE for the full license text.
