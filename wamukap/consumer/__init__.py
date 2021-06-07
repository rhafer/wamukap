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

import aiopg
import asyncio
import logging
import signal
import sys
from wamukap.common import kafka_util
from wamukap.common import utils
from wamukap.common.monitor_result import MonitorResult

logger = logging.getLogger(__name__)

DESCRIPTION = """
    The Website Availability Monitor consumer (wamukap-consumer) implements a
    service that consumes messages send by the wamukap-producer from a Kafka
    message queue and persists them in to a PostgreSQL database.
"""

sql_insert_cmd = """
    INSERT INTO wamukap (timestamp, url,
                         request_success, error_msg,
                         request_time, http_code,
                         http_msg, pattern_matched,
                         pattern)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

sql_table = """
    CREATE TABLE IF NOT EXISTS wamukap (
        timestamp TIMESTAMP NOT NULL,
        url VARCHAR(1024) NOT NULL,
        request_success BOOLEAN NOT NULL,
        error_msg VARCHAR(1024),
        request_time interval NOT NULL,
        http_code SMALLINT,
        http_msg VARCHAR(1024),
        pattern_matched BOOLEAN,
        pattern VARCHAR(128))
"""


async def _kafka_consumer(consumer, db_conn):
    async with db_conn.cursor() as cur:
        async for msg in consumer:
            try:
                json_res = msg.value.decode('utf-8')
                logger.debug('Received message {}'.format(json_res))
                res = MonitorResult.from_json(json_res)
            except Exception as e:
                logger.warning('Unable to decode result from message {}. Ignoring'.format(e))
            else:
                # FIXME: improve error handling here
                await cur.execute(sql_insert_cmd, (res.timestamp,
                                                   res.url,
                                                   res.request_success,
                                                   res.request_error_msg,
                                                   res.request_time,
                                                   res.http_status,
                                                   res.http_status_reason,
                                                   res.pattern_matched,
                                                   res.pattern))


async def _persist_monitor_results(cfg):
    tasks = []

    # try to shutdown gracefully on SIGTERM
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, _shutdown, loop)

    conn = await _init_db_connection(cfg.database)

    try:
        kafka_consumer = await kafka_util.get_consumer(cfg.kafka, logger)
        kafka_consumer_task = asyncio.create_task(
            _kafka_consumer(consumer=kafka_consumer, db_conn=conn)
        )
        tasks.append(kafka_consumer_task)
        await asyncio.gather(*tasks)
    finally:
        conn.close()


def _shutdown(loop):
    logger.info('Shutting down')
    for task in asyncio.Task.all_tasks():
        task.cancel()


async def _init_db_connection(dbcfg):
    logger.debug('Connecting to database {} at {}'.format(
        dbcfg['database'], dbcfg['host'])
    )
    conn = await aiopg.connect(**dbcfg)

    # Create the required table if it does not exist yet
    async with conn.cursor() as cur:
        await cur.execute(sql_table)
    return conn


def consumer():
    # This is the main entry point of wamukap-consumer
    args = utils.parse_args(DESCRIPTION)
    logging.basicConfig(format=utils.LOG_FORMAT, datefmt=utils.LOG_DATE)

    if args is None:
        sys.exit()

    cfg = utils.WamConfig()
    try:
        cfg.read_config(args.config_file)
        cfg.validate_consumer_config()
        logger.setLevel(cfg.cfg['log-level'])
    except utils.ConfigurationError as e:
        logger.error('Error reading config file: {}'.format(e))
        sys.exit()

    if args.log_level:
        logger.setLevel(args.log_level)

    asyncio.run(_persist_monitor_results(cfg))
