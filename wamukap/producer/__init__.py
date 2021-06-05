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
from time import perf_counter

from wamukap.common import config
from wamukap.common import kafka
from wamukap.common.monitor_result import MonitorResult


def _match_content(regex, content):
    return re.search(regex, content) is not None


async def _check_url(url, regexp=None):
    async with aiohttp.ClientSession() as session:
        matched = False
        start = perf_counter()
        try:
            async with session.get(url) as response:
                logging.debug('Status: {} {}'.format(
                    response.status,
                    response.reason)
                )
                if response.ok and regexp:
                    content = await response.text()
                    matched = _match_content(regexp, content)
                    logging.debug('match: {}'.format(matched))
        except aiohttp.ClientConnectionError as e:
            logging.warn('{} {}'.format(type(e).__name__, str(e)))
            return MonitorResult(start_time=start,
                                 end_time=perf_counter(),
                                 url=url,
                                 request_success=False,
                                 request_error_msg=str(e))
        else:
            return MonitorResult(start_time=start,
                                 end_time=perf_counter(),
                                 url=url,
                                 request_success=True,
                                 http_status=response.status,
                                 http_status_reason=response.reason,
                                 pattern_matched=matched)


async def _watch_url(queue, url, interval, regexp=None):
    while True:
        res = await _check_url(url, regexp)
        await queue.put(res)
        logging.debug('{} {} queue len {}'.format(res.url, res.request_success, queue.qsize()))
        await asyncio.sleep(interval)


async def _kafka_worker(producer, queue):
    try:
        while True:
            item = await queue.get()
            logging.debug('kafka {} {} queue len {}'.format(item.url, item.request_success, queue.qsize()))
            # Produce message
            await producer.send_and_wait("wamukap", item.to_json().encode())
            queue.task_done()
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()


async def _monitor_urls(cfg):
    tasks = []
    queue = asyncio.Queue()

    kafka_producer = await kafka.get_producer(cfg.kafka)
    kafka_producer_task = asyncio.create_task(
        _kafka_worker(kafka_producer, queue)
    )
    tasks.append(kafka_producer_task)

    for site in cfg.watcher['sites']:
        interval = site.get('interval', cfg.watcher['interval'])
        regexp = site.get('regexp', None)
        logging.debug('Monitoring {}'.format(site))
        tasks.append(
                asyncio.create_task(
                    _watch_url(queue, site['url'], interval, regexp)
                    )
                )
    await asyncio.gather(*tasks)


def producer():
    cfg = config.WamConfig()
    cfg.read_config('wamukap.toml')
    logging.basicConfig(level=logging.DEBUG)

    asyncio.run(_monitor_urls(cfg))
