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

import pytest
import asyncio
from aioresponses import aioresponses
from unittest.mock import AsyncMock, patch, ANY

import wamukap.producer
import wamukap.common
from wamukap.common.monitor_result import MonitorResult


@pytest.mark.asyncio
async def test_check_url():
    testdata = {
        'http://test.com': {
            'pattern': None,
            'response': {
                'status': 200
            },
            'expected': {
                'success': True,
                'pattern_matched': None
            }
         },
        'http://without-pattern-match/': {
            'pattern': 'with\\s.+\\smatch',
            'response': {
                'status': 200,
                'body': 'Test body without pattern match'
            },
            'expected': {
                'success': True,
                'pattern_matched': False
            }
        },
        'http://with-pattern-match/': {
            'pattern': 'with\\s.+\\smatch',
            'response': {
                'status': 200,
                'body': 'Test body with pattern match'
            },
            'expected': {
                'success': True,
                'pattern_matched': True
            }
        },
        'http://fail': {
            'pattern': None,
            'response': {
                'status': 404
            },
            'expected': {
                'success': True,
                'pattern_matched': None
            }
        },
        'http://exception': {
            'pattern': None,
            'response': {
                'exception': Exception('error')
            },
            'expected': {
                'success': False,
                'error': 'error'
            }
        }
    }
    with aioresponses() as resp:
        for url, testset in testdata.items():
            resp.get(url, **testset['response'])
            res = await wamukap.producer._check_url(url, testset['pattern'])
            assert res.request_success == testset['expected']['success']
            if testset['expected']['success']:
                assert res.http_status == testset['response']['status']
                assert res.pattern_matched == testset['expected']['pattern_matched']
            else:
                assert res.http_status is None
                assert res.request_error_msg == testset['expected']['error']


@pytest.mark.asyncio
@patch('asyncio.sleep', new_callable=AsyncMock)
@patch('wamukap.producer._check_url', new_callable=AsyncMock)
async def test_watch_url(mock_check_url, mock_sleep):
    mock_sleep.side_effect = ErrorAfter(0)
    queue = asyncio.Queue()
    with pytest.raises(CallableExhausted):
        await wamukap.producer._watch_url(queue, 'http://test', 5)

    # A single loop iteration should have queued exactly one
    # result
    assert queue.qsize() == 1
    mock_check_url.assert_called_once_with('http://test', None)
    mock_sleep.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_kafka_worker():
    mock_producer = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()
    # Make send_and_wait fail after the first loop iteration
    # to escape loop
    mock_producer.send_and_wait.side_effect = ErrorAfter(0)
    queue = asyncio.Queue()
    fake_result = MonitorResult("", 0, 'http://test', False)
    await queue.put(fake_result)
    with pytest.raises(CallableExhausted):
        await wamukap.producer._kafka_worker(mock_producer, 'topic', queue)
    mock_producer.send_and_wait.assert_called_once_with('topic', ANY)


@pytest.mark.asyncio
@patch('wamukap.common.utils.WamConfig')
@patch('wamukap.producer._kafka_worker', new_callable=AsyncMock)
@patch('wamukap.producer._watch_url', new_callable=AsyncMock)
@patch('wamukap.common.kafka_util.get_producer', new_callable=AsyncMock)
async def test_monitor_url(mock_get_producer,
                           mock_watch_url,
                           mock_kafka_worker,
                           mock_config):
    cfg = wamukap.common.utils.WamConfig()
    config_dict = {
        'kafka': {
            'topic': 'topic'
        },
        'watcher': {
            'interval': 3,
            'sites': [{
                'url': 'test',
                'interval': 5
                }]
        }
    }

    cfg.kafka = config_dict['kafka']
    cfg.watcher = config_dict['watcher']

    await wamukap.producer._monitor_urls(cfg)
    mock_watch_url.assert_called_once_with(ANY, 'test', 5, None)


# Helper class to be able to get of endless loops
# see http://igorsobreira.com/2013/03/17/testing-infinite-loops.html
class ErrorAfter():
    '''
    Callable that will raise `CallableExhausted`
    exception after `limit` calls

    '''
    def __init__(self, limit):
        self.limit = limit
        self.calls = 0

    def __call__(self, *args):
        self.calls += 1
        if self.calls > self.limit:
            raise CallableExhausted


class CallableExhausted(Exception):
    pass
