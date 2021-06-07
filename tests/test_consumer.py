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
from unittest.mock import AsyncMock, MagicMock

import wamukap.consumer
import wamukap.common


# Verify that db insertion is skipped for invalid messages
@pytest.mark.asyncio
async def test_kafka_consumer():
    # construct a couple of return Messages to be fed into the consumer
    class FakeMsg:
        def __init__(self, value):
            self.value = value
    raw_msg = [
            # Valid JSON valid Result
            b'''{"timestamp": "2021-06-07T06:25:37.005922", "request_time": 0.07753138600014609,
                 "url": "http://domain-doesnt-exist-abc.com/", "request_success": false,
                 "request_error_msg": "Error message"}''',
            # Valid JSON invalid Result (missing timestamp)
            b'''{"request_time": 0.10596726500011755,
                 "url": "http://h4kamp.net/", "request_success": true, "http_status": 403,
                 "http_status_reason": "Forbidden"}''',
            # Invalid JSON
            b'''Invalid'''
    ]
    fake_results = [FakeMsg(m) for m in raw_msg]

    # luckily python 3.8 gained support for async iterators and context managers see
    # https://docs.python.org/3/library/unittest.mock-examples.html#mocking-asynchronous-iterators
    mock_consumer = AsyncMock()
    mock_consumer.__aiter__.return_value = fake_results

    mock_db_conn = MagicMock()
    mock_cursor = AsyncMock()
    mock_db_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    await wamukap.consumer._kafka_consumer(mock_consumer, mock_db_conn)
    mock_cursor.execute.assert_called_once()
