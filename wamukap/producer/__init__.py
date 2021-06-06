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

import aiohttp
import asyncio
import logging
import re
import signal
import sys
from datetime import datetime
from kafka import errors as kafka_errors
from time import perf_counter

from wamukap.common import kafka_util
from wamukap.common import utils
from wamukap.common.monitor_result import MonitorResult

logger = logging.getLogger(__name__)

DESCRIPTION = """
    The Website Availability Monitor producer (wamukap-producer) implements a
    service that checks a set of websited defined in a configuration file for
    their availability and submits the results of those checks to a Kafka
    message queue to be consumed by wamukap-comsumer."""


def _match_content(regex, content):
    return re.search(regex, content) is not None


async def _check_url(url, regexp=None):
    async with aiohttp.ClientSession() as session:
        matched = None
        timestamp = datetime.utcnow().isoformat()
        perf_start = perf_counter()
        try:
            async with session.get(url) as response:
                logger.debug('Got HTTP result for {}: Status={} "{}"'.format(
                    url,
                    response.status,
                    response.reason)
                )
                if response.ok and regexp:
                    content = await response.text()
                    matched = _match_content(regexp, content)
        except Exception as e:
            # The HTTP request failed. There is no status code
            # and no text body to check
            logger.warning('Request failed for {} {} {}'.format(
                url,
                type(e).__name__,
                str(e))
            )
            return MonitorResult(timestamp=timestamp,
                                 request_time=perf_counter()-perf_start,
                                 url=url,
                                 request_success=False,
                                 request_error_msg=str(e))
        else:
            return MonitorResult(timestamp=timestamp,
                                 request_time=perf_counter()-perf_start,
                                 url=url,
                                 request_success=True,
                                 http_status=response.status,
                                 http_status_reason=response.reason,
                                 pattern_matched=matched,
                                 pattern=regexp)


async def _watch_url(queue, url, interval, regexp=None):
    # Query the <url> every <interval> seconds in an endless
    # loop, submit the result of the check (a MonitorResult object)
    # to the asyncio.Queue
    while True:
        res = await _check_url(url, regexp)
        await queue.put(res)
        await asyncio.sleep(interval)


async def _kafka_worker(producer, topic, queue):
    # read MonitorResults from the asyncio.Queue, convert them to json
    # and submit them to Kafka under the specified topic.
    try:
        while True:
            item = await queue.get()
            logger.debug('Submit result for {} to Kafka'.format(item.url))
            await producer.send_and_wait(topic, item.to_json().encode())
            queue.task_done()
    except kafka_errors.KafkaError as e:
        logger.error('Error sending message to Kafka {}'.format(e))
        # FIXME could we handle this more gracefully than just shutting down?
        _shutdown(asyncio.get_event_loop())
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()


# https://stackoverflow.com/questions/34710835/proper-way-to-shutdown-asyncio-tasks
def _shutdown(loop):
    logger.info('Shutting down')
    for task in asyncio.Task.all_tasks():
        task.cancel()


async def _monitor_urls(cfg):
    # for every configured url setup a async task that periodically
    # checks the url. The results are submitted to an async queue
    # from where they are consumed by another task to be submitted
    # to kafka.
    tasks = []
    queue = asyncio.Queue()

    # try to shutdown gracefully on SIGTERM
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, _shutdown, loop)

    kafka_producer = await kafka_util.get_producer(cfg.kafka, logger)
    if kafka_producer is None:
        return None

    kafka_producer_task = asyncio.create_task(
        _kafka_worker(producer=kafka_producer,
                      topic=cfg.kafka['topic'],
                      queue=queue)
    )
    tasks.append(kafka_producer_task)

    for site in cfg.watcher['sites']:
        interval = site.get('interval', cfg.watcher['interval'])
        regexp = site.get('regexp', None)
        logger.debug('Monitoring {}'.format(site))
        tasks.append(
                asyncio.create_task(
                    _watch_url(queue, site['url'], interval, regexp)
                    )
                )
    try:
        await asyncio.gather(*tasks)
    except asyncio.exceptions.CancelledError:
        logger.debug("Tasks canceled")


def producer():
    # This is the main entry point of wamukap-producer

    args = utils.parse_args(DESCRIPTION)
    logging.basicConfig(format=utils.LOG_FORMAT, datefmt=utils.LOG_DATE)

    if args is None:
        sys.exit()

    cfg = utils.WamConfig()
    try:
        cfg.read_config(args.config_file)
        cfg.validate_producer_config()
        logger.setLevel(cfg.cfg['log-level'])
    except utils.ConfigurationError as e:
        logger.error('Error reading config file: {}'.format(e))
        sys.exit()

    if args.log_level:
        logger.setLevel(args.log_level)

    asyncio.run(_monitor_urls(cfg))
