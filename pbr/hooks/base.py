# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import
from __future__ import print_function


class BaseConfig(object):

    section = None

    def __init__(self, config):
        self._global_config = config
        self.config = self._global_config.get(self.section, {})
        self.pbr_config = config.get('pbr', {})

    def run(self):
        self.hook()
        self.save()

    def hook(self):
        pass

    def save(self):
        self._global_config[self.section] = self.config
