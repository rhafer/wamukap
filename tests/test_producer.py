import pytest
import asyncio
from aioresponses import aioresponses
from unittest.mock import AsyncMock, patch, ANY

import wamukap.producer
import wamukap.common


@pytest.mark.asyncio
async def test_check_url():
    with aioresponses() as r:
        r.get('http://test', status=200)
        await wamukap.producer._check_url('http://test')


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
@patch('wamukap.common.config.WamConfig')
@patch('wamukap.producer._kafka_worker', new_callable=AsyncMock)
@patch('wamukap.producer._watch_url', new_callable=AsyncMock)
@patch('wamukap.common.kafka.get_producer', new_callable=AsyncMock)
async def test_monitor_url(mock_get_producer,
                           mock_watch_url,
                           mock_kafka_worker,
                           mock_config):
    cfg = wamukap.common.config.WamConfig()
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
