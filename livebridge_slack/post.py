# -*- coding: utf-8 -*-
#
# Copyright 2016 dpa-infocom GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from datetime import datetime
from livebridge.base import BasePost

logger = logging.getLogger(__name__)

class SlackPost(BasePost):

    source = "slack"

    @property
    def id(self):
        return self.data.get("deleted_ts", self.data.get("message", self.data).get("ts"))

    @property
    def source_id(self):
       return self.data.get("channel")

    @property
    def created(self):
       return datetime.utcfromtimestamp(float(self.data.get("message", self.data).get("ts")))

    @property
    def updated(self):
       return datetime.utcfromtimestamp(float(self.data.get("ts", None)))

    @property
    def is_update(self):
        return (self.data.get("livebridge", {}).get("action") == "update")

    @property
    def is_deleted(self):
        return (self.data.get("livebridge", {}).get("action") == "delete")

    @property
    def is_sticky(self):
       return False

    def get_action(self):
        return self.data.get("livebridge", {}).get("action", None)
