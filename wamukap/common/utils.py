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

import argparse
import logging
import toml

logger = logging.getLogger(__name__)

LOG_LEVELS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
LOG_FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
LOG_DATE = '%m-%d %H:%M'


def parse_args(DESCRIPTION):

    parser = argparse.ArgumentParser(
            description=DESCRIPTION
    )
    parser.add_argument('-c', '--config-file', default='/etc/wamukap.toml',
                        help='Path to the configuration file (default:%(default)s)')
    parser.add_argument('-l', '--log-level', default=None,
                        help='Override log-level from config file')

    args = parser.parse_args()
    if args.log_level is not None and args.log_level not in LOG_LEVELS:
        logger.error(
                'Invalid log-level "{}" use one of {}'.format(
                    args.log_level,
                    ', '.join(LOG_LEVELS)
                )
        )
        return None

    return args


class ConfigurationError(Exception):
    pass


class WamConfig(object):
    def __init__(self):
        self._cfg = None

    def validate_kafka_config(self, consumer=False):
        if 'kafka' not in self.cfg:
            raise ConfigurationError('"kafka" section is missing in config file')

        required_keys = ['servers', 'ssl_ca_cert', 'ssl_cert', 'ssl_cert_key', 'topic']
        # the consumer also requires a group_id setting for the auto-commit
        if consumer:
            required_keys.append('consumer_group_id')
        for i in required_keys:
            if i not in self.cfg['kafka'] or not self.cfg['kafka'][i]:
                raise ConfigurationError(
                    '"kafka" section is missing "{}" setting'.format(i))

    def validate_pg_config(self):
        if 'database' not in self.cfg:
            raise ConfigurationError('"database" section is missing in config file')
        # FIXME we might wanna add some more validation in here. But the
        # config is passed directly into the aiopg module which does its
        # own validation via libpg

    def validate_watcher_urls(self):
        if 'sites' not in self._cfg['watcher']:
            raise ConfigurationError('"watcher.sites" section is missing.')

        for site in self.cfg['watcher']['sites']:
            if 'url' not in site:
                raise ConfigurationError('"watcher.sites" elements need to define a url.')
        # FIXME add more checks here

    def validate_producer_config(self):
        self.validate_kafka_config()
        self.validate_watcher_urls()

    def validate_consumer_config(self):
        self.validate_pg_config()
        self.validate_kafka_config(consumer='True')

    def read_config(self, cfg_file):
        self._cfg = toml.load(cfg_file)
        self._cfg['log-level'] = self._cfg.get('log-level', 'WARNING')

        if self._cfg['log-level'] not in LOG_LEVELS:
            raise ConfigurationError('Invalid log-level. Use one of {}'.format(
                ', '.join(LOG_LEVELS)))

    @property
    def cfg(self):
        return self._cfg

    @property
    def database(self):
        return self._cfg['database']

    @property
    def kafka(self):
        return self._cfg['kafka']

    @property
    def watcher(self):
        return self._cfg['watcher']
