# (c) Copyright 2021, Ralf Haferkamp <ralf@h4kamp.de>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from aiokafka import AIOKafkaProducer
from aiokafka.helpers import create_ssl_context

async def get_producer(kafka_cfg):
    logging.debug("Connection to Kafka at {}".format(kafka_cfg['servers']))
    context = create_ssl_context(
        cafile=kafka_cfg['ssl_ca_cert'],
        certfile=kafka_cfg['ssl_cert'],
        keyfile=kafka_cfg['ssl_cert_key']
    )

    producer = AIOKafkaProducer(
            bootstrap_servers=kafka_cfg['servers'],
            security_protocol='SSL',
            ssl_context=context
    )
    await producer.start()
    return producer
