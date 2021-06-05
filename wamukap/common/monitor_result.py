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
import json


class MonitorResult:
    def __init__(self, start_time, end_time, url, request_success=False,
                 request_error_msg=None, http_status=None, http_status_reason=None,
                 pattern_matched=False):
        self._start_time = start_time
        self._end_time = end_time
        self._url = url
        self._request_success = request_success
        self._request_error_msg = request_error_msg
        self._http_status = http_status
        self._http_status_reason = http_status_reason
        self._pattern_matched = pattern_matched

    @property
    def url(self):
        return self._url

    @property
    def request_success(self):
        return self._request_success

    def to_json(self):
        # string leading underscores from private attributes
        res_dict = {
                key[1:]: value for key, value in
                self.__dict__.items() if value is not None
        }
        return json.dumps(res_dict)
